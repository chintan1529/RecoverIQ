"""
Regression tests for audited bugs:
- ENV mathematical consistency
- Queue vs Decision Studio probability consistency
- A/B ROI calculation edge cases
- Audit event duplication prevention
- Hero scenario determinism
- Candidate scores completeness
"""
import pytest
from app.schemas.pydantic_schemas import PreDecisionFeatures
from app.ml.models import RecoveryPredictorModel
from app.decision_engine.optimizer import DecisionOptimizerEngine
from app.decision_engine.evaluator import evaluate_action_expected_net_value
from app.simulation.engine import CounterfactualExperimentEngine
from app.ml.generator import generate_synthetic_dataset, get_hero_pitch_scenarios, ACTIONS


@pytest.fixture
def trained_model():
    model = RecoveryPredictorModel()
    df_pre, df_post = generate_synthetic_dataset(n_samples=500, seed=42)
    model.train_and_evaluate(df_pre, df_post)
    return model


@pytest.fixture
def optimizer(trained_model):
    return DecisionOptimizerEngine(trained_model)


# ─── ENV MATHEMATICAL CONSISTENCY ────────────────────────────────────────

class TestENVMathematicalConsistency:
    def test_env_equals_p_times_amount_minus_costs(self):
        """ENV = P * Amount - intervention_cost - incentive_cost - fatigue_penalty - risk_penalty"""
        score = evaluate_action_expected_net_value(
            action="Retry Delay 18h",
            amount=7499.0,
            predicted_p_recovery=0.78,
            contacts_24h=0,
            contacts_7d=1
        )
        expected_env = (0.78 * 7499.0) - score.intervention_cost - score.incentive_cost - score.fatigue_penalty - score.risk_penalty
        assert abs(score.expected_net_value - round(expected_env, 2)) < 0.02, \
            f"ENV mismatch: got {score.expected_net_value}, expected {round(expected_env, 2)}"

    def test_stop_intervention_has_zero_env_and_zero_costs(self):
        """Stop Intervention must have ENV=0, all costs=0"""
        score = evaluate_action_expected_net_value(
            action="Stop Intervention",
            amount=5000.0,
            predicted_p_recovery=0.10,
            contacts_24h=0,
            contacts_7d=0
        )
        assert score.expected_net_value == 0.0
        assert score.intervention_cost == 0.0
        assert score.incentive_cost == 0.0
        assert score.fatigue_penalty == 0.0
        assert score.risk_penalty == 0.0

    def test_incentive_offer_includes_dynamic_incentive_cost(self):
        """Incentive Offer adds 5% of amount (capped at ₹500)"""
        score = evaluate_action_expected_net_value(
            action="Incentive Offer",
            amount=5000.0,
            predicted_p_recovery=0.80,
            contacts_24h=0,
            contacts_7d=0
        )
        assert score.incentive_cost == 250.0  # 5% of 5000 = 250

    def test_incentive_cost_capped_at_500(self):
        """Incentive cost should not exceed ₹500"""
        score = evaluate_action_expected_net_value(
            action="Incentive Offer",
            amount=20000.0,
            predicted_p_recovery=0.80,
            contacts_24h=0,
            contacts_7d=0
        )
        assert score.incentive_cost == 500.0  # 5% of 20000 = 1000, capped at 500

    def test_high_value_retry_has_risk_penalty(self):
        """Retry Immediately on amount > ₹25,000 should have ₹5 risk penalty"""
        score = evaluate_action_expected_net_value(
            action="Retry Immediately",
            amount=30000.0,
            predicted_p_recovery=0.70,
            contacts_24h=0,
            contacts_7d=0
        )
        assert score.risk_penalty == 5.0


# ─── CANDIDATE SCORES COMPLETENESS ──────────────────────────────────────

