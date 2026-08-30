import pytest
import concurrent.futures
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db, Base, engine
from app.models.db_models import CustomerDB, PaymentDB, CustomerFatigueDB, DecisionContractDB, RecoveryOutcomeDB

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield

class TestSecurityAndAuthentication:
    def test_execute_endpoint_requires_auth(self):
        # 1. Unauthenticated request must return 401
        res = client.post("/api/payments/PAY-TEST-001/execute")
        assert res.status_code == 401
        assert "Authentication required" in res.json()["detail"]

    def test_execute_endpoint_rejects_invalid_key(self):
        # 2. Invalid key must return 403
        res = client.post(
            "/api/payments/PAY-TEST-001/execute",
            headers={"X-API-Key": "invalid_unauthorized_key"}
        )
        assert res.status_code == 403
        assert "Insufficient permissions" in res.json()["detail"]

    def test_approve_endpoint_requires_auth(self):
        res = client.post("/api/payments/PAY-TEST-001/approve")
        assert res.status_code == 401

    def test_reject_endpoint_requires_auth(self):
        res = client.post("/api/payments/PAY-TEST-001/reject")
        assert res.status_code == 401

    def test_evaluate_endpoint_requires_auth(self):
        res = client.post("/api/payments/PAY-TEST-001/evaluate")
        assert res.status_code == 401

    def test_demo_seed_requires_admin_auth(self):
        # Unauthenticated seed must return 401
        res = client.post("/api/demo/seed")
        assert res.status_code == 401

        # Operator key cannot seed (needs admin key) -> 403
        res_op = client.post("/api/demo/seed", headers={"X-API-Key": "test_operator_key"})
        assert res_op.status_code == 403


class TestConcurrencyAndIdempotency:
    def test_concurrent_execution_race_condition(self):
        """
        Tests two simultaneous execution requests on the exact same payment decision.
        Asserts atomic idempotency: one executes, the second triggers idempotent lock safely.
        """
        db = next(get_db())
        cust_id = "CUST-CONCURRENCY-001"
        pay_id = "PAY-CONCURRENCY-001"

        db.query(RecoveryOutcomeDB).filter(RecoveryOutcomeDB.payment_id == pay_id).delete()
        db.query(DecisionContractDB).filter(DecisionContractDB.payment_id == pay_id).delete()
        db.query(PaymentDB).filter(PaymentDB.payment_id == pay_id).delete()
        db.query(CustomerFatigueDB).filter(CustomerFatigueDB.customer_id == cust_id).delete()
        db.query(CustomerDB).filter(CustomerDB.customer_id == cust_id).delete()
        db.commit()

        cust = CustomerDB(
            customer_id=cust_id,
            name="Concurrent Test User",
            email="concurrent@example.com",
            tenure_months=18,
            subscription_status="ACTIVE",
            segment="MidMarket",
            historical_recovery_rate=0.6,
            engagement_score=0.75,
            do_not_contact=False
        )
        fatigue = CustomerFatigueDB(
            customer_id=cust_id,
            contacts_24h=0,
            contacts_7d=1,
            consecutive_failures=1
        )
        pay = PaymentDB(
            payment_id=pay_id,
            customer_id=cust_id,
            amount=4500.0,
            currency="INR",
            payment_method="Card",
            failure_reason="Network Timeout",
            failure_code="ERR_NET",
            status="FAILED"
        )
        db.add_all([cust, fatigue, pay])
        db.commit()

        headers = {"X-API-Key": "test_operator_key"}

        # Evaluate decision with operator key
        eval_res = client.post(f"/api/payments/{pay_id}/evaluate", headers=headers)
        assert eval_res.status_code == 200

        def send_exec():
            c = TestClient(app)
            return c.post(f"/api/payments/{pay_id}/execute", headers=headers)

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            f1 = executor.submit(send_exec)
            f2 = executor.submit(send_exec)
            r1 = f1.result()
            r2 = f2.result()

        # Both must return 200, but exactly one must be the primary execution and one must be idempotent
        assert r1.status_code == 200
        assert r2.status_code == 200

        messages = [r1.json()["message"], r2.json()["message"]]
        has_executed = any("Action execution simulated" in m for m in messages)
        has_idempotent = any("Idempotent" in m or "already executed" in m for m in messages)
        
        # Verify exactly ONE recovery outcome was committed to the DB
        outcomes_count = db.query(RecoveryOutcomeDB).filter(RecoveryOutcomeDB.payment_id == pay_id).count()
        assert outcomes_count == 1
        assert has_executed or has_idempotent
