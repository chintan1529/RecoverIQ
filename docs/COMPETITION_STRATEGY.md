# Razorpay AI Builder 2026: Competition Strategy & Judge Q&A

## 1. Product Value Proposition & Razorpay Strategic Fit
Razorpay processes billions of dollars in gross merchandise value (GMV) across subscriptions, e-commerce, and SaaS. A 1% lift in payment recovery rate translates to tens of millions of dollars in recovered merchant GMV.

### Why RecoverIQ Wins:
1. **Decision Intelligence over Chatbots**: Solves the fundamental fintech optimization problem: *"Which candidate action maximizes Expected Net Value after accounting for channel costs, customer fatigue churn risk, and regulatory guardrails?"*
2. **Deterministic Guardrails That Override ML**: Financial institutions demand code-level certainty; our 5-tier guardrail engine guarantees hard blocks, contact frequency limits, and approval policies are mathematically unbypassable.
3. **Paired Counterfactual Testing with Bootstrap 95% CIs**: Directly proves causal business lift and incremental revenue using Common Random Numbers (CRN) and 500-iteration bootstrap confidence intervals.
4. **Calibrated ML & Zero Data Leakage**: Calibrated via Platt Scaling (Brier Score: 0.1908, ECE: 0.0281) with automated pre-decision barrier checks.
5. **Drop-in Middleware**: Consumes standard payment failure payloads and outputs deterministic Decision Contracts.

---

## 2. Anticipated Judge Q&A & Defenses

### Q1: "How do you ensure the ML model probabilities are trustworthy for financial decisions?"
> **Answer**: "Raw gradient boosted classifiers often produce overconfident probabilities at the extremes. RecoverIQ employs `CalibratedClassifierCV` with cross-validated Platt scaling (Sigmoid, $K=3$) on chronological splits. This reduces the Brier score to 0.1908 and achieves an Expected Calibration Error (ECE) of 0.0281. Because Expected Net Value directly multiplies $P(\text{Recovery}) \times \text{Amount}$, calibration is essential to prevent financial over-intervention."

### Q2: "How does RecoverIQ avoid data leakage in its ML models?"
> **Answer**: "We enforce an immutable Pre-Decision Feature Schema (`PreDecisionFeatures`) that only accepts data available prior to action execution (amount, customer tenure, past recovery rate, failure code, contact counts). We maintain automated pytest assertions (`test_assert_no_feature_leakage`) that fail any build if post-action fields like `recovered_amount` or `actual_outcome` enter feature transformers."

### Q3: "Why do you use Expected Net Value instead of just maximizing recovery probability?"
> **Answer**: "Optimizing solely for $P(\text{recovery})$ leads to economically destructive behavior—such as deploying a ₹150 human escalation or spamming WhatsApp nudges for a ₹199 transaction with low recovery chance. ENV explicitly subtracts channel costs, discount incentives, and customer fatigue churn risk, ensuring every action is net profitable."

### Q4: "How does the counterfactual simulation work, and why should we trust the lift numbers?"
> **Answer**: "Rather than running naive uncoupled groups, our simulation engine uses **Common Random Numbers (CRN)** to evaluate both the baseline retry schedule and the RecoverIQ decision policy on the exact same cohort under identical latent customer response shocks. We then run **500-iteration paired bootstrap resampling** to output empirical 95% Confidence Intervals for gross lift, incremental revenue, and net value. On $N=1,000$, RecoverIQ demonstrates a statistically significant gross lift of +16.1 pp (95% CI: [+13.5 pp, +18.7 pp])."

### Q5: "What happens when an action is BLOCKED or requires Human Approval?"
> **Answer**: "In RecoverIQ:
> - A `BLOCK` status (e.g. Do-Not-Contact or negative ENV) immediately sets `execution_status = NOT_EXECUTED`, `selected_action = 'Stop Intervention'`, and `ENV = ₹0.00`, with zero costs incurred.
> - A `RECOMMEND_FOR_APPROVAL` status (high-value $\ge ₹50,000$ or low confidence) pauses execution in `PENDING_SIMULATION` until an operator issues a signed approval (`/approve`) or rejection (`/reject`). Execution barriers strictly prevent unapproved or rejected payments from dispatching."

### Q6: "How do you handle feature importance without fabricating explanations?"
> **Answer**: "We calculate true **Permutation Feature Importance** on the out-of-sample validation split ($N=750$, 5 repeats, ROC-AUC scoring). Signals like `failure_reason_Expired Card` (32.6% share) and `candidate_action_Stop Intervention` (26.4% share) genuinely drive model discrimination. The LLM is used solely to generate natural language operator summaries and customer drafts, with structured fact validation that falls back to deterministic text if any contradiction is detected."
