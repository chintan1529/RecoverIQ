import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime


from app.core.database import get_db
from app.models.db_models import PaymentDB, CustomerDB, DecisionContractDB, RecoveryOutcomeDB, AgentEventDB, CustomerFatigueDB
from app.schemas.pydantic_schemas import PaymentResponse, DecisionContract, PreDecisionFeatures, CandidateActionScore, BlockedAction, GuardrailResult, Explanation
from app.ml.models import RecoveryPredictorModel
from app.decision_engine.optimizer import DecisionOptimizerEngine
from app.ml.generator import LatentSyntheticEnvironment
from app.core.security import require_operator_auth, mask_name, mask_email
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/payments", tags=["Payments"])

# Singleton model instance for fast in-memory scoring
global_ml_model = RecoveryPredictorModel()
global_optimizer = DecisionOptimizerEngine(global_ml_model)


def _db_dec_to_contract(latest_dec) -> DecisionContract:
    """Convert a DecisionContractDB row into a pydantic DecisionContract."""
    # Reconstruct candidate_scores from JSON if available
    cs_list = []
    if latest_dec.candidate_scores_json:
        for cs in latest_dec.candidate_scores_json:
            cs_list.append(CandidateActionScore(**cs))

    # Reconstruct blocked_actions
    blocked_list = []
    if latest_dec.blocked_actions_json:
        for b in latest_dec.blocked_actions_json:
            blocked_list.append(BlockedAction(**b))

    # Reconstruct guardrail_results
    gr_list = []
    if latest_dec.guardrail_results_json:
        for g in latest_dec.guardrail_results_json:
            gr_list.append(GuardrailResult(**g))

    # Reconstruct explanation
    explanation = latest_dec.explanation_json
    if isinstance(explanation, dict):
        explanation = Explanation(**explanation)

    return DecisionContract(
        decision_id=latest_dec.decision_id,
        payment_id=latest_dec.payment_id,
        timestamp=latest_dec.timestamp,
        model_version=latest_dec.model_version,
        policy_version=latest_dec.policy_version,
        feature_snapshot=latest_dec.feature_snapshot_json,
        candidate_actions=latest_dec.candidate_actions_json,
        feasible_actions=latest_dec.feasible_actions_json,
        blocked_actions=blocked_list,
        candidate_scores=cs_list,
        predicted_recovery_probability=latest_dec.predicted_recovery_probability,
        expected_recovered_amount=latest_dec.expected_recovered_amount,
        intervention_cost=latest_dec.intervention_cost,
        incentive_cost=latest_dec.incentive_cost,
        fatigue_penalty=latest_dec.fatigue_penalty,
        risk_penalty=latest_dec.risk_penalty,
        expected_net_value=latest_dec.expected_net_value,
        selected_action=latest_dec.selected_action,
        decision_status=latest_dec.decision_status,
        approval_required=latest_dec.approval_required,
        guardrail_results=gr_list,
        explanation=explanation,
        execution_status=latest_dec.execution_status
    )


def _contract_to_db(contract: DecisionContract) -> DecisionContractDB:
    """Convert a pydantic DecisionContract into a DecisionContractDB row."""
    return DecisionContractDB(
        decision_id=contract.decision_id,
        payment_id=contract.payment_id,
        timestamp=contract.timestamp,
        model_version=contract.model_version,
        policy_version=contract.policy_version,
        feature_snapshot_json=contract.feature_snapshot,
        candidate_actions_json=contract.candidate_actions,
        feasible_actions_json=contract.feasible_actions,
        blocked_actions_json=[b.model_dump() for b in contract.blocked_actions],
        candidate_scores_json=[s.model_dump() for s in contract.candidate_scores],
        predicted_recovery_probability=contract.predicted_recovery_probability,
        expected_recovered_amount=contract.expected_recovered_amount,
        intervention_cost=contract.intervention_cost,
        incentive_cost=contract.incentive_cost,
        fatigue_penalty=contract.fatigue_penalty,
        risk_penalty=contract.risk_penalty,
        expected_net_value=contract.expected_net_value,
        selected_action=contract.selected_action,
        decision_status=contract.decision_status,
        approval_required=contract.approval_required,
        guardrail_results_json=[g.model_dump() for g in contract.guardrail_results],
        explanation_json=contract.explanation.model_dump(),
        execution_status=contract.execution_status
    )


