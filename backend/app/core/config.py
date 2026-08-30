import os
from dataclasses import dataclass, field
from typing import Dict

@dataclass
class Settings:
    PROJECT_NAME: str = "RecoverIQ — AI Revenue Recovery Decision Engine"
    API_V1_STR: str = "/api"
    
    # Environment & Database
    ENV: str = os.getenv("ENV", "development")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./recoveriq.db")
    
    # LLM & Gateway Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-2.5-flash")
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")
    RAZORPAY_WEBHOOK_SECRET: str = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")

    # Security & API Key Authentication (Strictly Environment-Driven, No Insecure Defaults)
    OPERATOR_API_KEYS: str = os.getenv("RECOVERIQ_OPERATOR_KEYS", "")
    ADMIN_API_KEYS: str = os.getenv("RECOVERIQ_ADMIN_KEYS", "")

    # Model & Policy Versions
    MODEL_VERSION: str = "recovery_gbm_v1.0"
    POLICY_VERSION: str = "policy_2026_v1"
    
    # Financial & Risk Thresholds
    HIGH_VALUE_THRESHOLD: float = 50000.0  # ₹50,000+ requires approval if confidence < 85%
    HIGH_VALUE_APPROVAL_P_THRESHOLD: float = 0.85
    LOW_CONFIDENCE_THRESHOLD: float = 0.45
    INCENTIVE_MAX_AMOUNT: float = 500.0
    INCENTIVE_MAX_PCT: float = 0.05  # 5%
    
    # Operational Limits
    MAX_CONSECUTIVE_FAILURES: int = 3
    MAX_CONTACTS_24H: int = 2
    MAX_CONTACTS_7D: int = 5
    MIN_RETRY_DELAY_HOURS: int = 4
    
    # Configurable Illustrative Simulation Cost Matrix (in INR)
    COST_MATRIX: Dict[str, float] = field(default_factory=lambda: {
        "Retry Immediately": 1.00,
        "Retry Delay 6h": 1.00,
        "Retry Delay 18h": 1.00,
        "Payment Method Update": 25.00,
        "Personalized Email": 0.20,
        "WhatsApp Nudge": 0.50,
        "Incentive Offer": 0.00,  # Base fee + dynamic incentive calculation
        "Human Escalation": 150.00,
        "Stop Intervention": 0.00
    })

settings = Settings()
