import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.ml.generator import generate_synthetic_dataset, get_hero_pitch_scenarios
from app.ml.models import RecoveryPredictorModel
from app.decision_engine.optimizer import DecisionOptimizerEngine
from app.schemas.pydantic_schemas import PreDecisionFeatures

df_pre, df_post = generate_synthetic_dataset(n_samples=2000, seed=42)
model = RecoveryPredictorModel()
model.train_and_evaluate(df_pre, df_post)
optimizer = DecisionOptimizerEngine(model)

scenarios = get_hero_pitch_scenarios()
for s in scenarios:
    feat = PreDecisionFeatures(**s)
    dec = optimizer.optimize_and_decide(feat)
    print(f"=== {s['scenario_id']}: {s['name']} ===")
    print(f"  Selected Action: {dec.selected_action}")
    print(f"  P(Recovery): {dec.predicted_recovery_probability:.2%}")
    print(f"  ENV: INR {dec.expected_net_value:,.2f}")
    print(f"  Decision Status: {dec.decision_status}")
    print(f"  Execution Status: {dec.execution_status}")
    print(f"  Feasible Actions: {dec.feasible_actions}")
    print(f"  Blocked Actions: {[b.action for b in dec.blocked_actions]}")
    for cs in dec.candidate_scores:
        print(f"    - {cs.action}: P={cs.predicted_p_recovery:.2%}, Cost={cs.intervention_cost}, Fatigue={cs.fatigue_penalty}, ENV={cs.expected_net_value}, Blocked={cs.is_blocked}")
    print()
