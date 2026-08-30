from typing import Dict, Any
from app.schemas.pydantic_schemas import CandidateActionScore
from app.core.config import settings
from app.decision_engine.fatigue import compute_action_fatigue_penalty

def evaluate_action_expected_net_value(
    action: str,
    amount: float,
    predicted_p_recovery: float,
    contacts_24h: int,
    contacts_7d: int
) -> CandidateActionScore:
    """
    Computes Expected Net Value (ENV) for a single candidate action.
    ENV = P(recovery | context, action) * Amount - InterventionCost - IncentiveCost - FatiguePenalty - RiskPenalty
    """
    base_cost = settings.COST_MATRIX.get(action, 0.00)

    # Dynamic incentive cost calculation (3% of transaction amount, capped at ₹500)
    incentive_cost = 0.00
    if action == "Incentive Offer":
        incentive_cost = min(amount * settings.INCENTIVE_MAX_PCT, settings.INCENTIVE_MAX_AMOUNT)

    # Action-specific fatigue penalty
    fatigue_penalty = compute_action_fatigue_penalty(action, contacts_24h, contacts_7d)

    # Risk penalty
    risk_penalty = 0.00
    if action == "Retry Immediately" and amount > 25000.0:
        risk_penalty = 5.00  # Gateway penalty risk for large retries
    elif action == "Human Escalation":
        risk_penalty = 10.00

    if action == "Stop Intervention":
        base_cost = 0.00
        incentive_cost = 0.00
        fatigue_penalty = 0.00
        risk_penalty = 0.00
        expected_recovered = 0.00
        env = 0.00
    else:
        expected_recovered = predicted_p_recovery * amount
        total_costs = base_cost + incentive_cost + fatigue_penalty + risk_penalty
        env = expected_recovered - total_costs

    return CandidateActionScore(
        action=action,
        predicted_p_recovery=predicted_p_recovery,
        expected_recovered_amount=round(expected_recovered, 2),
        intervention_cost=round(base_cost, 2),
        incentive_cost=round(incentive_cost, 2),
        fatigue_penalty=round(fatigue_penalty, 2),
        risk_penalty=round(risk_penalty, 2),
        expected_net_value=round(env, 2),
        is_blocked=False,
        block_reason=None
    )
