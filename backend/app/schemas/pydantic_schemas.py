import uuid
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class PreDecisionFeatures(BaseModel):
    """
    Strict Pre-Decision Features schema.
    Contains ONLY features available before a decision is made.
    POST-ACTION OUTCOMES ARE STRICTLY FORBIDDEN HERE.
    """
    payment_id: str = Field(default_factory=lambda: f"PAY-SIM-{uuid.uuid4().hex[:8]}")
    customer_id: str = Field(default_factory=lambda: f"CUST-SIM-{uuid.uuid4().hex[:8]}")
    amount: float
    currency: str = "INR"
    payment_method: str  # UPI, Card, NetBanking, AutoPay
    card_type: Optional[str] = None
    failure_reason: str  # Insufficient Funds, Expired Card, Network Timeout, Authentication Failed, Bank Downtime
    failure_code: str = "FAIL_GENERIC"
    customer_tenure_months: int = 12
    customer_segment: str = "MidMarket"
    engagement_score: float = 0.65
    historical_recovery_rate: float = 0.50
    contacts_24h: int = 0
    contacts_7d: int = 1
    consecutive_failures: int = 1
    hours_since_last_contact: float = 24.0
    do_not_contact: bool = False
    candidate_action: Optional[str] = None

class PostActionOutcome(BaseModel):
    """
    Post-Action Outcome schema.
    Recorded ONLY after an action is simulated or executed.
    """
    outcome_id: str
    payment_id: str
    decision_id: str
    selected_action: str
    actual_outcome: str  # SUCCESS, FAILED
    recovered_amount: float
    actual_cost: float
    time_to_recovery_hours: float
    recorded_at: datetime

class CandidateActionScore(BaseModel):
    action: str
    predicted_p_recovery: float
    expected_recovered_amount: float
    intervention_cost: float
    incentive_cost: float
    fatigue_penalty: float
    risk_penalty: float
    expected_net_value: float
    is_blocked: bool = False
    block_reason: Optional[str] = None

class BlockedAction(BaseModel):
    action: str
    reason: str

class GuardrailResult(BaseModel):
    guardrail: str
    status: str  # PASS, BLOCK, ESCALATE
    reason: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Explanation(BaseModel):
    summary: str
    key_factors: List[str]
    why_selected: str
    why_not_selected: Dict[str, str]
    customer_message_preview: Optional[str] = None

class DecisionContract(BaseModel):
    """
    Canonical Decision Contract.
    Unified representation across backend, DB, APIs, frontend, and traces.
    """
    decision_id: str
    payment_id: str
    timestamp: datetime
    model_version: str
    policy_version: str
    feature_snapshot: Dict[str, Any]
    candidate_actions: List[str]
    feasible_actions: List[str]
    blocked_actions: List[BlockedAction]
    candidate_scores: List[CandidateActionScore] = Field(default_factory=list)
    predicted_recovery_probability: float
    expected_recovered_amount: float
    intervention_cost: float
    incentive_cost: float
    fatigue_penalty: float
    risk_penalty: float
    expected_net_value: float
    selected_action: str  # High-ENV action or STOP_INTERVENTION
    decision_status: str  # AUTO_EXECUTE, RECOMMEND_FOR_APPROVAL, BLOCK
    approval_required: bool
    guardrail_results: List[GuardrailResult]
    explanation: Explanation
    execution_status: str  # PENDING_SIMULATION, EXECUTED, APPROVED, REJECTED, NOT_EXECUTED

class PaymentResponse(BaseModel):
    payment_id: str
    customer_id: str
    customer_name: str
    customer_email: str
    amount: float
    currency: str
    payment_method: str
    failure_reason: str
    failure_code: str
    status: str
    created_at: datetime
    latest_decision: Optional[DecisionContract] = None
    latest_outcome: Optional[Dict[str, Any]] = None

class ExperimentRequest(BaseModel):
    sample_size: int = 2000
    random_seed: int = 42
    baseline_policy_name: str = "Standard Retry Schedule"
    ai_policy_name: str = "RecoverIQ Decision Engine"

class ExperimentResponse(BaseModel):
    experiment_id: str
    sample_size: int
    random_seed: int
    baseline_recovered_revenue: float
    ai_recovered_revenue: float
    incremental_revenue: float
    baseline_recovery_rate: float
    ai_recovery_rate: float
    gross_recovery_lift_pct: float
    baseline_costs: float
    ai_costs: float
    incremental_intervention_cost: float
    baseline_net_value: float
    ai_net_value: float
    net_incremental_value: float
    roi: float
    roi_display_label: str = "Cost Saving (Pure Gain)"
    gross_recovery_lift_ci_95: Optional[List[float]] = None
    incremental_revenue_ci_95: Optional[List[float]] = None
    net_incremental_value_ci_95: Optional[List[float]] = None
    methodology: str = "Paired Counterfactual Simulation with Common Random Numbers (CRN) & 500-Iteration Bootstrap 95% CI"
    created_at: datetime

class AgentEventResponse(BaseModel):
    event_id: str
    payment_id: str
    timestamp: datetime
    stage: str  # INGEST, CONTEXT, PREDICT, OPTIMIZE, GUARDRAIL, DECIDE, ACT, OUTCOME, LEARN
    status: str  # INFO, WARN, ERROR, SUCCESS
    message: str
    metadata_json: Dict[str, Any]

class AnalyticsSummaryResponse(BaseModel):
    revenue_at_risk: float
    expected_recoverable: float
    recovered_revenue: float
    baseline_recovered_revenue: float
    incremental_revenue: float
    recovery_rate_pct: float
    baseline_recovery_rate_pct: float
    interventions_avoided: int
    net_incremental_value: float
    roi: float