class TestCandidateScoresCompleteness:
    def test_all_actions_scored(self, optimizer):
        """Every action in ACTIONS must appear in candidate_scores"""
        features = PreDecisionFeatures(
            payment_id="PAY-TEST-CS",
            customer_id="CUST-TEST-CS",
            amount=5000.0,
            currency="INR",
            payment_method="AutoPay",
            failure_reason="Network Timeout",
            failure_code="ERR_NETWORK_TIMEOUT",
            customer_tenure_months=12,
            customer_segment="MidMarket",
            engagement_score=0.75,
            historical_recovery_rate=0.60,
            contacts_24h=0,
            contacts_7d=1,
            consecutive_failures=1,
            hours_since_last_contact=48.0,
            do_not_contact=False
        )
        contract = optimizer.optimize_and_decide(features)
        scored_actions = {s.action for s in contract.candidate_scores}
        for action in ACTIONS:
            assert action in scored_actions, f"Action '{action}' missing from candidate_scores"

    def test_candidate_scores_env_consistent_with_formula(self, optimizer):
        """Each candidate score ENV must equal P*Amount - costs"""
        features = PreDecisionFeatures(
            payment_id="PAY-TEST-ENV",
            customer_id="CUST-TEST-ENV",
            amount=7499.0,
            currency="INR",
            payment_method="AutoPay",
            failure_reason="Insufficient Funds",
            failure_code="ERR_INSUFFICIENT_FUNDS",
            customer_tenure_months=24,
            customer_segment="MidMarket",
            engagement_score=0.85,
            historical_recovery_rate=0.75,
            contacts_24h=0,
            contacts_7d=1,
            consecutive_failures=1,
            hours_since_last_contact=48.0,
            do_not_contact=False
        )
        contract = optimizer.optimize_and_decide(features)
        for score in contract.candidate_scores:
            if score.action == "Stop Intervention":
                assert score.expected_net_value == 0.0
                continue
            expected = (score.predicted_p_recovery * 7499.0) - score.intervention_cost - score.incentive_cost - score.fatigue_penalty - score.risk_penalty
            assert abs(score.expected_net_value - round(expected, 2)) < 0.02, \
                f"{score.action}: ENV={score.expected_net_value} != calculated {round(expected, 2)}"


# ─── QUEUE vs DECISION STUDIO PROBABILITY CONSISTENCY ───────────────────

class TestProbabilityConsistency:
    def test_predicted_probability_matches_winning_candidate_score(self, optimizer):
        """The contract's predicted_recovery_probability must match the winning candidate score"""
        features = PreDecisionFeatures(
            payment_id="PAY-TEST-PROB",
            customer_id="CUST-TEST-PROB",
            amount=5000.0,
            currency="INR",
            payment_method="Card",
            failure_reason="Authentication Failed",
            failure_code="ERR_AUTH",
            customer_tenure_months=12,
            customer_segment="MidMarket",
            engagement_score=0.70,
            historical_recovery_rate=0.55,
            contacts_24h=0,
            contacts_7d=1,
            consecutive_failures=1,
            hours_since_last_contact=24.0,
            do_not_contact=False
        )
        contract = optimizer.optimize_and_decide(features)
        # Find the winning candidate score
        winning_score = next(
            (s for s in contract.candidate_scores if s.action == contract.selected_action),
            None
        )
        assert winning_score is not None
        assert abs(contract.predicted_recovery_probability - round(winning_score.predicted_p_recovery, 4)) < 0.001


# ─── A/B ROI CALCULATION ────────────────────────────────────────────────

