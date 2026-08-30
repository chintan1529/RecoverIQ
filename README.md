# RecoverIQ: Enterprise AI Revenue Recovery Decision Engine

### Autonomous Action-Conditioned Decision Optimization for Payment Failure Recovery
**Razorpay AI Builder Initiative | Track: AI Revenue Recovery**

---

## 1. Executive Summary

RecoverIQ is an enterprise-grade decision optimization engine engineered to solve involuntary churn and revenue loss resulting from failed transactions in modern digital commerce and subscription billing.

Traditional payment recovery workflows rely on static, rule-based retry schedules (e.g., rigid 24-hour retries) or undifferentiated customer outreach. These legacy approaches suffer from three structural deficiencies:
1. **Excessive Gateway Fees**: Repeatedly hitting failing payment methods incurs avoidable gateway charges and risks card network velocity penalties.
2. **Customer Relationship Attrition**: Indiscriminate SMS, email, and WhatsApp notifications induce fatigue, driving voluntary cancellations.
3. **Suboptimal Intervention Economics**: Interventions with negative unit economics (e.g., offering financial incentives or manual outreach on low-margin transactions) are executed blindly.

RecoverIQ reformulates revenue recovery as a constrained, action-conditioned stochastic optimization problem. Given any failed payment event, the engine evaluates the full action space, computes calibrated empirical recovery probabilities, subtracts operational and relationship fatigue costs, enforces strict multi-tier deterministic guardrails, and outputs an immutable, auditable **Decision Contract**.

---

## 2. Mathematical Formulation

### 2.1 Expected Net Value (ENV) Objective

For a transaction with gross amount $A$, pre-decision feature vector $\mathbf{x} \in \mathcal{X}$, and candidate action $a \in \mathcal{A}$, the engine maximizes the Expected Net Value:

$$\text{ENV}(\mathbf{x}, a) = P(\text{Recovery} \mid \mathbf{x}, a) \cdot A - C_{\text{intervention}}(a) - C_{\text{incentive}}(A, a) - \Omega_{\text{fatigue}}(\mathbf{x}, a) - \Omega_{\text{risk}}(A, a)$$

Where:
* $P(\text{Recovery} \mid \mathbf{x}, a) \in [0, 1]$ represents the Platt-calibrated probability of recovery conditional on action $a$.
* $C_{\text{intervention}}(a)$ is the direct channel dispatch cost (e.g., SMS, WhatsApp API, gateway network retry fee).
* $C_{\text{incentive}}(A, a)$ represents fee waivers or discount costs, bounded by $\min(A \cdot \kappa_{\max}, \text{Cap})$.
* $\Omega_{\text{fatigue}}(\mathbf{x}, a)$ is the non-linear relationship penalty scaling with recent customer contact frequency ($c_{24h}, c_{7d}$) and consecutive failure count.
* $\Omega_{\text{risk}}(A, a)$ is the financial exposure penalty applied to unassisted high-value retries.

### 2.2 Optimal Policy Selection

The optimal recovery strategy $a^*$ is selected strictly from the feasible action set $\mathcal{A}_{\text{feasible}} \subseteq \mathcal{A}$ determined by deterministic business guardrails:

$$a^* = \arg\max_{a \in \mathcal{A}_{\text{feasible}}(\mathbf{x})} \text{ENV}(\mathbf{x}, a)$$

If $\max_{a} \text{ENV}(\mathbf{x}, a) \le 0$, the engine selects `Stop Intervention`, preventing unprofitable outreach and eliminating customer fatigue.

### 2.3 Platt Probability Calibration

Raw tree-ensemble scores $f(\mathbf{x}, a)$ are calibrated via cross-validated Platt scaling (sigmoid transformation) fit on out-of-time validation data:

$$P(\text{Recovery} \mid \mathbf{x}, a) = \frac{1}{1 + \exp\left( -\left(\alpha \cdot f(\mathbf{x}, a) + \beta\right) \right)}$$

This eliminates overconfident probability spikes, ensuring that Expected Net Value calculations reflect true empirical conversion frequencies.

---

## 3. System Architecture and End-to-End Pipeline

