from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.pydantic_schemas import ExperimentRequest, ExperimentResponse
from app.simulation.engine import CounterfactualExperimentEngine
from app.api.payments import global_ml_model
from app.models.db_models import ExperimentDB

router = APIRouter(prefix="/experiments", tags=["Experiments"])
exp_engine = CounterfactualExperimentEngine(global_ml_model)

@router.post("/run", response_model=ExperimentResponse)
def run_experiment(req: ExperimentRequest, db: Session = Depends(get_db)):
    res = exp_engine.run_counterfactual_simulation(
        sample_size=req.sample_size,
        random_seed=req.random_seed,
        baseline_policy_name=req.baseline_policy_name,
        ai_policy_name=req.ai_policy_name
    )

    db_exp = ExperimentDB(
        experiment_id=res.experiment_id,
        name=f"Experiment (Seed {req.random_seed}, N={req.sample_size})",
        sample_size=res.sample_size,
        random_seed=res.random_seed,
        baseline_policy_json={"name": req.baseline_policy_name},
        ai_policy_json={"name": req.ai_policy_name},
        baseline_recovered_revenue=res.baseline_recovered_revenue,
        ai_recovered_revenue=res.ai_recovered_revenue,
        incremental_revenue=res.incremental_revenue,
        gross_recovery_lift_pct=res.gross_recovery_lift_pct,
        incremental_intervention_cost=res.incremental_intervention_cost,
        net_incremental_value=res.net_incremental_value,
        roi=res.roi,
        created_at=res.created_at
    )
    db.add(db_exp)
    db.commit()

    return res

@router.get("/history")
def get_experiment_history(db: Session = Depends(get_db)):
    return db.query(ExperimentDB).order_by(ExperimentDB.created_at.desc()).limit(10).all()

@router.get("/sensitivity")
def get_sensitivity_analysis():
    """
    Returns empirical sensitivity analysis across multiple operational scales and parameter perturbations.
    """
    return exp_engine.run_sensitivity_suite(random_seed=42)

