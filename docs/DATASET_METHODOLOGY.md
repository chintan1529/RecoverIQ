# Synthetic Dataset & Latent Environment Methodology

## 1. Motivation & Problem Statement
Evaluating payment recovery models on simple random synthetic data creates unrealistic recovery dynamics and misleading accuracy. Real-world payment failures exhibit:
- Latent customer willingness to pay (propensity).
- Latent technical vs. balance-driven failure recoverability.
- Action-specific recovery effectiveness modifiers.
- Non-linear fatigue dynamics and channel decay.

To achieve authentic fintech realism, RecoverIQ implements a **3-Layer Latent Environment Generator**.

---

## 2. Mathematical Generative Model

For each synthetic transaction $i$, ground-truth probability of recovery $P(\text{Recovery} \mid \mathbf{x}_i, a)$ is determined by:

$$P(\text{Recovery}) = \sigma\left( L_{\text{customer}} + L_{\text{failure}} + M_{\text{action}}(a) - \Phi_{\text{fatigue}} \right)$$

where $\sigma(z) = \frac{1}{1 + e^{-z}}$ is the standard sigmoid logistic function.

### 2.1 Latent Components

1. **Latent Customer Propensity ($L_{\text{customer}}$)**:
   $$L_{\text{customer}} = 1.2 \cdot \text{engagement} + 0.8 \cdot \text{hist\_recovery\_rate} + 0.05 \cdot \text{tenure\_months} - 0.4 \cdot \text{consecutive\_failures}$$

2. **Latent Failure Recoverability ($L_{\text{failure}}$)**:
   - `Network Timeout`: $+0.80$ (Transient gateway failure; highly recoverable).
   - `Insufficient Funds`: $-0.20$ (Requires customer balance replenish or payday cycle).
   - `Authentication Failed`: $+0.10$ (Recoverable via retry or alternative verification).
   - `Card Limit Exceeded`: $-0.50$ (Requires customer credit limit increase).
   - `Expired Card`: $-1.20$ (Unrecoverable without card detail update).

3. **Action Effectiveness Modifiers ($M_{\text{action}}(a)$)**:
   - **`Retry Delay 18h`**: $+1.20$ on `Insufficient Funds` (matches end-of-day/payday processing).
   - **`Payment Method Update`**: $+1.80$ on `Expired Card`.
   - **`WhatsApp Nudge`**: $+0.90$ on `Authentication Failed` (fast mobile authorization).
   - **`Retry Immediately`**: $+1.10$ on `Network Timeout` (transient error cleared).
   - **`Stop Intervention`**: $-\infty$ ($P(\text{Recovery}) = 0.0$, zero outreach cost).

4. **Dynamic Customer Fatigue Penalty ($\Phi_{\text{fatigue}}$)**:
   $$\Phi_{\text{fatigue}} = 0.6 \cdot \text{contacts\_24h} + 0.25 \cdot \text{contacts\_7d}$$

---

## 3. Dataset Generation & Splitting

- **Sample Size**: 2,000 baseline transactions seeded across multiple customer segments (Enterprise, Mid-Market, SMB).
- **Chronological Time-Aware Split**:
  - Early 70% ($N = 1,400$) $\rightarrow$ Training Set.
  - Middle 15% ($N = 300$) $\rightarrow$ Validation Set.
  - Late 15% ($N = 300$) $\rightarrow$ Out-of-Time Test Set.
- **Strict Information Barrier**: Data generation strictly separates pre-decision features and post-action observed outcomes.
