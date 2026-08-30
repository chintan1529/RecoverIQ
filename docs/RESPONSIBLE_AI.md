# Responsible AI & Deterministic Fintech Guardrails

## 1. Core Safety Principles
In financial technology and revenue recovery, purely statistical ML models can make ungrounded, risky, or hostile decisions if left unconstrained (e.g. spamming customers, attempting impossible transactions on expired cards, or executing high-value retries without human oversight).

RecoverIQ enforces **Deterministic Guardrails That Strictly Override Statistical Model Recommendations**.

```
                           AI Model Proposal
                                   │
                                   ▼
         ┌───────────────────────────────────────────────────┐
         │       DETERMINISTIC CONSTRAINT ENGINE             │
         │  (Code-enforced invariants, zero AI bypass)       │
         └───────────────────────────────────────────────────┘
                                   │
         ├── 1. Hard Block (Do Not Contact List) ─────────────► STOP (BLOCK)
         ├── 2. Fatigue Limits (Max 2 in 24h, 5 in 7d) ──────► Filter Feasible Set
         ├── 3. Failure Limit (Max 3 consecutive) ───────────► Stop Automated Retries
         ├── 4. Instrument Suitability (Expired / Technical) ─► Restrict Infeasible Actions
         └── 5. High-Value Escalation (Amount >= ₹50,000) ───► RECOMMEND_FOR_APPROVAL
                                   │
                                   ▼
                       Canonical Decision Contract
```

---

## 2. Guardrail Hierarchy & Constraint Specifications

### Guardrail 1: Do-Not-Contact (DNC) Compliance — Priority Level 1 (Hard Block)
- **Rule**: If `do_not_contact == True`, all outreach, notifications, and automated retries are strictly blocked.
- **Contract Outcome**: `decision_status = "BLOCK"`, `selected_action = "Stop Intervention"`, `execution_status = "NOT_EXECUTED"`, `expected_net_value = 0.00`.
- **Precedence**: Overrides high-value escalation and all positive model propensities.

### Guardrail 2: Customer Fatigue Frequency Caps — Priority Level 2
- **Rule**: A customer cannot receive more than **2 outreach attempts within 24 hours** or **5 outreach attempts within 7 days**.
- **Enforcement**: If limits are reached, all outreach channels (`Personalized Email`, `WhatsApp Nudge`, `Incentive Offer`, `Payment Method Update`) are removed from the feasible set.

### Guardrail 3: Consecutive Failure Limit — Priority Level 3
- **Rule**: If a payment has failed **3 or more consecutive times**, all automated retry actions (`Retry Immediately`, `Retry Delay 6h`, `Retry Delay 18h`) are blocked to prevent triggering card network velocity abuse blocks.

### Guardrail 4: Instrument & Failure Reason Suitability — Priority Level 4
- **Expired Card**: Structurally unrecoverable via automated retry or generic nudges. Only `Payment Method Update` or `Stop Intervention` are feasible.
- **Network / Bank Technical Downtime**: Does not require payment instrument updates (`Payment Method Update` blocked).
- **Insufficient Funds**: Immediate retry is blocked (funds will not replenish in seconds; requires 18h delay or customer notification).

### Guardrail 5: High-Value Financial Escalation — Priority Level 5
- **Rule**: Any transaction with $\text{Amount} \ge ₹50,000$ or low recovery confidence ($P(\text{Recovery}) < 0.60$) requires manual human review.
- **Contract Outcome**: `decision_status = "RECOMMEND_FOR_APPROVAL"`, `approval_required = True`, `execution_status = "PENDING_SIMULATION"`.
- **Operator Actions**:
  - `POST /api/v1/payments/{payment_id}/approve`: Transitions status to `APPROVED`, enabling execution.
  - `POST /api/v1/payments/{payment_id}/reject`: Transitions status to `REJECTED`, permanently disabling execution.

---

## 3. Human-in-the-Loop Operator Governance
1. **Decision Studio Visual Audit**: Operators review the exact feature snapshot, calibrated recovery propensities across all 9 candidate actions, cost breakdown, and reason for escalation.
2. **Deterministic Execution Barriers**: The backend explicitly blocks execution attempts on `REJECTED` payments or unapproved `RECOMMEND_FOR_APPROVAL` decisions with `400 Bad Request`.
3. **Execution Idempotency**: Payments can only be executed once; subsequent execution attempts return the existing execution result without side effects.

---

## 4. Complete Audit Trail & Traceability
Every stage of the decision and execution pipeline produces immutable audit log events (`AgentEvent`):
- `EVENT_INSPECTION`: Pre-decision feature snapshot recording.
- `EVENT_GUARDRAIL_EVALUATION`: Feasible action masking and blocked action logging.
- `EVENT_DECISION_GENERATED`: Canonical `DecisionContract` persistence.
- `EVENT_OPERATOR_REVIEW`: Human operator approval or rejection recording.
- `EVENT_EXECUTION`: Downstream API dispatch (e.g. gateway retry or WhatsApp webhook) recording.
