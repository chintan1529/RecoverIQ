# RecoverIQ — AI Revenue Recovery Decision Engine

> **Razorpay AI Builder Internship 2026 — Track 3: AI Revenue Recovery**
>
> *"Given a failed payment, what is the highest-value action to take, when should we take it, and is that intervention actually worth taking?"*

---

## 🚀 Executive Overview

**RecoverIQ** is an enterprise-grade AI decision engine designed to solve the multi-billion dollar problem of failed transaction loss in modern fintech and subscription commerce.

Unlike legacy recovery tools that rely on naive fixed retry schedules (e.g., blind 24-hour retries) or spam customers with repetitive payment links, RecoverIQ treats revenue recovery as an **action-conditioned decision optimization problem**:

$$\text{Expected Net Value (ENV)} = P(\text{Recovery} \mid \mathbf{x}_{\text{pre}}, a) \times \text{Amount} - C_{\text{intervention}}(a) - C_{\text{incentive}}(a) - \text{Penalty}_{\text{fatigue}}(a) - \text{Penalty}_{\text{risk}}(a)$$

Every decision produces an immutable, cryptographically verifiable **Decision Contract** governed by deterministic fintech guardrails, preventing customer fatigue, financial loss, and unnecessary intervention costs.

```
                  ┌──────────────────────────────────────────────┐
                  │           FAILED PAYMENT DETECTED            │
                  │ (Webhook: Amount, Failure Code, Method, etc) │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │         1. FEATURE EXTRACTION PIPELINE       │
                  │   Pre-Decision Context (Zero Data Leakage)   │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │       2. DETERMINISTIC GUARDRAILS ENGINE     │
                  │ Safety ➔ Contact Limits ➔ Financial Escalation│
                  │         Produces: Feasible Action Set        │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │    3. CALIBRATED ML PROBABILITY SCORER       │
                  │    HistGBM + Platt Scaling (K=3)             │
                  │    Permutation Feature Importance            │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │       4. EXPECTED NET VALUE OPTIMIZER        │
                  │  Ranks Feasible Actions ➔ Generates Contract │
                  │ States: AUTO_EXECUTE | RECOMMEND | BLOCK     │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │         5. EXECUTION & AUDIT LOGGING         │
                  │ Human Approval (/approve, /reject)           │
                  │ CRN Simulation + 500-iter Bootstrap 95% CI   │
                  └──────────────────────────────────────────────┘
```

---

## 🏆 Key Innovations & Technical Highlights

### 1. Mathematical Rigor & Calibrated Machine Learning
- **Platt Scaling Probability Calibration**: Uses `CalibratedClassifierCV(method="sigmoid", cv=3)` on chronological customer-grouped train/val/test splits, reducing Brier score to **0.1889** and Expected Calibration Error (ECE) to **0.0316** (3.16%).
- **Permutation Feature Importance**: True out-of-sample permutation importance calculated strictly on observational pre-decision customer features on the validation split.
- **Strict Data Leakage Barrier**: Features receive strictly pre-decision customer and payment context ($\mathbf{x}_{\text{pre}}$). Post-action outcomes and recovered amounts are forbidden and protected with automated assertions.

### 2. Multi-Tier Guardrails That Override AI
Deterministic business, customer fatigue, and financial constraints strictly bound the AI:
1. **Safety & Policy**: Do-Not-Contact flag immediately enforces `Stop Intervention` (`BLOCK`).
2. **Customer Fatigue Frequency Caps**: Maximum 2 contacts in 24 hours and 5 contacts in 7 days.
3. **Consecutive Failure Limits**: 3 consecutive failures block automated retries to avoid gateway velocity abuse.
4. **Instrument Suitability**: Expired card failures block retries and generic nudges (requires instrument update).
5. **Financial Escalation**: High-value transactions ($\ge \text{₹}50,000$) or low confidence require operator approval (`RECOMMEND_FOR_APPROVAL`).