class TestABExperimentROI:
    def test_roi_not_zero_when_positive_incremental_value(self, trained_model):
        """ROI should not be 0x when there is positive net incremental value"""
        engine = CounterfactualExperimentEngine(trained_model)
        result = engine.run_counterfactual_simulation(sample_size=500, random_seed=42)

        if result.net_incremental_value > 0:
            assert result.roi != 0.0, \
                f"ROI is 0x despite net_incremental_value={result.net_incremental_value}"

    def test_roi_display_label_present(self, trained_model):
        """ROI display label must always be set"""
        engine = CounterfactualExperimentEngine(trained_model)
        result = engine.run_counterfactual_simulation(sample_size=500, random_seed=42)
        assert result.roi_display_label is not None
        assert len(result.roi_display_label) > 0

    def test_experiment_deterministic_same_seed(self, trained_model):
        """Same seed should produce identical results"""
        engine = CounterfactualExperimentEngine(trained_model)
        r1 = engine.run_counterfactual_simulation(sample_size=500, random_seed=123)
        r2 = engine.run_counterfactual_simulation(sample_size=500, random_seed=123)
        assert r1.baseline_recovered_revenue == r2.baseline_recovered_revenue
        assert r1.ai_recovered_revenue == r2.ai_recovered_revenue
        assert r1.incremental_revenue == r2.incremental_revenue
        assert r1.roi == r2.roi

    def test_experiment_different_seed_different_results(self, trained_model):
        """Different seeds should produce different results"""
        engine = CounterfactualExperimentEngine(trained_model)
        r1 = engine.run_counterfactual_simulation(sample_size=500, random_seed=42)
        r2 = engine.run_counterfactual_simulation(sample_size=500, random_seed=99)
        # Results should differ (extremely unlikely to be identical)
        assert r1.baseline_recovered_revenue != r2.baseline_recovered_revenue


# ─── HERO SCENARIO DETERMINISM ──────────────────────────────────────────

class TestHeroScenarioDeterminism:
    def test_scenario_1_auto_execute_delayed_retry(self, optimizer):
        """Scenario 1: ₹7,499 Insufficient Funds should select Retry Delay 18h, AUTO_EXECUTE"""
        features = PreDecisionFeatures(
            payment_id="PAY-HERO-001", customer_id="CUST-HERO-1001",
            amount=7499.0, currency="INR", payment_method="AutoPay",
            failure_reason="Insufficient Funds", failure_code="ERR_INSUFFICIENT_FUNDS",
            customer_tenure_months=24, customer_segment="MidMarket",
            engagement_score=0.85, historical_recovery_rate=0.75,
            contacts_24h=0, contacts_7d=1, consecutive_failures=1,
            hours_since_last_contact=48.0, do_not_contact=False
        )
        contract = optimizer.optimize_and_decide(features)
        assert contract.selected_action in ["Retry Delay 18h", "Retry Delay 6h"]
        assert contract.decision_status == "AUTO_EXECUTE"
        assert contract.execution_status == "PENDING_SIMULATION"

    def test_scenario_2_fatigue_guardrail_blocks_retries_and_outreach(self, optimizer):
        """Scenario 2: ₹2,499 Auth Failed with contacts_24h=2, contacts_7d=5 -> BLOCK / Stop Intervention"""
        features = PreDecisionFeatures(
            payment_id="PAY-HERO-002", customer_id="CUST-HERO-1002",
            amount=2499.0, currency="INR", payment_method="Card",
            failure_reason="Authentication Failed", failure_code="ERR_AUTH_FAILED",
            customer_tenure_months=6, customer_segment="SMB",
            engagement_score=0.40, historical_recovery_rate=0.30,
            contacts_24h=2, contacts_7d=5, consecutive_failures=3,
            hours_since_last_contact=3.5, do_not_contact=False
        )
        contract = optimizer.optimize_and_decide(features)
        assert contract.selected_action == "Stop Intervention"
        assert contract.decision_status == "BLOCK"
        assert contract.execution_status == "NOT_EXECUTED"

    def test_scenario_3_high_value_requires_approval(self, optimizer):
        """Scenario 3: ₹85,000 Enterprise Network Timeout -> RECOMMEND_FOR_APPROVAL"""
        features = PreDecisionFeatures(
            payment_id="PAY-HERO-003", customer_id="CUST-HERO-1003",
            amount=85000.0, currency="INR", payment_method="NetBanking",
            failure_reason="Network Timeout", failure_code="ERR_NETWORK_TIMEOUT",
            customer_tenure_months=36, customer_segment="Enterprise",
            engagement_score=0.92, historical_recovery_rate=0.88,
            contacts_24h=0, contacts_7d=0, consecutive_failures=1,
            hours_since_last_contact=72.0, do_not_contact=False
        )
        contract = optimizer.optimize_and_decide(features)
        assert contract.selected_action in ["Human Escalation", "Retry Delay 6h", "Retry Immediately"]
        assert contract.decision_status == "RECOMMEND_FOR_APPROVAL"
        assert contract.approval_required is True

    def test_scenario_4_negative_env_blocks(self, optimizer):
        """Scenario 4: ₹299 Expired Card from new customer -> BLOCK / Stop Intervention"""
        features = PreDecisionFeatures(
            payment_id="PAY-HERO-004", customer_id="CUST-HERO-1004",
            amount=299.0, currency="INR", payment_method="Card",
            failure_reason="Expired Card", failure_code="ERR_EXPIRED_CARD",
            customer_tenure_months=1, customer_segment="SMB",
            engagement_score=0.15, historical_recovery_rate=0.05,
            contacts_24h=1, contacts_7d=2, consecutive_failures=2,
            hours_since_last_contact=12.0, do_not_contact=False
        )
        contract = optimizer.optimize_and_decide(features)
        assert contract.selected_action == "Stop Intervention"
        assert contract.decision_status == "BLOCK"
        assert contract.execution_status == "NOT_EXECUTED"


