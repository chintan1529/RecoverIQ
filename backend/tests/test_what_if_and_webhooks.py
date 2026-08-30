import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.db_models import PaymentDB, CustomerDB, DecisionContractDB, AgentEventDB

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_db():
    db = SessionLocal()
    try:
        db.query(AgentEventDB).delete()
        db.query(DecisionContractDB).delete()
        db.query(PaymentDB).delete()
        db.query(CustomerDB).delete()
        db.commit()
    finally:
        db.close()


def test_what_if_endpoint_returns_calibrated_decision_and_attributions():
    payload = {
        "payment_id": "TEST_WHAT_IF_001",
        "customer_id": "CUST_001",
        "amount": 12500.0,
        "payment_method": "CreditCard",
        "failure_reason": "Network Timeout",
        "failure_code": "GATEWAY_TIMEOUT",
        "customer_tier": "Gold",
        "historical_recovery_rate": 0.65,
        "propensity_score": 0.75,
        "contact_count_24h": 0,
        "contact_count_7d": 1,
        "consecutive_failures": 1,
        "do_not_contact": False
    }

    res = client.post("/api/payments/what-if", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["is_what_if"] is True
    assert "contract" in data
    assert "attributions" in data

    contract = data["contract"]
    assert contract["selected_action"] in contract["feasible_actions"]
    assert 0.0 < contract["predicted_recovery_probability"] <= 1.0
    assert contract["expected_net_value"] >= -100.0
    assert contract["decision_status"] in ["AUTO_EXECUTE", "RECOMMEND_FOR_APPROVAL", "BLOCK"]

    attributions = data["attributions"]
    assert "base_probability" in attributions
    assert "predicted_probability" in attributions
    assert "attributions" in attributions
    assert len(attributions["attributions"]) >= 1


def test_what_if_dnc_hard_blocks():
    payload = {
        "amount": 5000.0,
        "payment_method": "CreditCard",
        "failure_reason": "Network Timeout",
        "customer_tier": "Gold",
        "propensity_score": 0.80,
        "contact_count_24h": 0,
        "consecutive_failures": 1,
        "do_not_contact": True  # Tier 1 Hard Block
    }

    res = client.post("/api/payments/what-if", json=payload)
    assert res.status_code == 200
    data = res.json()
    contract = data["contract"]

    assert contract["selected_action"] == "Stop Intervention"
    assert contract["decision_status"] == "BLOCK"
    assert contract["expected_net_value"] == 0.0
    assert 0.0 <= contract["predicted_recovery_probability"] <= 1.0


def test_what_if_high_value_escalates_to_approval():
    payload = {
        "amount": 75000.0,  # >= ₹50,000 threshold
        "payment_method": "CreditCard",
        "failure_reason": "Network Timeout",
        "customer_tier": "Gold",
        "propensity_score": 0.85,
        "contact_count_24h": 0,
        "consecutive_failures": 1,
        "do_not_contact": False
    }

    res = client.post("/api/payments/what-if", json=payload)
    assert res.status_code == 200
    data = res.json()
    contract = data["contract"]

    assert contract["decision_status"] == "RECOMMEND_FOR_APPROVAL"
    assert contract["approval_required"] is True


def test_what_if_expired_card_prevents_retry():
    payload = {
        "amount": 8000.0,
        "payment_method": "CreditCard",
        "failure_reason": "Expired Card",
        "customer_tier": "Silver",
        "propensity_score": 0.50,
        "contact_count_24h": 0,
        "consecutive_failures": 1,
        "do_not_contact": False
    }

    res = client.post("/api/payments/what-if", json=payload)
    assert res.status_code == 200
    data = res.json()
    contract = data["contract"]

    assert contract["selected_action"] == "Payment Method Update"
    assert "Retry Immediately" not in contract["feasible_actions"]


def test_razorpay_webhook_samples_catalog():
    res = client.get("/api/webhooks/samples")
    assert res.status_code == 200
    catalog = res.json()

    assert "payment.failed.insufficient_funds" in catalog
    assert "payment.failed.expired_card" in catalog
    assert "payment.failed.high_value_auth" in catalog
    assert "payment.failed.dnc_customer" in catalog
    assert "subscription.halted.recurring_card" in catalog


def test_razorpay_webhook_ingestion_executes_autonomous_decision():
    # Ingest Insufficient Funds Webhook
    sample_payload = {
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_rzp_auto_01",
                    "amount": 450000,  # 4,500 INR in paise
                    "currency": "INR",
                    "method": "card",
                    "error_code": "BAD_REQUEST_ERROR",
                    "error_description": "Payment failed due to insufficient funds in customer bank account",
                    "error_reason": "payment_failed_insufficient_funds",
                    "email": "priya.verma@enterprise.in",
                    "contact": "+919876543210"
                }
            }
        }
    }

    res = client.post("/api/webhooks/razorpay", json=sample_payload)
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "success"
    assert data["payment_id"] == "pay_test_rzp_auto_01"
    assert data["amount_inr"] == 4500.0
    assert data["failure_reason"] == "Insufficient Funds"
    assert data["selected_action"] == "Retry Delay 18h"
    assert data["execution_latency_ms"] < 3000.0  # Allow test runner initial model warmup and SQLite overhead
    assert data["decision_status"] == "AUTO_EXECUTE"




