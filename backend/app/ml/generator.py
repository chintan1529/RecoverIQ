import random
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Any
from datetime import datetime, timedelta

# List of supported actions
ACTIONS = [
    "Retry Immediately",
    "Retry Delay 6h",
    "Retry Delay 18h",
    "Payment Method Update",
    "Personalized Email",
    "WhatsApp Nudge",
    "Incentive Offer",
    "Human Escalation",
    "Stop Intervention"
]

FAILURE_REASONS = [
    "Insufficient Funds",
    "Expired Card",
    "Network Timeout",
    "Authentication Failed",
    "Bank Downtime"
]

PAYMENT_METHODS = ["UPI", "Card", "NetBanking", "AutoPay"]
SEGMENTS = ["SMB", "MidMarket", "Enterprise"]

class LatentSyntheticEnvironment:
    """
    Layer 1 Ground-Truth Simulation Engine.
    Generates realistic synthetic payment failure data with calibrated latent parameters.
    THE ML MODEL NEVER SEES THIS CLASS OR ITS INTERNAL FORMULAS DIRECTLY.
    """
    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)

    def _get_latent_customer_propensity(self, tenure_months: int, engagement: float, seg: str) -> float:
        seg_boost = {"Enterprise": 0.15, "MidMarket": 0.05, "SMB": 0.0}[seg]
        tenure_factor = min(tenure_months / 36.0, 1.0) * 0.20
        return 0.10 + tenure_factor + (engagement * 0.25) + seg_boost

    def _get_latent_failure_recoverability(self, failure_reason: str) -> float:
        base_map = {
            "Network Timeout": 0.70,
            "Bank Downtime": 0.65,
            "Insufficient Funds": 0.45,
            "Authentication Failed": 0.40,
            "Expired Card": 0.10
        }
        return base_map.get(failure_reason, 0.40)

    def _get_action_effectiveness_modifier(self, failure_reason: str, action: str, lc: float = 0.5) -> float:
        if action == "Stop Intervention":
            # Natural/passive recovery probability (e.g. organic self-resolution without intervention)
            return -1.20 if failure_reason != "Expired Card" else -2.50
        
        if failure_reason == "Network Timeout":
            if action == "Retry Immediately": return 0.40
            if "Retry Delay" in action: return 0.20
            if action in ["WhatsApp Nudge", "Personalized Email"]: return -0.20
        elif failure_reason == "Insufficient Funds":
            if action == "Retry Delay 18h": return 0.50  # Payday end-of-day timing boost
            if action == "Retry Delay 6h": return 0.20
            if action == "Retry Immediately": return -0.40  # Immediate retry fails on empty balance
            if action in ["WhatsApp Nudge", "Personalized Email"]: return -0.30
            if action == "Incentive Offer": return 0.15
        elif failure_reason == "Expired Card":
            if action == "Payment Method Update":
                return 0.40 if lc >= 0.35 else -0.50  # Unengaged new customers do not update expired card
            if "Retry" in action: return -0.80  # Retrying expired card is unrecoverable
            if action in ["WhatsApp Nudge", "Personalized Email"]: return -0.30
        elif failure_reason == "Authentication Failed":
            if action in ["WhatsApp Nudge", "Personalized Email"]: return 0.35
            if action == "Payment Method Update": return 0.20
        elif failure_reason == "Bank Downtime":
            if action in ["Retry Delay 6h", "Retry Delay 18h"]: return 0.40
            if action == "Retry Immediately": return -0.30
        
        if action == "Human Escalation": return 0.35
        return 0.0

    def compute_ground_truth_p_recovery(self, row: Dict[str, Any], action: str) -> float:
        lc = self._get_latent_customer_propensity(
            row["customer_tenure_months"], row["engagement_score"], row["customer_segment"]
        )
        lf = self._get_latent_failure_recoverability(row["failure_reason"])
        ma = self._get_action_effectiveness_modifier(row["failure_reason"], action, lc=lc)
        
        fatigue_penalty = (row["contacts_7d"] * 0.06) + (row["consecutive_failures"] * 0.08)
        
        # Logit calculation centered around realistic 0.30 - 0.78
        raw_score = (lc + lf + ma) - fatigue_penalty
        
        # Calibrated Sigmoid
        p = 1.0 / (1.0 + np.exp(-(raw_score - 0.85) * 2.4))
        return float(np.clip(p, 0.03, 0.92))

    def sample_actual_outcome(self, p_recovery: float) -> str:
        return "SUCCESS" if random.random() < p_recovery else "FAILED"


