# Counterfactual Experimentation & Statistical Methodology

> [!IMPORTANT]
> **Synthetic Simulation Benchmark Disclosure**:
> The lift and ROI numbers presented in this methodology (e.g. +16.1 pp gross lift, 206x incremental ROI) are empirical evaluation metrics generated within a controlled `LatentSyntheticEnvironment` simulation where the latent customer response function is parameterized. While Common Random Numbers (CRN) and 500-iteration Paired Bootstrap Resampling ensure rigorous internal statistical validity of the simulation, these results represent **synthetic benchmark evaluations** rather than live merchant production guarantees. Real-world validation requires randomized online champion-challenger traffic routing.

## 1. Executive Summary
RecoverIQ evaluates business impact through **Paired Counterfactual Simulation** using the **Common Random Numbers (CRN)** variance-reduction technique paired with **500-iteration Paired Bootstrap Resampling** to compute empirical 95% Confidence Intervals.

Rather than running naive independent synthetic groups, the engine simulates **both the Standard Retry Schedule Baseline and the Canonical RecoverIQ Decision Policy** on the exact same cohort of failed payment transactions under identical latent customer responsiveness shocks.

---

## 2. Experimental Setup & Policies

### A. Baseline Policy (Standard Industry Retry Schedule)
- **Retry Logic**: Fixed immediate retry + fixed delayed retries (6h, 18h).
- **Communication**: Unpersonalized, static communication without fatigue dampening or customer-state awareness.
- **Constraints**: Ignores customer contact limits, dynamic fatigue penalties, and negative Expected Net Value warnings.

### B. Treatment Policy (Canonical RecoverIQ Engine)
- **Policy Evaluator**: Vectorized execution of `DeterministicConstraintEngine` + `RecoveryPredictorModel` + `evaluate_action_expected_net_value`.
- **Optimization Objective**: For each transaction $i$, selects action $a_i^*$ that maximizes Expected Net Value:
  $$a_i^* = \arg\max_{a \in \mathcal{A}_{\text{feasible}}(i)} \text{ENV}(a \mid \mathbf{x}_i)$$
- **Safety**: Hard blocks on Do-Not-Contact customers, contact caps (2 in 24h, 5 in 7d), failure limit caps ($\le 3$), and human escalation on high-value transactions ($\ge ₹50,000$).

---

## 3. Mathematical Definitions & Metrics

For a cohort of $N$ payment transactions:

### 1. Baseline Recovered Revenue ($R_{\text{base}}$)
$$R_{\text{base}} = \sum_{i=1}^N \text{Amount}_i \cdot \mathbb{I}(\text{Recovered}_{\text{base}, i} = 1)$$

### 2. RecoverIQ Recovered Revenue ($R_{\text{ai}}$)
$$R_{\text{ai}} = \sum_{i=1}^N \text{Amount}_i \cdot \mathbb{I}(\text{Recovered}_{\text{ai}, i} = 1)$$

### 3. Incremental Recovered Revenue ($\Delta R$)
$$\Delta R = R_{\text{ai}} - R_{\text{base}}$$

### 4. Recovery Rate Comparison & Gross Lift (pp)
$$\text{Rate}_{\text{base}} = \frac{1}{N}\sum_{i=1}^N \mathbb{I}(\text{Recovered}_{\text{base}, i} = 1)$$
$$\text{Rate}_{\text{ai}} = \frac{1}{N}\sum_{i=1}^N \mathbb{I}(\text{Recovered}_{\text{ai}, i} = 1)$$
$$\text{Gross Recovery Lift (pp)} = (\text{Rate}_{\text{ai}} - \text{Rate}_{\text{base}}) \times 100$$

### 5. Intervention Costs ($C$) & Net Value ($V$)
$$C_{\text{base}} = \sum_{i=1}^N \text{Cost}(a_{\text{base}, i}), \quad C_{\text{ai}} = \sum_{i=1}^N \text{Cost}(a_{\text{ai}, i})$$
$$V_{\text{base}} = R_{\text{base}} - C_{\text{base}}, \quad V_{\text{ai}} = R_{\text{ai}} - C_{\text{ai}}$$
$$\text{Net Incremental Value } (\Delta V) = V_{\text{ai}} - V_{\text{base}} = \Delta R - (C_{\text{ai}} - C_{\text{base}})$$

### 6. Incremental Return on Investment (ROI)
$$\text{ROI} = \begin{cases} \frac{\Delta R}{C_{\text{ai}} - C_{\text{base}}} & \text{if } C_{\text{ai}} > C_{\text{base}} \\ \text{N/A (Cost Savings With Higher Recovery)} & \text{if } C_{\text{ai}} \le C_{\text{base}} \text{ and } \Delta R > 0 \end{cases}$$

---

## 4. Variance Reduction & Bootstrap 95% Confidence Intervals

### Common Random Numbers (CRN)
To eliminate sample variance when comparing policies, transaction $i$ receives a deterministic latent shock $u_i \sim \mathcal{U}(0, 1)$ shared across both baseline and AI evaluations:
$$\text{Recovered}_{\pi, i} = \mathbb{I}\left(u_i \le P_{\pi, i}\right)$$
This induces positive covariance $\text{Cov}(R_{\text{ai}}, R_{\text{base}}) > 0$, significantly reducing the variance of the incremental estimator:
$$\text{Var}(\Delta R) = \text{Var}(R_{\text{ai}}) + \text{Var}(R_{\text{base}}) - 2\text{Cov}(R_{\text{ai}}, R_{\text{base}})$$

### 500-Iteration Paired Bootstrap Resampling
Confidence intervals are estimated via non-parametric paired bootstrap:
1. For iteration $b = 1, \dots, 500$:
   - Draw sample with replacement $\mathcal{I}^{(b)} = \{i_1, \dots, i_N\}$ from $\{1, \dots, N\}$.
   - Compute paired metrics $\Delta R^{(b)}$, $\text{Lift}_{\text{pp}}^{(b)}$, and $\Delta V^{(b)}$.
2. Empirical 95% Confidence Interval is extracted from the 2.5th and 97.5th percentiles:
   $$\text{CI}_{95}(\theta) = \left[ \theta_{0.025}^*, \theta_{0.975}^* \right]$$

---

## 5. Typical Empirical Simulation Results ($N=1,000$, Seed: 42)

| Metric | Baseline Policy | RecoverIQ Policy | Incremental Difference | 95% Confidence Interval |
|---|---|---|---|---|
| **Recovery Rate** | 35.1% | 51.2% | **+16.1 pp** | [+13.5 pp, +18.7 pp] |
| **Recovered Revenue** | ₹1,980,450 | ₹2,887,200 | **+₹906,750** | [+₹745,200, +₹1,072,400] |
| **Intervention Costs** | ₹14,250 | ₹18,650 | +₹4,400 | — |
| **Net Value** | ₹1,966,200 | ₹2,868,550 | **+₹902,350** | [+₹740,800, +₹1,068,000] |
| **Incremental ROI** | — | — | **206.1x** | — |

---

## 6. Scientific Honesty & Limitations Note
- **Prediction vs Causal Mechanism**: Simulated recovery rates are derived from the action-conditioned model's predicted propensities and the ground-truth synthetic data generator. In actual production deployment, unobserved confounders (e.g. external macroeconomic liquidity shifts) may influence actual conversion. RecoverIQ is designed to be validated in production via randomized holdout A/B champion-challenger traffic routing.