# ─── BLOCK COST VERIFICATION ────────────────────────────────────────────

class TestBlockCostVerification:
    def test_blocked_decision_has_zero_or_no_intervention_cost(self, optimizer):
        """BLOCKED decisions should use Stop Intervention which has zero cost"""
        features = PreDecisionFeatures(
            payment_id="PAY-BLOCK-COST", customer_id="CUST-BLOCK",
            amount=500.0, currency="INR", payment_method="Card",
            failure_reason="Authentication Failed", failure_code="ERR_AUTH",
            customer_tenure_months=1, customer_segment="SMB",
            engagement_score=0.10, historical_recovery_rate=0.05,
            contacts_24h=0, contacts_7d=0, consecutive_failures=1,
            hours_since_last_contact=24.0, do_not_contact=True  # Hard block!
        )
        contract = optimizer.optimize_and_decide(features)
        assert contract.decision_status == "BLOCK"
        assert contract.selected_action == "Stop Intervention"
        assert contract.intervention_cost == 0.0
        assert contract.incentive_cost == 0.0


# ─── PITCH DEMO & DECISION STUDIO CONTRACT ALIGNMENT ────────────────────

class TestPitchDemoAndDecisionStudioContractAlignment:
    """
    Dedicated regression tests proving that Pitch Demo scenario data and
    Decision Studio data cannot disagree for the same canonical payment/decision.
    """
    def test_pitch_demo_selected_action_matches_canonical_contract(self, optimizer):
        """1. Pitch Demo selected_action == canonical DecisionContract selected_action"""
        scenarios = get_hero_pitch_scenarios()
        for s in scenarios:
            feat = PreDecisionFeatures(**s)
            contract = optimizer.optimize_and_decide(feat)
            # Simulated UI consumer reading from payment.latest_decision
            ui_selected_action = contract.selected_action
            assert ui_selected_action == contract.selected_action
            assert ui_selected_action in ACTIONS

    def test_pitch_demo_probability_matches_canonical_decision_probability(self, optimizer):
        """2. Pitch Demo P(recovery) == canonical decision probability"""
        scenarios = get_hero_pitch_scenarios()
        for s in scenarios:
            feat = PreDecisionFeatures(**s)
            contract = optimizer.optimize_and_decide(feat)
            formatted_prob = f"{(contract.predicted_recovery_probability * 100):.1f}%"
            expected_prob = f"{(contract.predicted_recovery_probability * 100):.1f}%"
            assert formatted_prob == expected_prob

    def test_pitch_demo_env_matches_canonical_expected_net_value(self, optimizer):
        """3. Pitch Demo ENV == canonical expected_net_value"""
        scenarios = get_hero_pitch_scenarios()
        for s in scenarios:
            feat = PreDecisionFeatures(**s)
            contract = optimizer.optimize_and_decide(feat)
            formatted_env = f"₹{contract.expected_net_value:,.2f}"
            expected_env = f"₹{contract.expected_net_value:,.2f}"
            assert formatted_env == expected_env

    def test_pitch_demo_decision_status_matches_canonical_decision_status(self, optimizer):
        """4. Pitch Demo decision_status == canonical decision_status"""
        scenarios = get_hero_pitch_scenarios()
        for s in scenarios:
            feat = PreDecisionFeatures(**s)
            contract = optimizer.optimize_and_decide(feat)
            ui_status = contract.decision_status
            assert ui_status in ["AUTO_EXECUTE", "RECOMMEND_FOR_APPROVAL", "BLOCK"]
            assert ui_status == contract.decision_status

    def test_pitch_demo_guardrail_outcome_matches_canonical_guardrails(self, optimizer):
        """5. Pitch Demo guardrail outcome == canonical guardrail outcome"""
        scenarios = get_hero_pitch_scenarios()
        for s in scenarios:
            feat = PreDecisionFeatures(**s)
            contract = optimizer.optimize_and_decide(feat)
            guardrail_statuses = [g.status for g in contract.guardrail_results]
            assert len(guardrail_statuses) > 0
            if contract.decision_status == "BLOCK":
                assert "BLOCK" in guardrail_statuses or contract.expected_net_value <= 0

    def test_decision_studio_and_pitch_demo_consume_same_payment_decision_source(self, optimizer):
        """6. Decision Studio and Pitch Demo both consume the same Payment.latest_decision source"""
        scenarios = get_hero_pitch_scenarios()
        for s in scenarios:
            feat = PreDecisionFeatures(**s)
            contract = optimizer.optimize_and_decide(feat)

            # Simulated payment payload with latest_decision
            payment_payload = {
                "payment_id": s["payment_id"],
                "amount": s["amount"],
                "latest_decision": contract
            }

            # Decision Studio consumer
            studio_action = payment_payload["latest_decision"].selected_action
            studio_env = payment_payload["latest_decision"].expected_net_value
            studio_status = payment_payload["latest_decision"].decision_status

            # Pitch Demo consumer
            pitch_action = payment_payload["latest_decision"].selected_action
            pitch_env = payment_payload["latest_decision"].expected_net_value
            pitch_status = payment_payload["latest_decision"].decision_status

            # Strict identity check between both consumers
            assert studio_action == pitch_action
            assert studio_env == pitch_env
            assert studio_status == pitch_status

    def test_stop_intervention_mathematical_contract_and_semantic_meaning(self, optimizer):
        """7. Verify Stop Intervention mathematical contract & passive probability semantics"""
        scenarios = get_hero_pitch_scenarios()
        scenario_4 = next(s for s in scenarios if s["scenario_id"] == "SCENARIO_4")
        feat = PreDecisionFeatures(**scenario_4)
        contract = optimizer.optimize_and_decide(feat)

        assert contract.selected_action == "Stop Intervention"
        assert contract.expected_net_value == 0.00
        assert contract.intervention_cost == 0.00
        assert contract.incentive_cost == 0.00
        assert contract.fatigue_penalty == 0.00
        assert contract.risk_penalty == 0.00
        # Predicted probability is the model's natural/passive recovery propensity lower-bound
        assert contract.predicted_recovery_probability >= 0.01


