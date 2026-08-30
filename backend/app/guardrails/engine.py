from typing import List, Dict, Tuple, Any
from app.schemas.pydantic_schemas import PreDecisionFeatures, GuardrailResult, BlockedAction
from app.core.config import settings

class DeterministicConstraintEngine:
    """
    Deterministic Constraints Engine.
    Evaluates Constraints 1-5 to produce the Feasible Action Set.
    Neither ML models nor LLM outputs can EVER override these constraints.
    """
    def evaluate_constraints(
        self,
        features: PreDecisionFeatures,
        candidate_actions: List[str]
    ) -> Tuple[List[str], List[BlockedAction], List[GuardrailResult], bool]:
        """
        Returns:
        - feasible_actions: List[str]
        - blocked_actions: List[BlockedAction]
        - guardrail_results: List[GuardrailResult]
        - hard_block_payment: bool (True if payment must be immediately BLOCKED)
        """
        guardrail_results: List[GuardrailResult] = []
        blocked_actions_map: Dict[str, str] = {}
        hard_block = False

        # Constraint 1: Safety / Policy Constraints (Do Not Contact)
        if features.do_not_contact:
            hard_block = True
            guardrail_results.append(GuardrailResult(
                guardrail="Safety / Policy Constraint",
                status="BLOCK",
                reason="Customer has active Do-Not-Contact flag set.",
                metadata={"do_not_contact": True}
            ))

        # Constraint 2: Customer Contact Constraints (24h and 7d limits)
        if features.contacts_24h >= settings.MAX_CONTACTS_24H:
            msg = f"Customer received {features.contacts_24h} contacts in 24h (limit: {settings.MAX_CONTACTS_24H})."
            guardrail_results.append(GuardrailResult(
                guardrail="Customer Contact Constraint (24h)",
                status="BLOCK",
                reason=msg,
                metadata={"contacts_24h": features.contacts_24h}
            ))
            for act in ["Personalized Email", "WhatsApp Nudge", "Incentive Offer", "Payment Method Update"]:
                blocked_actions_map[act] = msg

        if features.contacts_7d >= settings.MAX_CONTACTS_7D:
            msg = f"Customer received {features.contacts_7d} contacts in 7d (limit: {settings.MAX_CONTACTS_7D})."
            guardrail_results.append(GuardrailResult(
                guardrail="Customer Contact Constraint (7d)",
                status="BLOCK",
                reason=msg,
                metadata={"contacts_7d": features.contacts_7d}
            ))
            for act in ["Personalized Email", "WhatsApp Nudge", "Incentive Offer", "Payment Method Update"]:
                blocked_actions_map[act] = msg

        # Constraint 3: Financial Risk Constraints (Incentive caps & minimum amounts)
        if features.amount < 1000.0:
            msg = f"Transaction amount ₹{features.amount:,.2f} is below ₹1,000 threshold for incentive offer."
            blocked_actions_map["Incentive Offer"] = msg

        if features.failure_reason == "Insufficient Funds":
            blocked_actions_map["Incentive Offer"] = "Insufficient Funds failure is non-price-related; discount incentive blocked in favor of delayed retry timing."

        # Constraint 4: Operational Constraints (Max retries & Retry delays)
        if features.consecutive_failures >= settings.MAX_CONSECUTIVE_FAILURES:
            msg = f"Consecutive failure count ({features.consecutive_failures}) reached maximum limit ({settings.MAX_CONSECUTIVE_FAILURES})."
            guardrail_results.append(GuardrailResult(
                guardrail="Operational Retry Limit",
                status="BLOCK",
                reason=msg,
                metadata={"consecutive_failures": features.consecutive_failures}
            ))
            for act in ["Retry Immediately", "Retry Delay 6h", "Retry Delay 18h"]:
                blocked_actions_map[act] = msg

        # Specific rule: Insufficient Funds cannot be Retried Immediately or use Payment Method Update
        if features.failure_reason == "Insufficient Funds":
            msg_retry = "Insufficient Funds failure requires delay (Immediate retry blocked)."
            blocked_actions_map["Retry Immediately"] = msg_retry
            blocked_actions_map["Payment Method Update"] = "Payment instrument is valid; Insufficient Funds requires retry timing, not method update."
            guardrail_results.append(GuardrailResult(
                guardrail="Minimum Retry Delay Constraint",
                status="PASS",
                reason=msg_retry,
                metadata={"failure_reason": features.failure_reason}
            ))

        # Specific rule: Technical downtime does not require Payment Method Update
        if features.failure_reason in ["Network Timeout", "Bank Downtime"]:
            blocked_actions_map["Payment Method Update"] = f"Technical/bank failure ({features.failure_reason}) does not require updating payment instrument."

        # Specific rule: Expired Card failures cannot be retried or nudged generically; requires Payment Method Update
        if features.failure_reason == "Expired Card":
            msg_retry = "Expired Card failure cannot be retried. Requires Payment Method Update."
            for act in ["Retry Immediately", "Retry Delay 6h", "Retry Delay 18h"]:
                blocked_actions_map[act] = msg_retry
            msg_nudge = "Expired Card failure cannot be resolved via generic outreach; requires instrument update link."
            for act in ["Personalized Email", "WhatsApp Nudge", "Incentive Offer"]:
                blocked_actions_map[act] = msg_nudge

        # Constraint 5: Human Escalation Rules (High-value threshold)
        if features.amount < settings.HIGH_VALUE_THRESHOLD:
            # Human escalation is not suitable for small transactions
            msg = f"Transaction amount ₹{features.amount:,.2f} below ₹{settings.HIGH_VALUE_THRESHOLD:,.2f} threshold for Human Escalation."
            blocked_actions_map["Human Escalation"] = msg

        # Compute Feasible Actions
        feasible_actions = []
        blocked_actions_list = []

        if hard_block:
            # Hard block: only Stop Intervention is feasible
            feasible_actions = ["Stop Intervention"]
            for act in candidate_actions:
                if act != "Stop Intervention":
                    blocked_actions_list.append(BlockedAction(action=act, reason="Customer Do Not Contact flag enabled"))
        else:
            for act in candidate_actions:
                if act in blocked_actions_map:
                    blocked_actions_list.append(BlockedAction(action=act, reason=blocked_actions_map[act]))
                else:
                    feasible_actions.append(act)

            # Ensure Stop Intervention is always feasible
            if "Stop Intervention" not in feasible_actions:
                feasible_actions.append("Stop Intervention")

        if not guardrail_results:
            guardrail_results.append(GuardrailResult(
                guardrail="Standard Policy Check",
                status="PASS",
                reason="All standard policy constraints satisfied.",
                metadata={}
            ))

        return feasible_actions, blocked_actions_list, guardrail_results, hard_block
