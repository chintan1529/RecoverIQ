from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
import pandas as pd
import numpy as np

from app.core.database import get_db, engine, Base
from app.models.db_models import CustomerDB, PaymentDB, CustomerFatigueDB, DecisionContractDB, RecoveryOutcomeDB, AgentEventDB
from app.ml.generator import get_hero_pitch_scenarios, generate_synthetic_dataset, LatentSyntheticEnvironment
from app.schemas.pydantic_schemas import PreDecisionFeatures
from app.core.security import require_admin_auth
from app.api.payments import global_ml_model, global_optimizer, _contract_to_db

router = APIRouter(prefix="/demo", tags=["Demo Mode"])

@router.post("/seed")
def seed_demo_environment(
    db: Session = Depends(get_db),
    _auth: str = Depends(require_admin_auth)
):
    """
    Resets the database and seeds:
    1. 4 Seeded Hero Pitch Scenarios
    2. 45 Realistic Demo Failed Payments
    3. Evaluated Decision Contracts & Simulated Outcomes
    """
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Clear existing data
    db.query(RecoveryOutcomeDB).delete()
    db.query(DecisionContractDB).delete()
    db.query(AgentEventDB).delete()
    db.query(PaymentDB).delete()
    db.query(CustomerFatigueDB).delete()
    db.query(CustomerDB).delete()
    db.commit()

    # Train ML model on 2,000 synthetic records if not trained
    df_pre, df_post = generate_synthetic_dataset(n_samples=2000, seed=42)
    global_ml_model.train_and_evaluate(df_pre, df_post)

    # 1. Seed 4 Hero Pitch Scenarios
    hero_scenarios = get_hero_pitch_scenarios()
    env_sim = LatentSyntheticEnvironment(seed=42)

    for hero in hero_scenarios:
        # Create Customer
        cust = CustomerDB(
            customer_id=hero["customer_id"],
            name=hero["customer_name"],
            email=hero["customer_email"],
            tenure_months=hero["customer_tenure_months"],
            subscription_status="ACTIVE",
            segment=hero["customer_segment"],
            historical_recovery_rate=hero["historical_recovery_rate"],
            engagement_score=hero["engagement_score"],
            do_not_contact=hero["do_not_contact"],
            created_at=datetime.utcnow() - timedelta(days=30)
        )
        db.add(cust)

        # Create Fatigue Record
        fatigue = CustomerFatigueDB(
            customer_id=hero["customer_id"],
            contacts_24h=hero["contacts_24h"],
            contacts_7d=hero["contacts_7d"],
            failed_attempts=hero["consecutive_failures"],
            consecutive_failures=hero["consecutive_failures"],
            last_contact_timestamp=datetime.utcnow() - timedelta(hours=hero["hours_since_last_contact"]),
            fatigue_score=0.4 if hero["contacts_24h"] >= 1 else 0.1
        )
        db.add(fatigue)

        # Create Payment
        pay = PaymentDB(
            payment_id=hero["payment_id"],
            customer_id=hero["customer_id"],
            amount=hero["amount"],
            currency="INR",
            payment_method=hero["payment_method"],
            card_type="Visa" if hero["payment_method"] == "Card" else None,
            failure_reason=hero["failure_reason"],
            failure_code=hero["failure_code"],
            status="FAILED",
            created_at=datetime.utcnow() - timedelta(hours=2)
        )
        db.add(pay)

        # Evaluate Decision Contract
        pre_feat = PreDecisionFeatures(
            payment_id=hero["payment_id"],
            customer_id=hero["customer_id"],
            amount=hero["amount"],
            currency="INR",
            payment_method=hero["payment_method"],
            card_type="Visa" if hero["payment_method"] == "Card" else None,
            failure_reason=hero["failure_reason"],
            failure_code=hero["failure_code"],
            customer_tenure_months=hero["customer_tenure_months"],
            customer_segment=hero["customer_segment"],
            engagement_score=hero["engagement_score"],
            historical_recovery_rate=hero["historical_recovery_rate"],
            contacts_24h=hero["contacts_24h"],
            contacts_7d=hero["contacts_7d"],
            consecutive_failures=hero["consecutive_failures"],
            hours_since_last_contact=hero["hours_since_last_contact"],
            do_not_contact=hero["do_not_contact"]
        )

        contract = global_optimizer.optimize_and_decide(pre_feat)
        db.add(_contract_to_db(contract))

        # Log Agent Event — deterministic ID to prevent duplicates on re-seed
        db.add(AgentEventDB(
            event_id=f"evt_hero_{hero['scenario_id']}",
            payment_id=hero["payment_id"],
            stage="DECIDE",
            status="SUCCESS",
            message=f"Seeded Hero Scenario '{hero['name']}' -> Selected Action: {contract.selected_action} ({contract.decision_status})",
            metadata_json={"scenario_id": hero["scenario_id"], "decision_status": contract.decision_status}
        ))

    # 2. Seed 45 Additional Demo Payments (clean nan to None)
    df_clean = df_pre.replace({np.nan: None})
    sample_records = df_clean.iloc[:45].to_dict("records")
    for i, r in enumerate(sample_records):
        cid = f"CUST-DEMO-{i:03d}"
        pid = f"PAY-DEMO-{i:03d}"
        
        db.add(CustomerDB(
            customer_id=cid,
            name=f"Demo Merchant Customer {i+1}",
            email=f"customer{i+1}@example-merchant.in",
            tenure_months=r["customer_tenure_months"],
            segment=r["customer_segment"],
            historical_recovery_rate=r["historical_recovery_rate"],
            engagement_score=r["engagement_score"],
            do_not_contact=r["do_not_contact"]
        ))

        pay = PaymentDB(
            payment_id=pid,
            customer_id=cid,
            amount=r["amount"],
            currency="INR",
            payment_method=r["payment_method"],
            failure_reason=r["failure_reason"],
            failure_code=r["failure_code"],
            status="FAILED",
            created_at=datetime.utcnow() - timedelta(minutes=i * 45)
        )
        db.add(pay)

        # Evaluate decision contract
        r["payment_id"] = pid
        r["customer_id"] = cid
        if "card_type" not in r or r["card_type"] is None:
            r["card_type"] = None
        pre_f = PreDecisionFeatures(**r)
        c = global_optimizer.optimize_and_decide(pre_f)

        db.add(_contract_to_db(c))

        # Log Agent Event — deterministic ID
        db.add(AgentEventDB(
            event_id=f"evt_demo_{pid}",
            payment_id=pid,
            stage="DECIDE",
            status="SUCCESS",
            message=f"Evaluated {pid}: {c.selected_action} ({c.decision_status})",
            metadata_json={"decision_id": c.decision_id, "selected_action": c.selected_action}
        ))

        # Simulate 60% of cases having executed outcomes
        if i % 2 == 0 and c.decision_status in ["AUTO_EXECUTE", "RECOMMEND_FOR_APPROVAL"]:
            p_rec = env_sim.compute_ground_truth_p_recovery(r, c.selected_action)
            actual_out = env_sim.sample_actual_outcome(p_rec)
            rec_amt = pay.amount if actual_out == "SUCCESS" else 0.0
            
            db.add(RecoveryOutcomeDB(
                outcome_id=f"out_demo_{pid}",
                payment_id=pid,
                decision_id=c.decision_id,
                selected_action=c.selected_action,
                actual_outcome=actual_out,
                recovered_amount=rec_amt,
                actual_cost=c.intervention_cost + c.incentive_cost,
                time_to_recovery_hours=6.0
            ))
            pay.status = "RECOVERED" if actual_out == "SUCCESS" else "ABANDONED"

            db.add(AgentEventDB(
                event_id=f"evt_act_demo_{pid}",
                payment_id=pid,
                stage="ACT",
                status="SUCCESS",
                message=f"Simulated '{c.selected_action}' -> {actual_out}",
                metadata_json={"actual_outcome": actual_out, "recovered_amount": rec_amt}
            ))

    db.commit()
    return {"message": "Demo environment seeded successfully with 4 Hero Pitch Scenarios and 45 demo payments!"}
