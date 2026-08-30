# RecoverIQ — Forensic Baseline Audit Report

**Date & Time**: August 29, 2026  
**Audit Purpose**: Pre-hardening inspection of ML models, decision engine, simulation pipeline, guardrails, API contracts, tests, and documentation.

---

## 1. Executive Summary & Verification Baseline

| Subsystem | Baseline State | Status | Audited Defect / Finding |
|---|---|---|---|
| **Backend Test Suite** | 33 passed / 0 failed (32.8s) | Passing | All 33 tests pass, but coverage gaps exist in calibration, bootstrap CIs, and state transition guards. |
| **Frontend Production Build** | Vite production build passed (2.05s) | Clean | 0 TypeScript errors. Bundle size warning on Recharts chunk. |
| **ML Model (`models.py`)** | HistGradientBoosting + LogisticRegression | Functional | Feature importance generated via `np.random.uniform` (mock). Probability output raw/uncalibrated. Validation set unused. |
| **Feature Pipeline (`features.py`)** | One-hot + Fast numpy single-vectorizer | Robust | Pre-decision leakage assertion active. |
| **Counterfactual Simulator (`engine.py`)** | Common Random Numbers | Proxy Divergence | Evaluates RecoverIQ using hardcoded `if/elif` branch heuristics rather than calling the canonical decision policy. Confidence intervals not computed. |
| **Analytics API (`analytics.py`)** | Summary & 14-day Chart | Arbitrary Multiplier | Uses arbitrary heuristic multipliers (`* 0.70` and `* 0.75`) for baseline instead of counterfactual policy evaluation. |
| **Database Startup (`main.py`)** | Auto-seeding in lifespan | Wipe on Restart | Startup lifespan wiped and re-seeded database on every server restart. |
| **LLM Provider (`provider.py`)** | Gemini API + Fallback | Unvalidated | No schema/financial fact validator on LLM response; could accept hallucinated probabilities or amounts. |
| **Payment API (`payments.py`)** | CRUD + Evaluate + Execute | State Transition Gap | No duplicate execution guard; no explicit `/reject` endpoint for human escalation. |
| **Documentation (`docs/`)** | 8 Architecture / Methodology docs | Discrepancies | Cost matrix in `DECISION_ENGINE.md` differs from `config.py`. Calibration claims in `MODEL_CARD.md` not yet implemented in code. |

---

## 2. Detailed Findings by Subsystem

### A. Machine Learning Pipeline (`backend/app/ml/models.py`)
1. **Mock Feature Importance**: `self.feature_importances_ = {col: float(np.random.uniform(0.01, 0.25)) ...}` was generating random uniform values instead of statistically legitimate permutation importance or model-native tree importance.
2. **Missing Calibration**: `MODEL_CARD.md` described the model as "calibrated", but `models.py` called `predict_proba` directly without a `CalibratedClassifierCV` or validation-set calibration mapping (Platt / Isotonic).
3. **Unused Validation Split**: In `train_and_evaluate()`, `X_val, y_val` was extracted (15% split) but never used for hyperparameter selection or calibration fitting.

### B. Counterfactual Simulation Engine (`backend/app/simulation/engine.py`)
1. **Heuristic Branching in Simulation**: Lines 98-117 in `CounterfactualExperimentEngine` used handwritten `if/elif` rules for RecoverIQ actions rather than querying the canonical `DecisionOptimizerEngine`.
2. **Missing Uncertainty Estimation**: The experiment engine returned only point estimates for recovery rates and net value without paired bootstrap confidence intervals (e.g. 95% CI).

### C. Analytics Baseline Calculation (`backend/app/api/analytics.py`)
1. **Arbitrary Static Multipliers**: Lines 32-33 calculated `baseline_recovered_revenue = recovered_amount * 0.70` and `baseline_recovery_rate = recovery_rate * 0.75`. This is an assumed heuristic rather than a counterfactual baseline evaluation.

### D. Startup & State Machine Lifecycle (`backend/app/main.py`, `payments.py`)
1. **Database Reset on Restart**: `lifespan` always wiped and reseeded the database on server start.
2. **Execution Idempotency**: `execute_payment_simulation` lacked idempotent checks for already executed or abandoned payments.
3. **Missing Rejection Transition**: No endpoint existed for an operator to formally reject a `RECOMMEND_FOR_APPROVAL` decision.

### E. Documentation Consistency
1. **Cost Matrix Mismatch**: `docs/DECISION_ENGINE.md` listed Payment Method Update as ₹0.30 and Human Escalation as ₹25.00, whereas `config.py` uses ₹25.00 and ₹150.00 respectively.

---

## 3. Hardening Plan & Objectives
1. **Phase 1-3**: Implement proper Chronological Split, CalibratedClassifierCV (isotonic/sigmoid on validation set), Permutation Importance, and reproducible evaluation script `backend/app/evaluation/evaluate_model.py`.
2. **Phase 4-5**: Implement Action-Conditioned invariant tests.
3. **Phase 6-7**: Integrate canonical decision optimizer into counterfactual simulation; implement paired bootstrap confidence intervals (95% CI).
4. **Phase 8-9**: Replace arbitrary multipliers with principled counterfactual baseline policy tracking.
5. **Phase 10-14**: Harden guardrails, state transitions, duplicate execution guards, and `/reject` endpoint.
6. **Phase 15-16**: Add structured validation to Gemini LLM responses.
7. **Phase 17-18**: Make database startup idempotent (seed only if empty; preserve existing data).
8. **Phase 19-20**: Synchronize all documentation and expand test suite with property and invariant tests.
