export interface BlockedAction {
  action: string;
  reason: string;
}

export interface GuardrailResult {
  guardrail: string;
  status: 'PASS' | 'BLOCK' | 'ESCALATE';
  reason: string;
  metadata?: Record<string, any>;
}

export interface Explanation {
  summary: string;
  key_factors: string[];
  why_selected: string;
  why_not_selected: Record<string, string>;
  customer_message_preview?: string;
}

export interface CandidateActionScore {
  action: string;
  predicted_p_recovery: number;
  expected_recovered_amount: number;
  intervention_cost: number;
  incentive_cost: number;
  fatigue_penalty: number;
  risk_penalty: number;
  expected_net_value: number;
  is_blocked: boolean;
  block_reason?: string | null;
}

export interface DecisionContract {
  decision_id: string;
  payment_id: string;
  timestamp: string;
  model_version: string;
  policy_version: string;
  feature_snapshot: Record<string, any>;
  candidate_actions: string[];
  feasible_actions: string[];
  blocked_actions: BlockedAction[];
  candidate_scores: CandidateActionScore[];
  predicted_recovery_probability: number;
  expected_recovered_amount: number;
  intervention_cost: number;
  incentive_cost: number;
  fatigue_penalty: number;
  risk_penalty: number;
  expected_net_value: number;
  selected_action: string;
  decision_status: 'AUTO_EXECUTE' | 'RECOMMEND_FOR_APPROVAL' | 'BLOCK';
  approval_required: boolean;
  guardrail_results: GuardrailResult[];
  explanation: Explanation;
  execution_status: 'PENDING_SIMULATION' | 'EXECUTED' | 'APPROVED' | 'REJECTED' | 'NOT_EXECUTED';
}

export interface Payment {
  payment_id: string;
  customer_id: string;
  customer_name: string;
  customer_email: string;
  amount: number;
  currency: string;
  payment_method: string;
  failure_reason: string;
  failure_code: string;
  status: string;
  created_at: string;
  latest_decision?: DecisionContract;
  latest_outcome?: {
    outcome_id: string;
    selected_action: string;
    actual_outcome: 'SUCCESS' | 'FAILED';
    recovered_amount: number;
    actual_cost: number;
    recorded_at: string;
  };
}

export interface AnalyticsSummary {
  revenue_at_risk: number;
  expected_recoverable: number;
  recovered_revenue: number;
  baseline_recovered_revenue: number;
  incremental_revenue: number;
  recovery_rate_pct: number;
  baseline_recovery_rate_pct: number;
  interventions_avoided: number;
  net_incremental_value: number;
  roi: number;
}

export interface ExperimentResponse {
  experiment_id: string;
  sample_size: number;
  random_seed: number;
  baseline_recovered_revenue: number;
  ai_recovered_revenue: number;
  incremental_revenue: number;
  baseline_recovery_rate: number;
  ai_recovery_rate: number;
  gross_recovery_lift_pct: number;
  baseline_costs: number;
  ai_costs: number;
  incremental_intervention_cost: number;
  baseline_net_value: number;
  ai_net_value: number;
  net_incremental_value: number;
  roi: number;
  roi_display_label: string;
  gross_recovery_lift_ci_95?: [number, number];
  incremental_revenue_ci_95?: [number, number];
  net_incremental_value_ci_95?: [number, number];
  methodology?: string;
  created_at: string;
}

export interface AgentEvent {
  event_id: string;
  payment_id: string;
  timestamp: string;
  stage: string;
  status: string;
  message: string;
  metadata_json: Record<string, any>;
}

export interface StrategyPerformance {
  action: string;
  attempts: number;
  recovery_rate_pct: number;
  recovered_revenue: number;
  avg_cost_per_recovery: number;
  roi: number;
  best_segment: string;
}

export interface FeatureAttribution {
  feature: string;
  label: string;
  value: string | number;
  contribution: number;
  direction: 'positive' | 'negative';
}

export interface AttributionsResult {
  base_probability: number;
  predicted_probability: number;
  net_lift_from_base: number;
  attributions: FeatureAttribution[];
}

export interface WhatIfResponse {
  contract: DecisionContract;
  attributions: AttributionsResult;
  is_what_if: boolean;
  timestamp: string;
}

export interface CalibrationBin {
  bin_range: string;
  mean_uncalibrated: number | null;
  mean_calibrated: number | null;
  empirical_rate: number | null;
  sample_count: number;
  bin_error: number;
}

export interface TopFeatureImportance {
  feature: string;
  importance: number;
  share_pct: number;
}

export interface CalibrationData {
  bins: CalibrationBin[];
  ece: number;
  uncalibrated_ece: number;
  calibration_gain_pct: number;
  brier_score: number;
  roc_auc: number;
  pr_auc: number;
  top_features: TopFeatureImportance[];
  sample_counts?: {
    total: number;
    train_size: number;
    val_size: number;
    test_size: number;
  };
}

export interface RoiCalculatorResponse {
  inputs: {
    monthly_gmv: number;
    failure_rate_pct: number;
    aov: number;
    margin_pct: number;
    monthly_failed_gmv: number;
    monthly_failed_transactions: number;
  };
  recovery_rates: {
    baseline_recovery_pct: number;
    recoveriq_recovery_pct: number;
    gross_lift_pp: number;
    ci_95_bounds_pp: [number, number];
  };
  financial_impact: {
    monthly_recovered_gmv: number;
    monthly_incremental_gmv: number;
    annual_incremental_gmv: number;
    annual_ci_95_gmv: [number, number];
    annual_channel_operating_cost: number;
    annual_net_incremental_value: number;
    annual_merchant_net_profit: number;
    roi_multiplier: number;
    gmv_multiplier?: number;
    payback_period_days: number;
  };
}

export interface RazorpayWebhookReceipt {
  status: string;
  webhook_event: string;
  payment_id: string;
  customer_id: string;
  customer_name: string;
  amount_inr: number;
  failure_reason: string;
  selected_action: string;
  predicted_recovery_probability: number;
  expected_net_value: number;
  decision_status: string;
  approval_required: boolean;
  dispatch_channel: string;
  razorpay_payment_link?: string | null;
  execution_latency_ms: number;
  explanation: string;
  timestamp: string;
}

export interface PreDecisionFeaturesInput {
  payment_id?: string;
  customer_id?: string;
  amount: number;
  payment_method: string;
  failure_reason: string;
  failure_code?: string;
  customer_tier?: string;
  historical_recovery_rate?: number;
  propensity_score?: number;
  contact_count_24h?: number;
  contact_count_7d?: number;
  consecutive_failures?: number;
  do_not_contact?: boolean;
}