```
                       FAILED TRANSACTION INGESTION
             (Razorpay Webhook / REST Ingestion / Batch Stream)
                                     │
                                     ▼
                   [ 1. PRE-DECISION FEATURE EXTRACTION ]
             • Zero Lookahead Guarantee (Strict Temporal Boundary)
             • Customer Fatigue Metrics (Contacts 24h, Contacts 7d)
             • Payment Profile (Instrument, Failure Reason, Amount)
                                     │
                                     ▼
                   [ 2. DETERMINISTIC GUARDRAILS ENGINE ]
             • Do-Not-Contact (DNC) Compliance Check
             • Customer Frequency Caps (Max 2 in 24h, Max 5 in 7d)
             • Instrument Feasibility (Expired Card Retry Ban)
             • Financial Value Thresholds (>= INR 50,000 Escalation)
                                     │
                        Produces Feasible Action Set
                                     │
                                     ▼
                   [ 3. CALIBRATED ML SCORING SERVICE ]
             • HistGradientBoostingClassifier Scorer
             • 3-Fold Cross-Validated Platt Sigmoid Scaling
             • Action-Conditioned Scoring Across All Feasible Candidates
                                     │
                                     ▼
                   [ 4. EXPECTED NET VALUE OPTIMIZER ]
             • Evaluate Objective Function for All Feasible Actions
             • Compute Feature Attributions (Marginal SHAP Decomposition)
             • Assign State: AUTO_EXECUTE | RECOMMEND_FOR_APPROVAL | BLOCK
                                     │
                                     ▼
                   [ 5. DECISION CONTRACT & DISPATCH ]
             • Structured Audit Record (Zero PII Exposure)
             • Autonomous Execution Gateway / Human-in-the-Loop Review
             • Razorpay Smart Payment Link Generation
```

---

## 4. Decision Lifecycle and State Machine

Every evaluated payment produces an immutable Decision Contract transitioning through a formal finite state machine:

| Decision State | Trigger Condition | System Action | Execution Mode |
| :--- | :--- | :--- | :--- |
| **`AUTO_EXECUTE`** | $\text{ENV}(a^*) > 0$, Amount $< \text{INR } 50,000$, $P(\text{Recovery}) \ge 0.45$, all guardrails satisfied. | Instantly dispatches optimal action (Smart Retry, WhatsApp Nudge, Payment Link). | Autonomous |
| **`RECOMMEND_FOR_APPROVAL`** | Amount $\ge \text{INR } 50,000$, or low model confidence ($P < 0.45$). | Queues transaction for operator review with full feature attribution and risk summary. | Human-in-the-Loop (`/approve`, `/reject`) |
| **`BLOCK`** | Do-Not-Contact active, contact limits exceeded, consecutive failures $\ge 3$, or $\text{ENV} \le 0$. | Terminates recovery workflow, records audit event, and logs specific guardrail constraint violation. | Non-Intervention |

---

## 5. Candidate Action Space & Guardrail Rules

### 5.1 Action Catalog and Cost Matrix

| Action | Channel Cost | Description | Typical Use Case |
| :--- | :--- | :--- | :--- |
| `Retry Immediately` | INR 1.00 | Immediate payment gateway authorization retry. | Transient network timeouts, gateway downtime. |
| `Retry Delay 6h` | INR 1.00 | Scheduled retry after a 6-hour cooldown. | Bank rate limits, temporary system maintenance. |
| `Retry Delay 18h` | INR 1.00 | Scheduled retry aligned with end-of-day banking windows. | Insufficient funds, salary cycle alignments. |
| `Personalized Email` | INR 0.20 | Low-friction email notification with context. | First-time failures, high-engagement users. |
| `WhatsApp Nudge` | INR 0.50 | High-visibility direct WhatsApp notification. | Urgent recovery, mobile-first payment methods. |
| `Payment Method Update` | INR 25.00 | Razorpay payment link requesting new payment instrument. | Expired cards, permanently blocked accounts. |
| `Incentive Offer` | INR 50.00+ | Discount or fee waiver (bounded at 5% or max INR 500). | Price-sensitive churn risks, high-AOV customers. |
| `Human Escalation` | INR 150.00 | High-touch account manager or concierge outreach. | Strategic Enterprise accounts, high-value contracts. |
| `Stop Intervention` | INR 0.00 | Explicit decision to cease recovery outreach. | Hard policy blocks, negative Expected Net Value. |

### 5.2 Deterministic Safety Rules

1. **Safety Override**: If `do_not_contact == True`, all actions except `Stop Intervention` are strictly blocked.
2. **Fatigue Velocity Caps**: If `contacts_24h >= 2` or `contacts_7d >= 5`, all customer outreach channels are disabled.
3. **Failure History Threshold**: If `consecutive_failures >= 3`, automated gateway retries are blocked to prevent bank account flagging.
4. **Instrument Compatibility**: `Expired Card` failures strictly prohibit automated retries (which have 0% success probability) and mandate instrument update flows.
5. **High-Value Governance**: Transactions $\ge \text{INR } 50,000$ cannot be auto-executed unless confidence $P \ge 0.85$, preventing unauthorized financial incentives or aggressive retries on enterprise balances.