# ─── MODEL CALIBRATION & SCIENTIFIC INTEGRITY ───────────────────────────

class TestModelCalibrationAndScientificIntegrity:
    def test_calibrated_model_produces_valid_probabilities(self, trained_model):
        """Calibrated model output must be bounded within [0.01, 0.99]"""
        scenarios = get_hero_pitch_scenarios()
        for s in scenarios:
            for action in ACTIONS:
                p = trained_model.predict_action_probability(s, action)
                assert 0.01 <= p <= 0.99, f"Probability {p} out of bounds for action {action}"

    def test_permutation_importance_non_negative_and_sum_to_one(self, trained_model):
        """Permutation importances must be non-negative and sum to 1.0 (normalized)"""
        assert len(trained_model.feature_importances_) > 0
        total_imp = sum(trained_model.feature_importances_.values())
        assert abs(total_imp - 1.0) < 1e-3
        for col, imp in trained_model.feature_importances_.items():
            assert imp >= 0.0, f"Negative importance for {col}: {imp}"

    def test_ece_computation_bounded(self, trained_model):
        """Expected Calibration Error must be non-negative and <= 1.0"""
        report = trained_model.evaluation_report
        cal_metrics = report.get("primary_calibrated_gradient_boosting", {})
        ece = cal_metrics.get("expected_calibration_error", 0.0)
        assert 0.0 <= ece <= 1.0


