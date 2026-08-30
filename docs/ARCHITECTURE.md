# RecoverIQ Architecture Specification

## 1. System Overview & Design Philosophy

RecoverIQ is built as an enterprise-grade **modular monolith** optimized for low-latency decision optimization, statistical rigor, auditability, and fintech compliance. The architecture cleanly separates probabilistic machine learning, deterministic business guardrails, and financial mathematical optimization.

```
                    ┌──────────────────────────────────────┐
                    │      Payment Gateway Webhook         │
                    │   (payment.failed event payload)     │
                    └──────────────────┬───────────────────┘
                                       │
                                       ▼
                    ┌──────────────────────────────────────┐
                    │       FastAPI Gateway Layer          │
                    │    Pydantic Schema Validation        │
                    └──────────────────┬───────────────────┘
                                       │
            ┌──────────────────────────┴──────────────────────────┐
            ▼                                                     ▼
┌───────────────────────┐                             ┌───────────────────────┐
│ Feature Extraction    │                             │ Deterministic Rules   │
│ Pipeline              │                             │ Engine (Guardrails)   │
│ (Zero Leakage Barrier)│                             │ 5-Level Validation    │
└───────────┬───────────┘                             └───────────┬───────────┘
            │                                                     │
            │ Pre-Decision Feature Context                        │ Feasible Action Set
            │                                                     │
            └──────────────────────────┬──────────────────────────┘
                                       ▼
                    ┌──────────────────────────────────────┐
                    │ Calibrated ML Predictor              │
                    │ HistGBM + Platt Scaling (cv=3)       │
                    │ Permutation Feature Importance       │
                    └──────────────────┬───────────────────┘
                                       │
                                       ▼
                    ┌──────────────────────────────────────┐
                    │ Expected Net Value (ENV) Optimizer   │
                    │ Dynamic Fatigue & Risk Penalties     │
                    └──────────────────┬───────────────────┘
                                       │
                                       ▼
                    ┌──────────────────────────────────────┐
                    │ Canonical Decision Contract          │
                    │ States: AUTO_EXECUTE /               │
                    │ RECOMMEND_FOR_APPROVAL / BLOCK       │
                    └──────────────────┬───────────────────┘
                                       │
            ┌──────────────────────────┴──────────────────────────┐
            ▼                                                     ▼
┌───────────────────────┐                             ┌───────────────────────┐
│ Simulated Execution / │                             │ Counterfactual Engine │
│ Human Approval API    │                             │ CRN + 500-iter Bootstrap│
│ (/approve, /reject)   │                             │ 95% Confidence Bounds │
└───────────┬───────────┘                             └───────────┬───────────┘
            │                                                     │
            └──────────────────────────┬──────────────────────────┘
                                       ▼
                    ┌──────────────────────────────────────┐
                    │ Persistent Audit & Ledger (SQLite)   │
                    │ Observable Event Stream              │
                    └──────────────────────────────────────┘
```

---

## 2. Core Modules Breakdown

### 2.1 Feature Pipeline & Leakage Barrier (`app/ml/features.py`)
- **Strict Pre-Decision Schema**: Restricts model inputs to features available before intervention (e.g., amount, tenure, past recovery rate, failure reason, contact history).
- **Automated Leakage Assertion**: Asserts that outcome fields (`actual_outcome`, `recovered_amount`, `actual_cost`, `ground_truth_p`) are absent before prediction.

### 2.2 Deterministic Guardrails Engine (`app/guardrails/engine.py`)
Hierarchical rule enforcement that takes precedence over ML optimization:
1. **Safety**: `do_not_contact == True` $\rightarrow$ Hard block (Stop Intervention).
2. **Customer Fatigue Limits**: `contacts_24h >= 2` or `contacts_7d >= 5` $\rightarrow$ Blocks outreach.
3. **Failure Limits**: `consecutive_failures >= 3` $\rightarrow$ Blocks automated retries.
4. **Instrument Suitability**: `Expired Card` blocks retries and generic nudges (requires Payment Method Update); technical downtime blocks instrument updates.
5. **Financial Safeguards**: High transaction amounts ($\ge \text{₹}50,000$) or low confidence ($P < 0.60$) require operator approval.

### 2.3 Calibrated ML Prediction Engine (`app/ml/models.py`)
- **Algorithm**: `HistGradientBoostingClassifier` with `LogisticRegression` baseline.
- **Calibration**: `CalibratedClassifierCV(method="sigmoid", cv=3)` (Platt Scaling) ensuring Brier score optimization and minimal Expected Calibration Error (ECE: 0.0281).
- **Feature Importance**: Permutation Feature Importance computed on validation split ($N=750$, 5 repeats).
- **Evaluation Strategy**: Chronological time-aware train/validation/test split (70% / 15% / 15%).

### 2.4 Decision Optimizer & State Machine (`app/decision_engine/optimizer.py`)
- Evaluates **Expected Net Value (ENV)**:
  $$\text{ENV}(a) = P(\text{Recovery} \mid \mathbf{x}, a) \cdot \text{Amount} - C_{\text{intervention}}(a) - C_{\text{incentive}}(a) - \text{Penalty}_{\text{fatigue}}(a) - \text{Penalty}_{\text{risk}}(a)$$
- Generates structured **Decision Contract** with one of three states:
  - `AUTO_EXECUTE`: Feasible action with $\text{ENV} > 0$ and standard risk.
  - `RECOMMEND_FOR_APPROVAL`: High-value ($\ge ₹50,000$) or low confidence ($P < 0.60$) transaction requiring human operator review.
  - `BLOCK`: Zero feasible actions or $\text{ENV} \le 0$ (terminates with Stop Intervention, $\text{ENV} = 0$, $C = 0$).

### 2.5 Counterfactual Experimentation Engine (`app/simulation/engine.py`)
- Evaluates canonical RecoverIQ policy against Standard Retry Baseline on identical cohorts using **Common Random Numbers (CRN)**.
- Computes **500-Iteration Paired Bootstrap 95% Confidence Intervals** for gross recovery lift, incremental revenue, and net incremental value.

### 2.6 Human-in-the-Loop & Execution State Guards (`app/api/payments.py`)
- `POST /api/v1/payments/{payment_id}/approve`: Operator sign-off for pending recommendations.
- `POST /api/v1/payments/{payment_id}/reject`: Operator rejection permanently blocking execution.
- `POST /api/v1/payments/{payment_id}/execute`: Enforces approval prerequisites and prevents duplicate execution.

---

## 3. Database Schema (SQLite / SQLAlchemy)

- **`payments`**: Core transaction record storing pre-decision features, decision status (`AUTO_EXECUTE`, `RECOMMEND_FOR_APPROVAL`, `BLOCK`), execution status (`PENDING_SIMULATION`, `APPROVED`, `REJECTED`, `EXECUTED`, `NOT_EXECUTED`), and serialized `candidate_scores_json`.
- **`agent_events`**: Immutable append-only audit stream tracking stage, status, operator actions, and execution metadata.
- **`experiments`**: Persisted counterfactual simulation runs with sample size, random seed, confidence intervals, and ROI metrics.
