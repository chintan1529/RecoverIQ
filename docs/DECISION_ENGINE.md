# RecoverIQ Decision Engine & Optimization Specification

## 1. Architectural Overview
The **RecoverIQ Decision Engine** bridges predictive machine learning with deterministic operational guardrails and financial mathematical optimization.

```
Incoming Failed Payment
         │
         ▼
[1. Deterministic Constraint Engine]
 ├── Hard Blocks (Do-Not-Contact)
 ├── Fatigue Limits (24h: 2, 7d: 5)
 ├── Failure Limit (Consecutive: 3)
 └── Channel Suitability Masks (e.g. Expired Card -> PMU only)
         │
         ▼
    Feasible Action Set $\mathcal{A}_{\text{feasible}} \subseteq \mathcal{A}$
         │
         ▼
[2. Action-Conditioned Probability Scorer]
 └── Evaluates Calibrated $P(\text{Recovery} \mid \mathbf{x}, a)$ for all $a \in \mathcal{A}$
         │
         ▼
[3. Expected Net Value (ENV) Evaluator]
 └── Computes $\text{ENV}(a) = P(a) \cdot \text{Amount} - C_{\text{int}}(a) - C_{\text{inc}}(a) - \text{Pen}_{\text{fatigue}}(a) - \text{Pen}_{\text{risk}}(a)$
         │
         ▼
[4. Optimization & Escalation Policy]
 ├── $a^* = \arg\max_{a \in \mathcal{A}_{\text{feasible}}} \text{ENV}(a)$
 ├── If Hard Block OR $\text{ENV}(a^*) \le 0$: `decision_status = BLOCK` ($a^* = \text{Stop Intervention}$)
 ├── If Amount $\ge ₹50,000$ OR $P(a^*) < 0.60$: `decision_status = RECOMMEND_FOR_APPROVAL`
 └── Else: `decision_status = AUTO_EXECUTE`
         │
         ▼
[5. Canonical DecisionContract]
 └── Immutable JSON payload + candidate_scores_json persisted to database
```

---

## 2. Canonical Expected Net Value (ENV) Formula

For a candidate action $a \in \mathcal{A}$ on a payment of $\text{Amount}$ INR:

$$\text{ENV}(a) = P(\text{Recovery} \mid \mathbf{x}, a) \cdot \text{Amount} - C_{\text{intervention}}(a) - C_{\text{incentive}}(a) - \text{Penalty}_{\text{fatigue}}(a) - \text{Penalty}_{\text{risk}}(a)$$

### Stop Intervention Invariant:
$$\text{ENV}(\text{"Stop Intervention"}) \equiv 0.00 \quad (\text{Cost} = 0, \text{Incentive} = 0, \text{Penalties} = 0)$$

---

## 3. Intervention Cost Matrix ($C_{\text{intervention}}$)

*Defined in `backend/app/core/config.py`:*

| Action Name | Type | Base Cost (INR) | Operational Rationale |
|---|---|---|---|
| **Stop Intervention** | Passive | ₹0.00 | Passive baseline; zero outreach |
| **Retry Immediately** | Automated | ₹1.00 | Gateway transaction processing fee |
| **Retry Delay 6h** | Automated | ₹1.00 | Gateway transaction processing fee |
| **Retry Delay 18h** | Automated | ₹1.00 | Gateway transaction processing fee |
| **Personalized Email** | Outreach | ₹0.20 | Transactional email delivery service fee |
| **WhatsApp Nudge** | Outreach | ₹0.50 | Business API message fee |
| **Incentive Offer** | Outreach + Promo | ₹5.00 | Base delivery fee + dynamic promo discount |
| **Payment Method Update** | Outreach + KYC | ₹25.00 | Secure instrument update link + tokenization fee |
| **Human Escalation** | Manual Ops | ₹150.00 | Dedicated customer support operator handling cost |

---

## 4. Dynamic Costs & Penalties

### A. Incentive Cost ($C_{\text{incentive}}$)
For `Incentive Offer`, a 5% discount is offered to incentivize recovery on transactions $\ge ₹1,000$, capped at ₹500:
$$C_{\text{incentive}} = \min(0.05 \cdot \text{Amount}, 500.0)$$
For all other actions, $C_{\text{incentive}} = 0.0$.

### B. Action Fatigue Penalty ($\text{Penalty}_{\text{fatigue}}$)
Quantifies long-term customer churn risk caused by excessive outreach:
- **Stop Intervention / Retries**: ₹0.00
- **Personalized Email**: $8.0 \cdot \text{contacts}_{\text{7d}} + 25.0 \cdot \mathbb{I}(\text{contacts}_{\text{24h}} \ge 1)$
- **WhatsApp Nudge**: $25.0 \cdot \text{contacts}_{\text{7d}} + 50.0 \cdot \mathbb{I}(\text{contacts}_{\text{24h}} \ge 1)$
- **Payment Method Update**: $15.0 \cdot \text{contacts}_{\text{7d}} + 50.0 \cdot \mathbb{I}(\text{contacts}_{\text{24h}} \ge 1)$
- **Incentive Offer**: $10.0 \cdot \text{contacts}_{\text{7d}}$
- **Human Escalation**: $5.0 \cdot \text{contacts}_{\text{7d}}$

### C. High-Value Risk Penalty ($\text{Penalty}_{\text{risk}}$)
For transactions $\ge ₹50,000$, unapproved immediate retries incur a ₹50.00 risk penalty to prevent compounding gateway failure rates.

---

## 5. Candidate Score Persistence Pipeline
To guarantee complete visual transparency, the candidate scores survive end-to-end without loss:
1. **DecisionOptimizerEngine** scores all 9 candidate actions $\rightarrow$ `List[CandidateActionScore]`.
2. **DecisionContract** packages scores into `candidate_scores: List[CandidateActionScore]`.
3. **Database** serializes scores to `PaymentDB.candidate_scores_json` via JSON column.
4. **API Layer** deserializes to `DecisionContract` schema with exact probabilities, costs, and ENV.
5. **Frontend Decision Studio** renders interactive comparison table directly from persisted candidate scores with zero client-side recalculation.
