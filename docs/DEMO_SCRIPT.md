# RecoverIQ: 5-Minute Competition Demo Script

## Timing & Stage Breakdown

### 0:00 - 0:45 | The Hook & Problem Framing
- **Presenter**: *"Failed payments cost merchants billions annually. Most recovery tools blindly retry failed cards every 24 hours or spam customers with repetitive links. This causes customer churn, wasted gateway fees, and negative ROI. Meet RecoverIQ: an AI decision engine that answers: Given a failed payment, what is the highest-value action, when should we take it, and is it worth taking?"*
- **Action**: Show Executive Dashboard with live KPIs (Revenue at Risk: ₹2.38L, Incremental Revenue: +₹13.9K, Recovery Rate: 42.9% vs. Baseline 28.4%).

---

### 0:45 - 2:00 | The 4 Hero Scenarios Walkthrough
- **Action**: Click **5-MIN PITCH DEMO** button in navbar.
- **Scenario 1 (PAY-HERO-001 - Smart Delayed Retry)**:
  - *"₹7,499 Insufficient Funds. Instead of an immediate retry that would fail, RecoverIQ selects an 18-hour delay to align with the customer's end-of-day balance refresh. ENV: ₹5,848. Status: AUTO_EXECUTE."*
  - Click **Execute Simulation** to show successful recovery.
- **Scenario 2 (PAY-HERO-002 - Fatigue Guardrail)**:
  - *"₹2,499 Auth Failure. Customer already received 2 messages today. Level 2 Guardrail triggers a hard BLOCK. Status: BLOCK, Selected Action: STOP_INTERVENTION, Cost: ₹0."*
- **Scenario 3 (PAY-HERO-003 - High-Value Escalation)**:
  - *"₹85,000 Enterprise Transaction. Exceeds financial threshold. System assigns RECOMMEND_FOR_APPROVAL for human operator review."*
  - Click **Approve Decision** to show operator approval workflow.
- **Scenario 4 (PAY-HERO-004 - Negative ENV Avoidance)**:
  - *"₹299 Expired Card from a brand-new customer. Outreach costs exceed expected recovery value. System terminates with BLOCK to protect merchant profit margins."*

---

### 2:00 - 3:30 | Paired Counterfactual A/B Experiment Studio
- **Action**: Switch to **A/B Experiment Studio** tab.
- **Presenter**: *"How do we prove this isn't vanity metrics? We run a paired counterfactual experiment with Common Random Numbers on 2,000 identical transactions."*
- **Action**: Click **RUN PAIRED A/B EXPERIMENT**.
- **Presenter**: *"In 50 milliseconds, we see: Baseline Policy recovered 28.4%, while RecoverIQ recovered 46.6% (+18.2% Gross Lift), delivering ₹2.45L in Net Incremental Value with high ROI."*

---

### 3:30 - 4:30 | Strategy Intelligence & Real-Time Agent Feed
- **Action**: Switch to **Strategy Intelligence** to show the Revenue Opportunity Map and Strategy Conversion Matrix.
- **Action**: Switch to **Agent Decision Trace** to show the live immutable event stream (`DECIDE`, `ACT`, `GUARDRAIL`).

---

### 4:30 - 5:00 | Conclusion & Architecture Summary
- **Presenter**: *"RecoverIQ combines mathematical rigor, deterministic fintech guardrails, zero data leakage, and real-time decision contracts. It's ready to plug directly into Razorpay's payment infrastructure."*