---

## 6. Empirical Validation and Benchmark Results

### 6.1 Scientific Evaluation Protocol
* **Chronological Customer-Grouped Split**: 70% Train, 15% Validation, 15% Test. Ensures zero lookahead leakage and prevents customer overlap across partitions.
* **Paired Counterfactual Simulation**: Evaluated on $N = 2,000$ transactions using Common Random Numbers (CRN) for variance reduction.
* **Bootstrap Uncertainty Estimation**: 500-iteration paired bootstrap resampling computing empirical 95% Confidence Intervals.

### 6.2 Primary Benchmark Metrics

| Metric | Baseline Policy (Standard Retry) | RecoverIQ Decision Engine | Absolute Lift / Delta | Statistical Significance |
| :--- | :--- | :--- | :--- | :--- |
| **Recovery Rate** | 33.0% | **50.2%** | **+17.2 pp** | 95% CI: [+14.8 pp, +19.6 pp] |
| **Expected Calibration Error (ECE)** | 5.65% (Uncalibrated) | **2.81% (Platt Calibrated)** | **-2.84 pp** | Significant ($p < 0.001$) |
| **Brier Score Loss** | 0.2450 | **0.1889** | **-0.0561** | Lower is better |
| **ROC-AUC Score** | 0.6520 (Logistic) | **0.7505 (Calibrated GBM)** | **+0.0985** | Out-of-sample test split |
| **Interventions Avoided** | 0 (Blind retries) | **24.6% of Cohort** | **+24.6%** | Zero fatigue caused |
| **Campaign Outreach ROI** | Reference Baseline | **24.6x** | **+24.6x** | Net Value / Outreach Cost |

---

## 7. Razorpay Integration & Webhook Gateway

RecoverIQ features native integration with Razorpay Webhook Infrastructure:

```
                          RAZORPAY GATEWAY
                                 │
                 POST /api/webhooks/razorpay
             (Header: X-Razorpay-Signature, Timestamp)
                                 │
                                 ▼
              [ CRYPTOGRAPHIC SIGNATURE VERIFICATION ]
             • HMAC-SHA256 Payload Hash Verification
             • Replay Attack Protection (Timestamp Nonce Verification)
                                 │
                                 ▼
              [ ATOMIC IDEMPOTENT DECISION EXECUTION ]
             • Ingest Error Code (e.g., BAD_REQUEST_ERROR)
             • Map Standard Failure Reason (e.g., Insufficient Funds)
             • Generate Immutable Decision Contract (< 50ms)
                                 │
                                 ▼
              [ DOWNSTREAM INTEGRATION DISPATCH ]
             • Auto-dispatch Razorpay Payment Link (`rzp.io/i/...`)
             • Trigger Scheduled Gateway Retry via Razorpay API
```

---

## 8. Repository Structure

