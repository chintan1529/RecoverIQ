from typing import Dict, Any

def calculate_customer_fatigue_score(
    contacts_24h: int,
    contacts_7d: int,
    consecutive_failures: int,
    hours_since_last_contact: float
) -> float:
    """
    Calculates normalized Customer Fatigue Score [0.0, 1.0].
    """
    recent_factor = min(contacts_24h / 2.0, 1.0) * 0.4
    weekly_factor = min(contacts_7d / 5.0, 1.0) * 0.3
    failure_factor = min(consecutive_failures / 3.0, 1.0) * 0.2
    recency_factor = max(0.0, (24.0 - hours_since_last_contact) / 24.0) * 0.1

    score = recent_factor + weekly_factor + failure_factor + recency_factor
    return float(min(score, 1.0))


def compute_action_fatigue_penalty(action: str, contacts_24h: int, contacts_7d: int) -> float:
    """
    Computes action-specific fatigue penalty in INR.
    - Stop Intervention: ₹0.00
    - Retry actions (invisible to customer): ₹0.00
    - Personalized Email: ₹5 per 7d contact
    - WhatsApp Nudge: ₹25 per 7d contact + ₹50 if contacted in last 24h
    - Incentive Offer: ₹10 per 7d contact
    """
    if action in ["Stop Intervention", "Retry Immediately", "Retry Delay 6h", "Retry Delay 18h"]:
        return 0.00
    elif action == "Personalized Email":
        penalty = float(contacts_7d * 8.00)
        if contacts_24h >= 1:
            penalty += 25.00
        return penalty
    elif action == "WhatsApp Nudge":
        penalty = float(contacts_7d * 25.00)
        if contacts_24h >= 1:
            penalty += 50.00
        return penalty
    elif action == "Incentive Offer":
        return float(contacts_7d * 10.00)
    elif action == "Payment Method Update":
        penalty = float(contacts_7d * 15.00)
        if contacts_24h >= 1:
            penalty += 50.00
        return penalty
    elif action == "Human Escalation":
        return float(contacts_7d * 5.00)
    return 0.00