def test_razorpay_webhook_expired_card_dispatches_method_update_link():
    sample_payload = {
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_rzp_exp_02",
                    "amount": 1200000,  # 12,000 INR
                    "currency": "INR",
                    "method": "card",
                    "error_code": "BAD_REQUEST_ERROR",
                    "error_description": "Card has expired",
                    "error_reason": "card_expired",
                    "email": "customer.card@tech.org",
                    "contact": "+919811223344"
                }
            }
        }
    }

    res = client.post("/api/webhooks/razorpay", json=sample_payload)
    assert res.status_code == 200
    data = res.json()

    assert data["selected_action"] == "Payment Method Update"
    assert data["razorpay_payment_link"] is not None
    assert "rzp.io/i/rec_" in data["razorpay_payment_link"]


def test_model_calibration_endpoint():
    res = client.get("/api/analytics/calibration")
    assert res.status_code == 200
    data = res.json()

    assert "bins" in data
    assert len(data["bins"]) == 10
    assert "ece" in data
    assert data["ece"] < 0.10
    assert "brier_score" in data
    assert "roc_auc" in data
    assert "top_features" in data
    assert len(data["top_features"]) >= 5


def test_enterprise_roi_calculator_math_consistency():
    res = client.get("/api/analytics/roi-calculator?monthly_gmv=50000000&failure_rate_pct=12&aov=2500&margin_pct=2.0")
    assert res.status_code == 200
    data = res.json()

    impact = data["financial_impact"]
    assert impact["annual_incremental_gmv"] > 0
    assert impact["roi_multiplier"] >= 1.0
    assert impact["payback_period_days"] <= 365.0


def test_razorpay_webhook_replay_idempotency():
    sample_payload = {
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_rzp_idempotent_99",
                    "amount": 250000,
                    "currency": "INR",
                    "method": "card",
                    "error_code": "BAD_REQUEST_ERROR",
                    "error_description": "Network timeout during authorization",
                    "error_reason": "gateway_timeout",
                    "email": "idempotent.test@merchant.in",
                    "contact": "+919988776655"
                }
            }
        }
    }

    # First delivery
    res1 = client.post("/api/webhooks/razorpay", json=sample_payload)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["status"] == "success"
    assert data1.get("is_idempotent_replay") is not True

    # Replay delivery (simulating network retry from Razorpay)
    res2 = client.post("/api/webhooks/razorpay", json=sample_payload)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["status"] == "success"
    assert data2.get("is_idempotent_replay") is True
    assert data2["selected_action"] == data1["selected_action"]
    assert data2["expected_net_value"] == data1["expected_net_value"]


def test_health_ready_endpoint():
    res = client.get("/api/health/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["ready", "initializing"]
    assert "model_version" in data
    assert "policy_version" in data