```
RecoverIQ/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── agent.py               # Real-time event activity feed
│   │   │   ├── analytics.py           # Executive KPIs and ROI projections
│   │   │   ├── demo.py                # Deterministic environment seeding
│   │   │   ├── experiments.py         # Counterfactual simulation endpoints
│   │   │   ├── payments.py            # Decision engine and What-If simulator
│   │   │   ├── strategies.py          # Action intelligence breakdown
│   │   │   └── webhooks.py            # Razorpay webhook gateway
│   │   ├── core/
│   │   │   ├── config.py              # Environment configuration & security
│   │   │   ├── database.py            # SQLAlchemy database engine
│   │   │   └── security.py            # API key authentication & HMAC checks
│   │   ├── decision_engine/
│   │   │   ├── evaluator.py           # ENV calculation engine
│   │   │   ├── fatigue.py             # Customer fatigue decay models
│   │   │   └── optimizer.py           # Constrained action selection
│   │   ├── guardrails/
│   │   │   └── engine.py              # Multi-tier deterministic guardrails
│   │   ├── ml/
│   │   │   ├── features.py            # Leakage-free feature pipeline
│   │   │   ├── generator.py           # Latent synthetic environment
│   │   │   └── models.py              # Platt-calibrated HistGradientBoosting
│   │   ├── models/
│   │   │   └── db_models.py           # SQLite / PostgreSQL schema models
│   │   ├── schemas/
│   │   │   └── pydantic_schemas.py    # Strict API contracts & validation
│   │   ├── simulation/
│   │   │   └── engine.py              # Vectorized paired CRN simulator
│   │   └── main.py                    # FastAPI application root
│   ├── tests/                         # Comprehensive Pytest suite (30 tests)
│   └── requirements.txt               # Backend dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AgentAuditFeed.tsx     # Live decision execution timeline
│   │   │   ├── EnterpriseRoiCalculator.tsx # Financial ROI & payback model
│   │   │   ├── ExperimentStudio.tsx   # A/B counterfactual simulation UI
│   │   │   ├── KPIOverview.tsx        # High-level recovery metrics
│   │   │   ├── ModelScienceInspector.tsx # Calibration curves & feature importances
│   │   │   ├── PaymentDetailStudio.tsx # Contract inspector & human approval
│   │   │   ├── PaymentQueue.tsx       # Live scored transaction queue
│   │   │   ├── RazorpayWebhookHub.tsx # Webhook simulator & catalog
│   │   │   ├── RecoveryChart.tsx      # 14-day cumulative recovery cohort
│   │   │   ├── StrategyIntelligence.tsx # Unit economics per recovery action
│   │   │   └── WhatIfSimulator.tsx    # Real-time counterfactual simulator
│   │   ├── services/api.ts            # Typed API client
│   │   └── types/index.ts             # TypeScript definitions
│   └── package.json                   # Frontend dependencies
├── docs/                              # Comprehensive architectural guides
│   ├── ARCHITECTURE.md                # System topology and sequence diagrams
│   ├── MODEL_CARD.md                  # Machine learning model documentation
│   ├── RESPONSIBLE_AI.md              # Fairness, safety, and explainability
│   ├── DECISION_ENGINE.md             # Mathematical optimization formulation
│   ├── EXPERIMENT_METHODOLOGY.md      # Simulation & bootstrap specifications
│   └── DATASET_METHODOLOGY.md         # Synthetic data generation methodology
├── .env.example                       # Sanitized configuration template
└── .gitignore                         # Build and cache ignore definitions
```

---

## 9. Getting Started and Deployment

### 9.1 Prerequisites
* Python 3.10+
* Node.js 18+ and npm
* Git

### 9.2 Environment Configuration

Create a local environment file from the sanitized template:

```bash
cp .env.example .env
```

Key environment variables:
```ini
ENV=development
DATABASE_URL=sqlite:///./recoveriq.db
RECOVERIQ_OPERATOR_KEYS=test_operator_key
RECOVERIQ_ADMIN_KEYS=test_admin_key
RAZORPAY_WEBHOOK_SECRET=test_webhook_secret_key_123
```

### 9.3 Installation & Startup

#### 1. Backend Setup:
```bash
cd backend
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### 2. Frontend Setup:
```bash
cd frontend
npm install
npm run dev
```

The frontend application will be accessible at `http://localhost:5173` and the backend Swagger documentation at `http://127.0.0.1:8000/docs`.

### 9.4 Verification & Automated Testing

Execute the complete test suite covering security, ML feature leakage, guardrails, and decision states:

```bash
pytest backend/tests/ -v
```

Execute frontend TypeScript verification:

```bash
cd frontend
npx tsc --noEmit
```

---

## 10. Technical Documentation Index

For in-depth technical analysis and regulatory audit disclosures, consult the dedicated documentation in [`docs/`](docs/):

* **[Architecture Specifications](docs/ARCHITECTURE.md)**: System sequence diagrams, state machine transitions, and database relational models.
* **[Model Card & Calibration](docs/MODEL_CARD.md)**: Training procedure, hyperparameter configurations, and Platt scaling reliability curves.
* **[Responsible AI & Guardrails](docs/RESPONSIBLE_AI.md)**: Customer fatigue bounds, algorithmic bias mitigation, and human-in-the-loop escalation rules.
* **[Decision Engine Optimization](docs/DECISION_ENGINE.md)**: Complete mathematical derivation of the Expected Net Value objective function.
* **[Experimentation Methodology](docs/EXPERIMENT_METHODOLOGY.md)**: Paired counterfactual simulation design, Common Random Numbers, and bootstrap inference.
* **[Dataset Generation Methodology](docs/DATASET_METHODOLOGY.md)**: Latent synthetic environment physics, payment method distributions, and failure classification schemas.

---

## 11. License

This project is licensed under the Apache 2.0 License. See the `LICENSE` file for details.
