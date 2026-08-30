# Model Card: Action-Conditioned Recovery Predictor

## 1. Model Details
- **Model Name**: `RecoverIQ Action-Conditioned Recovery Predictor`
- **Model Version**: `recovery_gbm_v1.1`
- **Model Architecture**: HistGradientBoostingClassifier (Histogram-based Gradient Boosted Decision Trees)
- **Probability Calibration**: CalibratedClassifierCV with Sigmoid (Platt Scaling) cross-validated on Training Split ($K=3$)
- **Feature Importance Method**: Permutation Feature Importance computed strictly on Observational Pre-Decision Features on the Validation Split ($N=664$, 5 repeats, scoring: ROC-AUC)
- **Baseline Model**: L2-Regularized Logistic Regression with StandardScaler
- **Input Features**: $\mathbf{x}_{\text{pre}} \in \mathbb{R}^d$ (pre-decision payment and customer features) + $a \in \mathcal{A}$ (candidate action)
- **Target Output**: Calibrated $P(\text{Recovery} = 1 \mid \mathbf{x}_{\text{pre}}, a) \in [0.01, 0.99]$

---

## 2. Intended Use & Scope
- **Primary Use**: Predicts the calibrated probability that a failed transaction will be successfully recovered if a specific candidate intervention action $a$ is executed under context $\mathbf{x}_{\text{pre}}$.
- **Downstream Consumer**: RecoverIQ Expected Net Value (ENV) Optimizer and Deterministic Constraint Engine.
- **Out of Scope**: Primary authorization, credit underwriting, fraud scoring, or automated debt collection.

---

## 3. Dataset Partitioning & Splitting Strategy (Leakage-Free)
To prevent temporal and customer-level data leakage, records are split using **Customer Group-Aware Chronological Splitting**:
- **Total Population**: 5,000 synthetic transaction records (Seed: 42)
- **Training Split (70% Customers)**: 3,735 records — FeaturePipeline encoder is fitted SOLELY on this partition. Fits baseline Logistic Regression and primary HistGradientBoostingClassifier with 3-fold cross-validated Platt scaling.
- **Validation Split (15% Customers)**: 664 records — used strictly for permutation feature importance calculation on observational predictors.
- **Test Holdout Split (15% Customers)**: 601 records — untouched out-of-time holdout with zero customer overlap from training, evaluated strictly once for unbiased benchmark metrics.
- **Positive Class Prevalence**: 34.9% (Test Set)

---

## 4. Live Benchmark Performance Metrics (Evaluated on Untouched Test Set $N=601$)

*Reproducible live command: `python backend/app/evaluation/evaluate_model.py`*

| Metric | Baseline Logistic Regression | Primary (Uncalibrated) | RecoverIQ (Calibrated) | Benchmark Significance |
|---|---|---|---|---|
| **ROC-AUC** | 0.7694 | 0.7414 | **0.7497** | Measures rank-order discrimination across candidate actions |
| **PR-AUC** | 0.6086 | 0.5585 | **0.5806** | Precision-Recall trade-off under class imbalance |
| **Brier Score** (Lower is better) | 0.1823 | 0.1973 | **0.1889** | Measures probability calibration error |
| **Expected Calibration Error (ECE)** | 0.0628 | 0.0712 | **0.0316** | Mean discrepancy between confidence and empirical accuracy (3.16%) |
| **F1 Score** (Threshold = 0.50) | 0.5722 | 0.5263 | **0.4831** | Harmonic mean of precision and recall |
| **Precision** | 0.6108 | 0.5556 | **0.5890** | Positive predictive value |
| **Recall** | 0.5381 | 0.5000 | **0.4095** | Sensitivity / recovery identification rate |

### Brier Score Improvement via Calibration
- Calibration improves the primary model Brier score from **0.1973** to **0.1889** (**+4.25% calibration gain**) and drops Expected Calibration Error from **0.0712** (7.12%) to **0.0316** (3.16%), ensuring predicted probabilities accurately reflect empirical recovery rates.

### Test Set Confusion Matrix (Threshold = 0.50, N=601)
```
                  Predicted Negative    Predicted Positive
Actual Failed             331                   60          (True Negatives: 331, False Positives: 60)
Actual Recovered          124                   86          (False Negatives: 124, True Positives: 86)
```

---

## 5. Permutation Feature Importance (Validation Set Observational Signals)

*Methodological Note: `candidate_action` is a treatment assignment variable and has been excluded from observational feature ranking to eliminate treatment-label conflation.*

| Rank | Observational Feature / Signal | Importance Score | Share (%) | Description |
|---|---|---|---|---|
| 1 | `failure_reason_Expired Card` | 0.5901 | 59.0% | Expired cards are structurally unrecoverable via retries |
| 2 | `failure_reason_Network Timeout` | 0.1063 | 10.6% | Transient technical failures have high recovery potential |
| 3 | `customer_tenure_months` | 0.0826 | 8.3% | Established merchant customers show higher recovery commitment |
| 4 | `fatigue_index` | 0.0565 | 5.7% | Composite frequency of recent contacts & failures |
| 5 | `failure_reason_Insufficient Funds` | 0.0392 | 3.9% | Liquidity window timing alignment |
| 6 | `amount` | 0.0356 | 3.6% | Ticket size sensitivity |
| 7 | `contacts_7d` | 0.0251 | 2.5% | Trailing contact density |
| 8 | `failure_reason_Authentication Failed` | 0.0179 | 1.8% | 3D-Secure / AutoPay mandate friction |

---

## 6. Pre-Decision Feature Schema & Leakage Defense

The system enforces automated barriers:
1. `assert_no_feature_leakage`: Prohibits post-decision outcome fields (`actual_outcome`, `recovered_amount`, `ground_truth_p`) from entering feature pipelines.
2. `RecoveryFeaturePipeline.fit`: Encoder fits strictly on training partition records.
3. `Customer Grouped Split`: Guarantees no customer ID in training appears in the test split.