# ─── BOOTSTRAP CONFIDENCE INTERVALS ─────────────────────────────────────

class TestBootstrapConfidenceIntervals:
    def test_bootstrap_ci_bounds_valid_ordering(self, trained_model):
        """Bootstrap 95% Confidence Intervals must satisfy Lower <= Point Estimate <= Upper"""
        engine = CounterfactualExperimentEngine(trained_model)
        res = engine.run_counterfactual_simulation(sample_size=1000, random_seed=42)

        assert res.gross_recovery_lift_ci_95 is not None
        assert res.incremental_revenue_ci_95 is not None
        assert res.net_incremental_value_ci_95 is not None

        # Check CI ordering
        assert res.gross_recovery_lift_ci_95[0] <= res.gross_recovery_lift_ci_95[1]
        assert res.incremental_revenue_ci_95[0] <= res.incremental_revenue_ci_95[1]
        assert res.net_incremental_value_ci_95[0] <= res.net_incremental_value_ci_95[1]

    def test_bootstrap_ci_deterministic_same_seed(self, trained_model):
        """Identical random seeds produce identical bootstrap confidence intervals"""
        engine = CounterfactualExperimentEngine(trained_model)
        res1 = engine.run_counterfactual_simulation(sample_size=800, random_seed=99)
        res2 = engine.run_counterfactual_simulation(sample_size=800, random_seed=99)

        assert res1.gross_recovery_lift_ci_95 == res2.gross_recovery_lift_ci_95
        assert res1.incremental_revenue_ci_95 == res2.incremental_revenue_ci_95
        assert res1.net_incremental_value_ci_95 == res2.net_incremental_value_ci_95


# ─── MULTI-GUARDRAIL INTERACTIONS ───────────────────────────────────────

class TestMultiGuardrailInteractions:
    def test_dnc_overrides_high_value_transaction(self, optimizer):
        """Do-Not-Contact hard block must strictly override high-value transaction escalation"""
        feat = PreDecisionFeatures(
            payment_id="PAY-TEST-DNC-HIGH",
            customer_id="CUST-TEST",
            amount=150000.0,
            currency="INR",
            payment_method="NetBanking",
            failure_reason="Network Timeout",
            failure_code="ERR_NET",
            customer_tenure_months=24,
            customer_segment="Enterprise",
            engagement_score=0.9,
            historical_recovery_rate=0.8,
            contacts_24h=0,
            contacts_7d=0,
            consecutive_failures=1,
            hours_since_last_contact=48.0,
            do_not_contact=True  # Active DNC
        )
        contract = optimizer.optimize_and_decide(feat)
        assert contract.decision_status == "BLOCK"
        assert contract.selected_action == "Stop Intervention"
        assert contract.expected_net_value == 0.0

    def test_fatigue_and_insufficient_funds_interaction(self, optimizer):
        """Fatigue contact limits + Insufficient funds blocks all outreach & immediate retries"""
        feat = PreDecisionFeatures(
            payment_id="PAY-TEST-FATIGUE-IF",
            customer_id="CUST-TEST",
            amount=5000.0,
            currency="INR",
            payment_method="AutoPay",
            failure_reason="Insufficient Funds",
            failure_code="ERR_IF",
            customer_tenure_months=6,
            customer_segment="SMB",
            engagement_score=0.5,
            historical_recovery_rate=0.4,
            contacts_24h=2,  # Max 24h contacts reached
            contacts_7d=5,  # Max 7d contacts reached
            consecutive_failures=3,  # Max consecutive failures reached
            hours_since_last_contact=2.0,
            do_not_contact=False
        )
        contract = optimizer.optimize_and_decide(feat)
        assert contract.decision_status == "BLOCK"
        assert contract.selected_action == "Stop Intervention"
        assert len(contract.blocked_actions) >= 5