### 3. Paired Counterfactual A/B Experimentation Engine
- Evaluates **Canonical RecoverIQ Policy** against **Standard Baseline Retry Policy** across identical cohorts using **Common Random Numbers (CRN)**.
- **500-Iteration Paired Bootstrap Resampling** computes empirical 95% Confidence Intervals for gross lift, incremental revenue, and net value.

### 4. Enterprise-Grade Decision Contract
Every payment evaluation yields a structured JSON contract containing:
- Feature snapshot
- Ranked candidate actions & expected net values
- Blocked actions and deterministic guardrail violation reasons
- Decision state (`AUTO_EXECUTE`, `RECOMMEND_FOR_APPROVAL`, `BLOCK`)
- Dual natural language explainability with structured fact validation

---

## 🛠️ System Architecture & Tech Stack

```
RecoverIQ/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI REST endpoints (payments, analytics, experiments, strategies, demo, webhooks)
│   │   ├── core/             # Configuration, database session, API key auth, PII masking
│   │   ├── decision_engine/  # Fatigue calculator, ENV evaluator, Decision optimizer
│   │   ├── evaluation/       # CLI reproducible model evaluation script
│   │   ├── guardrails/       # 5-tier deterministic rule engine
│   │   ├── llm/              # Gemini SDK wrapper + validated structured fallback explainer
│   │   ├── ml/               # Synthetic generator, feature pipeline, calibrated ML models
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic schemas & DecisionContract
│   │   └── simulation/       # Common Random Numbers (CRN) + Bootstrap 95% CI engine
│   ├── tests/                # Pytest suite covering security, concurrency, guardrails, and leakage
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/       # KPIOverview, RecoveryChart, PaymentQueue, DecisionStudio, WebhookHub, ModelScience, ROI Calculator
│   │   ├── services/         # Axios API client with authenticated headers
│   │   ├── types/            # TypeScript interfaces
│   │   └── index.css         # Dark slate + Emerald fintech design system
│   ├── package.json
│   └── vite.config.ts
└── docs/                     # Comprehensive engineering & competition documentation
```

---

## ⚡ Quickstart & Verification Commands

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ and `npm`

### 2. Environment Setup
```bash
# Copy example environment configuration
cp .env.example .env

# Install backend dependencies
pip install -r backend/requirements.txt

# Install frontend dependencies
cd frontend && npm install && cd ..
```

### 3. Launch Development Server
```bash
# Start backend (FastAPI) on :8000 and frontend (Vite) on :5173
npm run dev
```
- **Backend (FastAPI)**: `http://127.0.0.1:8000` (Swagger docs: `http://127.0.0.1:8000/docs`).
- **Frontend (React + Vite)**: `http://localhost:5173/`.

### 4. Reproduce ML Model Evaluation Metrics
```bash
python backend/app/evaluation/evaluate_model.py
```

### 5. Run Automated Test Suite
```bash
pytest backend/tests/ -v
```

### 6. Build Frontend Production Bundle
```bash
cd frontend && npm run build
```

---

## 📊 Live Benchmark Metrics (Evaluated on Untouched Holdout Test Set)

*Reproducible via: `python backend/app/evaluation/evaluate_model.py`*

| Metric | Baseline Logistic Regression | Primary (Uncalibrated) | RecoverIQ (Calibrated) | Benchmark Significance |
|---|---|---|---|---|
| **ROC-AUC** | 0.7694 | 0.7414 | **0.7497** | Measures rank-order discrimination |
| **PR-AUC** | 0.6086 | 0.5585 | **0.5806** | Precision-Recall under class imbalance |
| **Brier Score** | 0.1823 | 0.1973 | **0.1889** | Lower is better (MSE vs binary outcome) |
| **Expected Calibration Error (ECE)** | 0.0628 | 0.0712 | **0.0316** | Mean discrepancy between confidence & accuracy (3.16%) |
| **Gross Recovery Lift (Simulated)** | Baseline Policy | — | **+16.1 pp** | 95% CI: [+13.5 pp, +18.7 pp] |
