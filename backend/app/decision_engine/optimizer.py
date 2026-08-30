import uuid
from datetime import datetime
from typing import List, Dict, Tuple, Any
from app.schemas.pydantic_schemas import (
    PreDecisionFeatures,
    DecisionContract,
    CandidateActionScore,
    Explanation,
    GuardrailResult,
    BlockedAction
)
from app.ml.models import RecoveryPredictorModel
from app.guardrails.engine import DeterministicConstraintEngine
from app.decision_engine.evaluator import evaluate_action_expected_net_value
from app.ml.generator import ACTIONS
from app.core.config import settings

class DecisionOptimizerEngine:
    def __init__(self, ml_model: RecoveryPredictorModel):
        self.ml_model = ml_model
        self.constraint_engine = DeterministicConstraintEngine()

    def optimize_and_decide(
        self,
        features: PreDecisionFeatures,
        llm_explanation_provider=None
    ) -> DecisionContract:
        """
        Executes the canonical Decision Workflow:
        PreDecisionFeatures -> ML Predictions -> Deterministic Constraints -> Feasible Action Set -> ENV Optimization -> Risk Policy -> Canonical DecisionContract
        """
        # Step 1: Deterministic Constraint Check (Constraints 1-5)
        feasible_actions, blocked_actions, guardrail_results, hard_block = self.constraint_engine.evaluate_constraints(
            features, ACTIONS
        )

        # Step 2: Score P(recovery) & ENV for all candidate actions
        candidate_scores: List[CandidateActionScore] = []
        for action in ACTIONS:
            if action in [b.action for b in blocked_actions]:
                # Action is blocked
                block_res = next((b for b in blocked_actions if b.action == action), None)
                score = evaluate_action_expected_net_value(
                    action, features.amount, 0.0, features.contacts_24h, features.contacts_7d
                )
                score.is_blocked = True
                score.block_reason = block_res.reason if block_res else "Blocked by policy"
                candidate_scores.append(score)
            else:
                p_rec = self.ml_model.predict_action_probability(features.model_dump(), action)
                score = evaluate_action_expected_net_value(
                    action, features.amount, p_rec, features.contacts_24h, features.contacts_7d
                )
                candidate_scores.append(score)

        # Filter feasible candidate scores
        feasible_scores = [s for s in candidate_scores if not s.is_blocked]

        # Step 3: Rank feasible actions by Expected Net Value (ENV)
        feasible_scores.sort(key=lambda s: s.expected_net_value, reverse=True)
        top_action_score = feasible_scores[0] if feasible_scores else None

        # Step 4: Determine Decision State & Selected Action
        if hard_block or not top_action_score or top_action_score.action == "Stop Intervention" or top_action_score.expected_net_value <= 0:
            decision_status = "BLOCK"
            selected_action = "Stop Intervention"
            approval_required = False
            execution_status = "NOT_EXECUTED"
            winning_score = next((s for s in candidate_scores if s.action == "Stop Intervention"), top_action_score or candidate_scores[0])
        else:
            is_high_val = features.amount >= settings.HIGH_VALUE_THRESHOLD
            is_low_conf = top_action_score.predicted_p_recovery < settings.LOW_CONFIDENCE_THRESHOLD
            is_human_esc = top_action_score.action == "Human Escalation"

            if is_high_val or is_low_conf or is_human_esc:
                decision_status = "RECOMMEND_FOR_APPROVAL"
                selected_action = top_action_score.action
                approval_required = True
                execution_status = "PENDING_SIMULATION"
                winning_score = top_action_score

                if is_high_val:
                    g_name = "High-Value Transaction Policy"
                    g_reason = f"Transaction amount ₹{features.amount:,.2f} exceeds ₹{settings.HIGH_VALUE_THRESHOLD:,.2f} threshold; requires operator review."
                elif is_human_esc:
                    g_name = "Human Escalation Policy"
                    g_reason = f"Selected action '{top_action_score.action}' requires human specialist intervention."
                else:
                    g_name = "Low-Confidence Recovery Policy"
                    g_reason = f"Calibrated recovery probability ({(top_action_score.predicted_p_recovery * 100):.1f}%) is below auto-execution threshold ({settings.LOW_CONFIDENCE_THRESHOLD * 100:.0f}%); requires operator review."

                guardrail_results.append(GuardrailResult(
                    guardrail=g_name,
                    status="ESCALATE",
                    reason=g_reason,
                    metadata={"amount": features.amount, "action": top_action_score.action, "p_recovery": top_action_score.predicted_p_recovery}
                ))
            else:
                decision_status = "AUTO_EXECUTE"
                selected_action = top_action_score.action
                approval_required = False
                execution_status = "PENDING_SIMULATION"
                winning_score = top_action_score

        # Step 5: Build "Why Selected" & "Why Not Selected" Explanations
        why_not = {}
        for s in candidate_scores:
            if s.action != selected_action:
                if s.is_blocked:
                    why_not[s.action] = f"Blocked by guardrail: {s.block_reason}"
                elif s.expected_net_value < winning_score.expected_net_value:
                    why_not[s.action] = f"Lower expected net value (₹{s.expected_net_value:,.2f} vs ₹{winning_score.expected_net_value:,.2f})."
                elif s.predicted_p_recovery < winning_score.predicted_p_recovery:
                    why_not[s.action] = f"Lower predicted recovery probability ({s.predicted_p_recovery:.0%} vs {winning_score.predicted_p_recovery:.0%})."
                else:
                    why_not[s.action] = "Higher intervention or customer fatigue cost."

        summary_text = (
            f"Action '{selected_action}' selected with expected net value ₹{winning_score.expected_net_value:,.2f}."
            if decision_status != "BLOCK"
            else f"Intervention blocked (Status: BLOCK). Selected action '{selected_action}' to avoid unnecessary cost or customer fatigue."
        )

        explanation = Explanation(
            summary=summary_text,
            key_factors=[
                f"Customer tenure: {features.customer_tenure_months} months ({features.customer_segment})",
                f"Failure reason: {features.failure_reason}",
                f"Contacts (24h/7d): {features.contacts_24h}/{features.contacts_7d}",
                f"Consecutive failures: {features.consecutive_failures}"
            ],
            why_selected=f"Selected action '{selected_action}' has highest expected net value in feasible set.",
            why_not_selected=why_not,
            customer_message_preview=(
                f"Hi {features.customer_id}, we noticed an issue with your payment of ₹{features.amount:,.2f}. Click here to update details."
                if selected_action in ["WhatsApp Nudge", "Personalized Email", "Payment Method Update"]
                else None
            )
        )

        decision_id = f"dec_{uuid.uuid4().hex[:10]}"

        return DecisionContract(
            decision_id=decision_id,
            payment_id=features.payment_id,
            timestamp=datetime.utcnow(),
            model_version=settings.MODEL_VERSION,
            policy_version=settings.POLICY_VERSION,
            feature_snapshot=features.model_dump(),
            candidate_actions=ACTIONS,
            feasible_actions=feasible_actions,
            blocked_actions=blocked_actions,
            candidate_scores=candidate_scores,
            predicted_recovery_probability=round(winning_score.predicted_p_recovery, 4),
            expected_recovered_amount=round(winning_score.expected_recovered_amount, 2),
            intervention_cost=round(winning_score.intervention_cost, 2),
            incentive_cost=round(winning_score.incentive_cost, 2),
            fatigue_penalty=round(winning_score.fatigue_penalty, 2),
            risk_penalty=round(winning_score.risk_penalty, 2),
            expected_net_value=round(winning_score.expected_net_value, 2),
            selected_action=selected_action,
            decision_status=decision_status,
            approval_required=approval_required,
            guardrail_results=guardrail_results,
            explanation=explanation,
            execution_status=execution_status
        )