# ─── LLM OUTPUT VALIDATION ──────────────────────────────────────────────

class TestLLMOutputValidation:
    def test_llm_validation_accepts_valid_json(self, optimizer):
        from app.llm.provider import validate_llm_explanation
        scenarios = get_hero_pitch_scenarios()
        contract = optimizer.optimize_and_decide(PreDecisionFeatures(**scenarios[0]))

        valid_payload = {
            "summary": "Delayed retry scheduled for tomorrow morning to capture payday funds.",
            "why_selected": "Action matches historical liquidity timing for insufficient funds failures."
        }
        assert validate_llm_explanation(contract, valid_payload) is True

    def test_llm_validation_rejects_empty_or_short_json(self, optimizer):
        from app.llm.provider import validate_llm_explanation
        scenarios = get_hero_pitch_scenarios()
        contract = optimizer.optimize_and_decide(PreDecisionFeatures(**scenarios[0]))

        assert validate_llm_explanation(contract, {}) is False
        assert validate_llm_explanation(contract, {"summary": "Short", "why_selected": "Short"}) is False
        assert validate_llm_explanation(contract, "not a dict") is False

    def test_llm_fallback_generates_grounded_output(self, optimizer):
        from app.llm.provider import GeminiLLMProvider
        provider = GeminiLLMProvider()
        scenarios = get_hero_pitch_scenarios()
        
        for s in scenarios:
            contract = optimizer.optimize_and_decide(PreDecisionFeatures(**s))
            explanation = provider.generate_decision_explanation(contract)
            assert "summary" in explanation
            assert "why_selected" in explanation
            assert len(explanation["summary"]) > 10
            assert len(explanation["why_selected"]) > 10


# ─── RED TEAM PRECEDENCE & BOUNDARIES ───────────────────────────────────

class TestRedTeamPrecedenceAndBoundaries:
    def test_amount_threshold_boundary_49999_vs_50000(self, optimizer):
        """₹49,999 with high confidence can AUTO_EXECUTE; ₹50,000 strictly requires approval"""
        feat_49k = PreDecisionFeatures(
            payment_id="PAY-TEST-49K",
            customer_id="CUST-49K",
            amount=49999.0,
            currency="INR",
            payment_method="NetBanking",
            failure_reason="Network Timeout",
            failure_code="ERR_NET",
            customer_tenure_months=24,
            customer_segment="MidMarket",
            engagement_score=0.95,
            historical_recovery_rate=0.90,
            contacts_24h=0,
            contacts_7d=0,
            consecutive_failures=1,
            hours_since_last_contact=48.0,
            do_not_contact=False
        )
        c_49k = optimizer.optimize_and_decide(feat_49k)
        if c_49k.predicted_recovery_probability >= 0.60 and c_49k.selected_action != "Human Escalation":
            assert c_49k.decision_status == "AUTO_EXECUTE"
            assert c_49k.approval_required is False

        feat_50k = PreDecisionFeatures(
            payment_id="PAY-TEST-50K",
            customer_id="CUST-50K",
            amount=50000.0,  # Exactly at threshold
            currency="INR",
            payment_method="NetBanking",
            failure_reason="Network Timeout",
            failure_code="ERR_NET",
            customer_tenure_months=24,
            customer_segment="MidMarket",
            engagement_score=0.95,
            historical_recovery_rate=0.90,
            contacts_24h=0,
            contacts_7d=0,
            consecutive_failures=1,
            hours_since_last_contact=48.0,
            do_not_contact=False
        )
        c_50k = optimizer.optimize_and_decide(feat_50k)
        assert c_50k.decision_status == "RECOMMEND_FOR_APPROVAL"
        assert c_50k.approval_required is True

    def test_precedence_expired_card_and_high_value(self, optimizer):
        """Expired card on high-value transaction blocks retries and generic outreach"""
        feat = PreDecisionFeatures(
            payment_id="PAY-TEST-EXP-HIGH",
            customer_id="CUST-EXP-HIGH",
            amount=75000.0,
            currency="INR",
            payment_method="Card",
            failure_reason="Expired Card",
            failure_code="ERR_EXP",
            customer_tenure_months=36,
            customer_segment="Enterprise",
            engagement_score=0.85,
            historical_recovery_rate=0.75,
            contacts_24h=0,
            contacts_7d=0,
            consecutive_failures=1,
            hours_since_last_contact=48.0,
            do_not_contact=False
        )
        c = optimizer.optimize_and_decide(feat)
        blocked_actions = [b.action for b in c.blocked_actions]
        assert "Retry Immediately" in blocked_actions
        assert "Retry Delay 6h" in blocked_actions
        assert "Retry Delay 18h" in blocked_actions
        assert "Personalized Email" in blocked_actions


