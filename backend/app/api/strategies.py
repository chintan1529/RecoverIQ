from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.db_models import DecisionContractDB, RecoveryOutcomeDB
from app.ml.generator import ACTIONS

router = APIRouter(prefix="/strategies", tags=["Strategies"])

# Segment mapping for display
SEGMENT_MAP = {
    "Retry Delay 18h": "Insufficient Funds (SMB & MidMarket)",
    "Payment Method Update": "Expired Card (All Segments)",
    "WhatsApp Nudge": "Authentication Failed (MidMarket)",
    "Retry Immediately": "Network Timeout / Bank Downtime",
    "Personalized Email": "General Failed AutoPay",
    "Human Escalation": "High-Value Enterprise (>₹50,000)",
    "Incentive Offer": "High-Churn Risk Customers",
    "Retry Delay 6h": "Bank Downtime / Transient Failures",
    "Stop Intervention": "High Fatigue / Negative Net Value"
}

@router.get("")
def get_strategy_performance(db: Session = Depends(get_db)):
    """
    Returns strategy ROI and conversion performance metrics computed from actual DB data.
    """
    results = []

    for action in ACTIONS:
        # Count decisions that selected this action
        attempts = db.query(DecisionContractDB).filter(
            DecisionContractDB.selected_action == action
        ).count()

        if attempts == 0:
            results.append({
                "action": action,
                "attempts": 0,
                "recovery_rate_pct": 0.0,
                "recovered_revenue": 0.0,
                "avg_cost_per_recovery": 0.0,
                "roi": 0.0,
                "best_segment": SEGMENT_MAP.get(action, "—")
            })
            continue

        # Count successful outcomes for this action
        successes = db.query(RecoveryOutcomeDB).filter(
            RecoveryOutcomeDB.selected_action == action,
            RecoveryOutcomeDB.actual_outcome == "SUCCESS"
        ).count()

        total_outcomes = db.query(RecoveryOutcomeDB).filter(
            RecoveryOutcomeDB.selected_action == action
        ).count()

        recovered_rev = db.query(func.sum(RecoveryOutcomeDB.recovered_amount)).filter(
            RecoveryOutcomeDB.selected_action == action,
            RecoveryOutcomeDB.actual_outcome == "SUCCESS"
        ).scalar() or 0.0

        total_cost = db.query(func.sum(RecoveryOutcomeDB.actual_cost)).filter(
            RecoveryOutcomeDB.selected_action == action
        ).scalar() or 0.0

        recovery_rate = round((successes / total_outcomes) * 100, 1) if total_outcomes > 0 else 0.0
        avg_cost = round(total_cost / successes, 2) if successes > 0 else 0.0
        roi_val = round(recovered_rev / total_cost, 1) if total_cost > 0 else 0.0

        results.append({
            "action": action,
            "attempts": attempts,
            "recovery_rate_pct": recovery_rate,
            "recovered_revenue": round(recovered_rev, 2),
            "avg_cost_per_recovery": avg_cost,
            "roi": roi_val,
            "best_segment": SEGMENT_MAP.get(action, "—")
        })

    # Sort by recovered revenue descending
    results.sort(key=lambda x: x["recovered_revenue"], reverse=True)
    return results
