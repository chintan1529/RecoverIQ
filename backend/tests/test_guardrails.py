import pytest
from app.schemas.pydantic_schemas import PreDecisionFeatures
from app.guardrails.engine import DeterministicConstraintEngine

@pytest.fixture
def base_features():
    return PreDecisionFeatures(
        payment_id="PAY-TEST-001",
        customer_id="CUST-TEST-001",
        amount=5000.0,
        currency="INR",
        payment_method="AutoPay",
        failure_reason="Insufficient Funds",
        failure_code="ERR_INSUFFICIENT_FUNDS",
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

def test_do_not_contact_hard_blocks_payment(base_features):
    engine = DeterministicConstraintEngine()
    base_features.do_not_contact = True
    actions = ["Retry Immediately", "WhatsApp Nudge", "Stop Intervention"]
    
    feasible, blocked, results, hard_block = engine.evaluate_constraints(base_features, actions)
    
    assert hard_block is True
    assert feasible == ["Stop Intervention"]
    assert len(blocked) == 2

def test_consecutive_failures_limit_blocks_retries(base_features):
    engine = DeterministicConstraintEngine()
    base_features.consecutive_failures = 3  # Max limit
    actions = ["Retry Immediately", "Retry Delay 18h", "WhatsApp Nudge", "Stop Intervention"]
    
    feasible, blocked, results, hard_block = engine.evaluate_constraints(base_features, actions)
    
    assert hard_block is False
    assert "Retry Immediately" not in feasible
    assert "Retry Delay 18h" not in feasible
    assert "WhatsApp Nudge" in feasible

def test_insufficient_funds_blocks_immediate_retry(base_features):
    engine = DeterministicConstraintEngine()
    base_features.failure_reason = "Insufficient Funds"
    actions = ["Retry Immediately", "Retry Delay 18h", "Stop Intervention"]
    
    feasible, blocked, results, hard_block = engine.evaluate_constraints(base_features, actions)
    
    assert "Retry Immediately" not in feasible
    assert "Retry Delay 18h" in feasible