def generate_synthetic_dataset(n_samples: int = 5000, seed: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generates two separated datasets:
    1. PreDecisionFeatures (for ML training & inference)
    2. PostActionOutcomes (actual simulated ground-truth outcomes across candidate actions)
    """
    env = LatentSyntheticEnvironment(seed=seed)
    random.seed(seed)
    np.random.seed(seed)

    pre_decision_records = []
    post_action_records = []

    start_date = datetime.now() - timedelta(days=90)

    for i in range(1, n_samples + 1):
        pid = f"PAY-{seed}-{i:05d}"
        cid = f"CUST-{random.randint(1000, 9999)}"
        amount = round(float(np.random.exponential(scale=3500) + 150), 2)
        tenure = random.randint(1, 48)
        seg = random.choices(SEGMENTS, weights=[0.6, 0.3, 0.1])[0]
        engagement = round(random.uniform(0.2, 0.98), 2)
        hist_rec = round(random.uniform(0.1, 0.9), 2)
        pm = random.choice(PAYMENT_METHODS)
        f_reason = random.choice(FAILURE_REASONS)
        c_24h = random.choices([0, 1, 2, 3], weights=[0.5, 0.3, 0.15, 0.05])[0]
        c_7d = c_24h + random.choices([0, 1, 2, 3, 4], weights=[0.4, 0.3, 0.15, 0.1, 0.05])[0]
        consec_fail = random.choices([1, 2, 3, 4], weights=[0.6, 0.25, 0.1, 0.05])[0]
        hrs_contact = round(random.uniform(1.0, 168.0), 1)
        dnc = True if random.random() < 0.02 else False
        created_dt = start_date + timedelta(minutes=i * 25)

        # For action-conditioned ML dataset, sample one random action for training row
        sampled_action = random.choice(ACTIONS)

        base_dict = {
            "payment_id": pid,
            "customer_id": cid,
            "amount": amount,
            "currency": "INR",
            "payment_method": pm,
            "card_type": "Visa" if pm == "Card" else None,
            "failure_reason": f_reason,
            "failure_code": f"ERR_{f_reason.upper().replace(' ', '_')}",
            "customer_tenure_months": tenure,
            "customer_segment": seg,
            "engagement_score": engagement,
            "historical_recovery_rate": hist_rec,
            "contacts_24h": c_24h,
            "contacts_7d": c_7d,
            "consecutive_failures": consec_fail,
            "hours_since_last_contact": hrs_contact,
            "do_not_contact": dnc,
            "candidate_action": sampled_action,
            "created_at": created_dt
        }

        # Calculate ground truth probability & actual outcome
        p_rec = env.compute_ground_truth_p_recovery(base_dict, sampled_action)
        outcome = env.sample_actual_outcome(p_rec)
        rec_amt = amount if outcome == "SUCCESS" else 0.0
        time_to_rec = round(random.uniform(0.5, 24.0), 1) if outcome == "SUCCESS" else 0.0

        pre_decision_records.append(base_dict)
        post_action_records.append({
            "outcome_id": f"OUT-{pid}",
            "payment_id": pid,
            "selected_action": sampled_action,
            "ground_truth_p": p_rec,
            "actual_outcome": outcome,
            "recovered_amount": rec_amt,
            "actual_cost": 1.00,
            "time_to_recovery_hours": time_to_rec,
            "recorded_at": created_dt + timedelta(hours=time_to_rec)
        })

    df_pre = pd.DataFrame(pre_decision_records)
    df_post = pd.DataFrame(post_action_records)

    return df_pre, df_post


def get_hero_pitch_scenarios() -> List[Dict[str, Any]]:
    """
    Produces the 4 Seeded Hero Pitch Scenarios.
    """
    return [
        {
            "scenario_id": "SCENARIO_1",
            "name": "Smart Delayed Retry (High ROI)",
            "description": "₹7,499 Insufficient Funds payment from a 24-month customer. Immediate retry fails, but 18h delayed retry matches end-of-day payday window.",
            "payment_id": "PAY-HERO-001",
            "customer_id": "CUST-HERO-1001",
            "customer_name": "Aditya Sharma",
            "customer_email": "aditya.sharma@example.com",
            "amount": 7499.00,
            "payment_method": "AutoPay",
            "failure_reason": "Insufficient Funds",
            "failure_code": "ERR_INSUFFICIENT_FUNDS",
            "customer_tenure_months": 24,
            "customer_segment": "MidMarket",
            "engagement_score": 0.85,
            "historical_recovery_rate": 0.75,
            "contacts_24h": 0,
            "contacts_7d": 1,
            "consecutive_failures": 1,
            "hours_since_last_contact": 48.0,
            "do_not_contact": False
        },
        {
            "scenario_id": "SCENARIO_2",
            "name": "Fatigue Guardrail (Responsible AI)",
            "description": "₹2,499 Auth Failed payment. Customer has 2 recent contacts and 3 consecutive failures. Customer contact constraint blocks outreach, forcing STOP_INTERVENTION.",
            "payment_id": "PAY-HERO-002",
            "customer_id": "CUST-HERO-1002",
            "customer_name": "Priya Patel",
            "customer_email": "priya.patel@example.com",
            "amount": 2499.00,
            "payment_method": "Card",
            "failure_reason": "Authentication Failed",
            "failure_code": "ERR_AUTH_FAILED",
            "customer_tenure_months": 6,
            "customer_segment": "SMB",
            "engagement_score": 0.40,
            "historical_recovery_rate": 0.30,
            "contacts_24h": 2,
            "contacts_7d": 5,
            "consecutive_failures": 3,
            "hours_since_last_contact": 3.5,
            "do_not_contact": False
        },
        {
            "scenario_id": "SCENARIO_3",
            "name": "High-Value Human Escalation (Risk-Aware)",
            "description": "₹85,000 Network Timeout failure. High transaction value triggers financial escalation rule, setting state to RECOMMEND_FOR_APPROVAL.",
            "payment_id": "PAY-HERO-003",
            "customer_id": "CUST-HERO-1003",
            "customer_name": "Rajesh Verma (Enterprise)",
            "customer_email": "r.verma@enterprise-tech.in",
            "amount": 85000.00,
            "payment_method": "NetBanking",
            "failure_reason": "Network Timeout",
            "failure_code": "ERR_NETWORK_TIMEOUT",
            "customer_tenure_months": 36,
            "customer_segment": "Enterprise",
            "engagement_score": 0.92,
            "historical_recovery_rate": 0.88,
            "contacts_24h": 0,
            "contacts_7d": 0,
            "consecutive_failures": 1,
            "hours_since_last_contact": 72.0,
            "do_not_contact": False
        },
        {
            "scenario_id": "SCENARIO_4",
            "name": "AI Chooses Not to Recover (Negative ENV)",
            "description": "₹299 Expired Card payment from a new 1-month customer. Outreach cost (₹25) exceeds expected recovery (₹10). Decision engine sets decision_status = BLOCK, selected_action = STOP_INTERVENTION, execution_status = NOT_EXECUTED.",
            "payment_id": "PAY-HERO-004",
            "customer_id": "CUST-HERO-1004",
            "customer_name": "Sneha Gupta",
            "customer_email": "sneha.g@example.com",
            "amount": 299.00,
            "payment_method": "Card",
            "failure_reason": "Expired Card",
            "failure_code": "ERR_EXPIRED_CARD",
            "customer_tenure_months": 1,
            "customer_segment": "SMB",
            "engagement_score": 0.15,
            "historical_recovery_rate": 0.05,
            "contacts_24h": 1,
            "contacts_7d": 2,
            "consecutive_failures": 2,
            "hours_since_last_contact": 12.0,
            "do_not_contact": False
        }
    ]