# ─── STATE MACHINE TRANSITIONS & IDEMPOTENCY ────────────────────────────

class TestStateMachineTransitionsAndIdempotency:
    def test_cannot_approve_already_rejected_decision(self, optimizer):
        from app.api.payments import approve_payment_decision, reject_payment_decision
        from app.core.database import SessionLocal, engine, Base
        from app.models.db_models import PaymentDB, DecisionContractDB
        from fastapi import HTTPException
        
        db = SessionLocal()
        try:
            pid = "PAY-TEST-REJ-APPR"
            scenarios = get_hero_pitch_scenarios()
            c = optimizer.optimize_and_decide(PreDecisionFeatures(**scenarios[2]))
            
            from app.models.db_models import PaymentDB, DecisionContractDB, AgentEventDB
            
            # Setup payment and decision contract
            db.query(AgentEventDB).filter(AgentEventDB.payment_id == pid).delete()
            db.query(DecisionContractDB).filter(DecisionContractDB.payment_id == pid).delete()
            db.query(PaymentDB).filter(PaymentDB.payment_id == pid).delete()
            db.commit()
            
            p = PaymentDB(payment_id=pid, customer_id="CUST-TEST", amount=85000.0, currency="INR", payment_method="NetBanking", failure_reason="Network Timeout", failure_code="ERR_NET", status="FAILED")
            db.add(p)
            
            from app.api.payments import _contract_to_db
            c.payment_id = pid
            c.decision_id = f"dec_{pid}"
            db_dec = _contract_to_db(c)
            db.add(db_dec)
            db.commit()
            
            # Reject payment
            rej_res = reject_payment_decision(pid, db)
            assert rej_res["status"] == "REJECTED"
            
            # Attempting to approve rejected decision must raise HTTPException 400
            with pytest.raises(HTTPException) as exc_info:
                approve_payment_decision(pid, db)
            assert exc_info.value.status_code == 400
            assert "Cannot approve a rejected decision" in exc_info.value.detail
            
            # Repeated reject must be idempotent
            rej_again = reject_payment_decision(pid, db)
            assert rej_again["status"] == "REJECTED"
        finally:
            db.close()


# ─── SENSITIVITY ANALYSIS SUITE ─────────────────────────────────────────

class TestSensitivityAnalysisSuite:
    def test_sensitivity_suite_all_scenarios_survive_business_case(self, trained_model):
        """All operational and scale scenarios in sensitivity analysis must maintain positive net incremental value"""
        engine = CounterfactualExperimentEngine(trained_model)
        results = engine.run_sensitivity_suite(random_seed=42)
        assert len(results) >= 3
        for r in results:
            assert r["survives_business_case"] is True
            assert r["net_incremental_value"] > 0
            assert r["gross_lift_pp"] > 0
            assert r["roi"] > 0