@router.post("/what-if")
def simulate_what_if_scenario(features: PreDecisionFeatures):
    """
    Real-Time What-If Counterfactual Simulator:
    Allows interactive exploration of recovery probabilities, Expected Net Values,
    multi-tier guardrail outcomes, and SHAP-style local feature attributions in real time.
    """
    if not global_ml_model.is_trained:
        from app.ml.generator import generate_synthetic_dataset
        df_pre, df_post = generate_synthetic_dataset(n_samples=2000, seed=42)
        global_ml_model.train_and_evaluate(df_pre, df_post)

    contract = global_optimizer.optimize_and_decide(features)
    attributions = global_ml_model.get_feature_attributions(features.model_dump(), contract.selected_action)

    return {
        "contract": contract,
        "attributions": attributions,
        "is_what_if": True,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/{payment_id}/attributions")
def get_payment_attributions(payment_id: str, db: Session = Depends(get_db)):
    """
    Returns SHAP-style local feature attributions for an existing payment's decision.
    """
    latest_dec = db.query(DecisionContractDB).filter(DecisionContractDB.payment_id == payment_id).order_by(DecisionContractDB.timestamp.desc()).first()
    if not latest_dec:
        raise HTTPException(status_code=404, detail="Decision not found for payment")

    contract = _db_dec_to_contract(latest_dec)
    feats = contract.feature_snapshot
    attributions = global_ml_model.get_feature_attributions(feats, contract.selected_action)
    return attributions


@router.get("", response_model=List[PaymentResponse])
def get_payments(
    status: Optional[str] = None,
    failure_reason: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(PaymentDB)
    if status:
        query = query.filter(PaymentDB.status == status)
    if failure_reason:
        query = query.filter(PaymentDB.failure_reason == failure_reason)
    
    payments = query.order_by(PaymentDB.created_at.desc()).limit(limit).all()
    
    res = []
    for p in payments:
        cust = db.query(CustomerDB).filter(CustomerDB.customer_id == p.customer_id).first()
        latest_dec = db.query(DecisionContractDB).filter(DecisionContractDB.payment_id == p.payment_id).order_by(DecisionContractDB.timestamp.desc()).first()
        latest_out = db.query(RecoveryOutcomeDB).filter(RecoveryOutcomeDB.payment_id == p.payment_id).order_by(RecoveryOutcomeDB.recorded_at.desc()).first()
        
        dec_contract = _db_dec_to_contract(latest_dec) if latest_dec else None

        out_dict = None
        if latest_out:
            out_dict = {
                "outcome_id": latest_out.outcome_id,
                "selected_action": latest_out.selected_action,
                "actual_outcome": latest_out.actual_outcome,
                "recovered_amount": latest_out.recovered_amount,
                "actual_cost": latest_out.actual_cost,
                "recorded_at": latest_out.recorded_at.isoformat()
            }

        res.append(PaymentResponse(
            payment_id=p.payment_id,
            customer_id=p.customer_id,
            customer_name=cust.name if cust else "Unknown Customer",
            customer_email=cust.email if cust else "unknown@example.com",
            amount=p.amount,
            currency=p.currency,
            payment_method=p.payment_method,
            failure_reason=p.failure_reason,
            failure_code=p.failure_code,
            status=p.status,
            created_at=p.created_at,
            latest_decision=dec_contract,
            latest_outcome=out_dict
        ))
    return res

@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment_detail(payment_id: str, db: Session = Depends(get_db)):
    p = db.query(PaymentDB).filter(PaymentDB.payment_id == payment_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    cust = db.query(CustomerDB).filter(CustomerDB.customer_id == p.customer_id).first()
    latest_dec = db.query(DecisionContractDB).filter(DecisionContractDB.payment_id == p.payment_id).order_by(DecisionContractDB.timestamp.desc()).first()
    latest_out = db.query(RecoveryOutcomeDB).filter(RecoveryOutcomeDB.payment_id == p.payment_id).order_by(RecoveryOutcomeDB.recorded_at.desc()).first()

    dec_contract = _db_dec_to_contract(latest_dec) if latest_dec else None

    out_dict = None
    if latest_out:
        out_dict = {
            "outcome_id": latest_out.outcome_id,
            "selected_action": latest_out.selected_action,
            "actual_outcome": latest_out.actual_outcome,
            "recovered_amount": latest_out.recovered_amount,
            "actual_cost": latest_out.actual_cost,
            "recorded_at": latest_out.recorded_at.isoformat()
        }

    return PaymentResponse(
        payment_id=p.payment_id,
        customer_id=p.customer_id,
        customer_name=cust.name if cust else "Unknown Customer",
        customer_email=cust.email if cust else "unknown@example.com",
        amount=p.amount,
        currency=p.currency,
        payment_method=p.payment_method,
        failure_reason=p.failure_reason,
        failure_code=p.failure_code,
        status=p.status,
        created_at=p.created_at,
        latest_decision=dec_contract,
        latest_outcome=out_dict
    )

@router.post("/{payment_id}/evaluate", response_model=DecisionContract)
def evaluate_payment_decision(
    payment_id: str, 
    db: Session = Depends(get_db),
    _auth: str = Depends(require_operator_auth)
):
    p = db.query(PaymentDB).filter(PaymentDB.payment_id == payment_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Payment not found")
    cust = db.query(CustomerDB).filter(CustomerDB.customer_id == p.customer_id).first()
    fatigue = db.query(CustomerFatigueDB).filter(CustomerFatigueDB.customer_id == p.customer_id).first()

    # Compute hours since last contact if timestamp is available
    hrs_since_contact = 24.0
    if fatigue and fatigue.last_contact_timestamp:
        hrs_since_contact = max(0.5, round((datetime.utcnow() - fatigue.last_contact_timestamp).total_seconds() / 3600.0, 1))

    features = PreDecisionFeatures(
        payment_id=p.payment_id,
        customer_id=p.customer_id,
        amount=p.amount,
        currency=p.currency,
        payment_method=p.payment_method,
        card_type=p.card_type,
        failure_reason=p.failure_reason,
        failure_code=p.failure_code,
        customer_tenure_months=cust.tenure_months if cust else 12,
        customer_segment=cust.segment if cust else "MidMarket",
        engagement_score=cust.engagement_score if cust else 0.70,
        historical_recovery_rate=cust.historical_recovery_rate if cust else 0.50,
        contacts_24h=fatigue.contacts_24h if fatigue else 0,
        contacts_7d=fatigue.contacts_7d if fatigue else 1,
        consecutive_failures=fatigue.consecutive_failures if fatigue else 1,
        hours_since_last_contact=hrs_since_contact,
        do_not_contact=cust.do_not_contact if cust else False
    )

    contract = global_optimizer.optimize_and_decide(features)

    # Save decision contract to database
    db_dec = _contract_to_db(contract)
    db.add(db_dec)

    # Log Agent Event
    db.add(AgentEventDB(
        event_id=f"evt_{uuid.uuid4().hex[:8]}",
        payment_id=payment_id,
        stage="DECIDE",
        status="SUCCESS",
        message=f"Evaluated decision for {payment_id}: {contract.selected_action} ({contract.decision_status})",
        metadata_json={"decision_id": contract.decision_id, "selected_action": contract.selected_action}
    ))

    db.commit()
    return contract

@router.post("/{payment_id}/execute")
def execute_payment_simulation(
    payment_id: str, 
    db: Session = Depends(get_db),
    _auth: str = Depends(require_operator_auth)
):
    p = db.query(PaymentDB).filter(PaymentDB.payment_id == payment_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    dec = db.query(DecisionContractDB).filter(DecisionContractDB.payment_id == payment_id).order_by(DecisionContractDB.timestamp.desc()).first()
    if not dec:
        raise HTTPException(status_code=400, detail="Must evaluate payment decision before execution")
    
    # 1. State Guard: Prevent executing a REJECTED decision
    if dec.execution_status == "REJECTED":
        raise HTTPException(status_code=400, detail="Cannot execute a REJECTED decision")

    # 2. State Guard: Prevent executing a BLOCKED decision
    if dec.decision_status == "BLOCK":
        dec.execution_status = "NOT_EXECUTED"
        db.commit()
        return {"message": "Payment decision is BLOCKED. Action execution terminated without outreach.", "status": "NOT_EXECUTED"}

    # 3. State Guard: Prevent executing unapproved high-value recommendations
    if dec.decision_status == "RECOMMEND_FOR_APPROVAL" and dec.execution_status != "APPROVED":
        raise HTTPException(status_code=400, detail="Action requires human operator approval before execution")

    # 4. Duplicate Guard: Check if this decision was already executed
    existing_outcome = db.query(RecoveryOutcomeDB).filter(RecoveryOutcomeDB.decision_id == dec.decision_id).first()
    if existing_outcome or dec.execution_status == "EXECUTED":
        return {
            "message": "Payment decision was already executed (Idempotent call).",
            "actual_outcome": existing_outcome.actual_outcome if existing_outcome else "ALREADY_EXECUTED",
            "recovered_amount": existing_outcome.recovered_amount if existing_outcome else 0.0
        }

    # Fetch genuine customer and fatigue profile from DB (No hardcoding)
    cust = db.query(CustomerDB).filter(CustomerDB.customer_id == p.customer_id).first()
    fatigue = db.query(CustomerFatigueDB).filter(CustomerFatigueDB.customer_id == p.customer_id).first()

    customer_dict = {
        "amount": p.amount,
        "customer_tenure_months": cust.tenure_months if cust else 12,
        "engagement_score": cust.engagement_score if cust else 0.65,
        "customer_segment": cust.segment if cust else "MidMarket",
        "historical_recovery_rate": cust.historical_recovery_rate if cust else 0.50,
        "payment_method": p.payment_method,
        "failure_reason": p.failure_reason,
        "contacts_24h": fatigue.contacts_24h if fatigue else 0,
        "contacts_7d": fatigue.contacts_7d if fatigue else 1,
        "consecutive_failures": fatigue.consecutive_failures if fatigue else 1,
        "do_not_contact": cust.do_not_contact if cust else False
    }

    # Simulate realistic outcome using true customer features
    env = LatentSyntheticEnvironment()
    actual_p = env.compute_ground_truth_p_recovery(customer_dict, dec.selected_action)

    actual_outcome = env.sample_actual_outcome(actual_p)
    recovered_amount = p.amount if actual_outcome == "SUCCESS" else 0.0
    actual_cost = float(dec.intervention_cost + dec.incentive_cost)

    try:
        outcome_record = RecoveryOutcomeDB(
            outcome_id=f"out_{dec.decision_id}",
            decision_id=dec.decision_id,
            payment_id=payment_id,
            selected_action=dec.selected_action,
            actual_outcome=actual_outcome,
            recovered_amount=recovered_amount,
            actual_cost=actual_cost,
            time_to_recovery_hours=2.5 if actual_outcome == "SUCCESS" else 0.0
        )
        db.add(outcome_record)

        # Update states
        dec.execution_status = "EXECUTED"
        p.status = "RECOVERED" if actual_outcome == "SUCCESS" else "FAILED"

        # Log Execution Event with masked customer reference
        db.add(AgentEventDB(
            event_id=f"evt_exec_{uuid.uuid4().hex[:8]}",
            payment_id=payment_id,
            stage="EXECUTE",
            status="SUCCESS" if actual_outcome == "SUCCESS" else "WARN",
            message=f"Executed {dec.selected_action} for payment {payment_id}. Outcome: {actual_outcome}",
            metadata_json={"outcome": actual_outcome, "recovered_amount": recovered_amount}
        ))

        db.commit()
        return {"message": f"Action execution simulated. Outcome: {actual_outcome}", "actual_outcome": actual_outcome, "recovered_amount": recovered_amount}
    except IntegrityError:
        # Atomic rollback for concurrent execution attempts
        db.rollback()
        existing_outcome = db.query(RecoveryOutcomeDB).filter(RecoveryOutcomeDB.decision_id == dec.decision_id).first()
        return {
            "message": "Payment decision was already executed concurrently (Idempotent lock triggered).",
            "actual_outcome": existing_outcome.actual_outcome if existing_outcome else "ALREADY_EXECUTED",
            "recovered_amount": existing_outcome.recovered_amount if existing_outcome else 0.0
        }

@router.post("/{payment_id}/approve")
def approve_payment_decision(
    payment_id: str, 
    db: Session = Depends(get_db),
    _auth: str = Depends(require_operator_auth)
):
    dec = db.query(DecisionContractDB).filter(DecisionContractDB.payment_id == payment_id).order_by(DecisionContractDB.timestamp.desc()).first()
    if not dec:
        raise HTTPException(status_code=404, detail="Decision contract not found")
    
    if dec.execution_status == "EXECUTED":
        raise HTTPException(status_code=400, detail="Cannot approve an already executed decision")
    
    if dec.execution_status == "REJECTED":
        raise HTTPException(status_code=400, detail="Cannot approve a rejected decision")
        
    if dec.execution_status == "APPROVED":
        return {"message": f"Decision already approved for payment {payment_id}", "status": "APPROVED"}
    
    dec.execution_status = "APPROVED"
    db.add(AgentEventDB(
        event_id=f"evt_appr_{uuid.uuid4().hex[:8]}",
        payment_id=payment_id,
        stage="APPROVE",
        status="SUCCESS",
        message=f"Operator approved decision for payment {payment_id}",
        metadata_json={"approved_action": dec.selected_action}
    ))
    db.commit()
    return {"message": f"Decision approved for payment {payment_id}", "status": "APPROVED"}

@router.post("/{payment_id}/reject")
def reject_payment_decision(
    payment_id: str, 
    db: Session = Depends(get_db),
    _auth: str = Depends(require_operator_auth)
):
    dec = db.query(DecisionContractDB).filter(DecisionContractDB.payment_id == payment_id).order_by(DecisionContractDB.timestamp.desc()).first()
    if not dec:
        raise HTTPException(status_code=404, detail="Decision contract not found")
    
    if dec.execution_status == "EXECUTED":
        raise HTTPException(status_code=400, detail="Cannot reject an already executed decision")

    if dec.execution_status == "REJECTED":
        return {"message": f"Decision already rejected for payment {payment_id}", "status": "REJECTED"}

    dec.execution_status = "REJECTED"
    p = db.query(PaymentDB).filter(PaymentDB.payment_id == payment_id).first()
    if p:
        p.status = "REJECTED"

    db.add(AgentEventDB(
        event_id=f"evt_rej_{uuid.uuid4().hex[:8]}",
        payment_id=payment_id,
        stage="APPROVE",
        status="WARN",
        message=f"Operator rejected recommendation for payment {payment_id}. Outreach stopped.",
        metadata_json={"rejected_action": dec.selected_action}
    ))
    db.commit()
    return {"message": f"Decision rejected for payment {payment_id}. Action cancelled.", "status": "REJECTED"}
