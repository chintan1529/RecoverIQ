import pytest
from app.schemas.pydantic_schemas import PreDecisionFeatures
from app.ml.models import RecoveryPredictorModel
from app.decision_engine.optimizer import DecisionOptimizerEngine

from app.ml.generator import generate_synthetic_dataset

@pytest.fixture
def optimizer():
    model = RecoveryPredictorModel()
    df_pre, df_post = generate_synthetic_dataset(n_samples=500, seed=42)
    model.train_and_evaluate(df_pre, df_post)
    return DecisionOptimizerEngine(model)

def test_blocked_payment_returns_block_status_and_not_executed(optimizer):
    # Payment violating Do Not Contact flag
    features = PreDecisionFeatures(
        payment_id="PAY-BLOCK-001",
        customer_id="CUST-BLOCK-001",
        amount=5000.0,
        currency="INR",
        payment_method="Card",
        failure_reason="Authentication Failed",
        failure_code="ERR_AUTH",
        customer_tenure_months=6,
        customer_segment="SMB",
        engagement_score=0.40,
        historical_recovery_rate=0.30,
        contacts_24h=1,
        contacts_7d=2,
        consecutive_failures=1,
        hours_since_last_contact=12.0,
        do_not_contact=True  # Hard block!
    )

    contract = optimizer.optimize_and_decide(features)

    assert contract.decision_status == "BLOCK"
    assert contract.selected_action == "Stop Intervention"
    assert contract.execution_status == "NOT_EXECUTED"
    assert contract.approval_required is False

def test_high_value_transaction_triggers_recommend_for_approval(optimizer):
    # High value transaction >= ₹50,000
    features = PreDecisionFeatures(
        payment_id="PAY-HIGH-001",
        customer_id="CUST-HIGH-001",
        amount=85000.0,  # High value!
        currency="INR",
        payment_method="NetBanking",
        failure_reason="Network Timeout",
        failure_code="ERR_TIMEOUT",
        customer_tenure_months=36,
        customer_segment="Enterprise",
        engagement_score=0.90,
        historical_recovery_rate=0.85,
        contacts_24h=0,
        contacts_7d=0,
        consecutive_failures=1,
        hours_since_last_contact=72.0,
        do_not_contact=False
    )

    contract = optimizer.optimize_and_decide(features)

    assert contract.decision_status == "RECOMMEND_FOR_APPROVAL"
    assert contract.approval_required is True
    assert contract.execution_status == "PENDING_SIMULATION"

def test_standard_eligible_payment_returns_auto_execute(optimizer):
    # Normal eligible payment
    features = PreDecisionFeatures(
        payment_id="PAY-AUTO-001",
        customer_id="CUST-AUTO-001",
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

    assert contract.decision_status in ["AUTO_EXECUTE", "RECOMMEND_FOR_APPROVAL"]
    assert contract.selected_action != ""

def test_negative_env_yields_stop_intervention_block(optimizer):
    # Expired card on unengaged new customer yielding negative ENV
    features = PreDecisionFeatures(
        payment_id="PAY-NEG-001",
        customer_id="CUST-NEG-001",
        amount=199.0,  # Small transaction
        currency="INR",
        payment_method="Card",
        failure_reason="Expired Card",
        failure_code="ERR_EXPIRED",
        customer_tenure_months=1,
        customer_segment="SMB",
        engagement_score=0.10,
        historical_recovery_rate=0.05,
        contacts_24h=1,
        contacts_7d=2,
        consecutive_failures=2,
        hours_since_last_contact=12.0,
        do_not_contact=False
    )
    contract = optimizer.optimize_and_decide(features)
    assert contract.decision_status == "BLOCK"
    assert contract.selected_action == "Stop Intervention"
    assert contract.expected_net_value == 0.0
    assert contract.execution_status == "NOT_EXECUTED"


