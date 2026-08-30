from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class CustomerDB(Base):
    __tablename__ = "customers"
    
    customer_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    tenure_months = Column(Integer, default=1)
    subscription_status = Column(String, default="ACTIVE")
    segment = Column(String, default="MidMarket")
    historical_recovery_rate = Column(Float, default=0.50)
    engagement_score = Column(Float, default=0.70)
    do_not_contact = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    payments = relationship("PaymentDB", back_populates="customer")

class PaymentDB(Base):
    __tablename__ = "payments"
    
    payment_id = Column(String, primary_key=True, index=True)
    customer_id = Column(String, ForeignKey("customers.customer_id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="INR")
    payment_method = Column(String, nullable=False)
    card_type = Column(String, nullable=True)
    failure_reason = Column(String, nullable=False)
    failure_code = Column(String, nullable=False)
    status = Column(String, default="FAILED")  # FAILED, RECOVERING, RECOVERED, ESCALATED, ABANDONED
    created_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("CustomerDB", back_populates="payments")
    decisions = relationship("DecisionContractDB", back_populates="payment")
    outcomes = relationship("RecoveryOutcomeDB", back_populates="payment")

class CustomerFatigueDB(Base):
    __tablename__ = "customer_fatigue"
    
    customer_id = Column(String, primary_key=True, index=True)
    contacts_24h = Column(Integer, default=0)
    contacts_7d = Column(Integer, default=0)
    failed_attempts = Column(Integer, default=0)
    consecutive_failures = Column(Integer, default=0)
    last_contact_timestamp = Column(DateTime, nullable=True)
    fatigue_score = Column(Float, default=0.0)

class DecisionContractDB(Base):
    __tablename__ = "decision_contracts"
    
    decision_id = Column(String, primary_key=True, index=True)
    payment_id = Column(String, ForeignKey("payments.payment_id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    model_version = Column(String, nullable=False)
    policy_version = Column(String, nullable=False)
    feature_snapshot_json = Column(JSON, nullable=False)
    candidate_actions_json = Column(JSON, nullable=False)
    feasible_actions_json = Column(JSON, nullable=False)
    blocked_actions_json = Column(JSON, nullable=False)
    candidate_scores_json = Column(JSON, nullable=True)
    predicted_recovery_probability = Column(Float, nullable=False)
    expected_recovered_amount = Column(Float, nullable=False)
    intervention_cost = Column(Float, nullable=False)
    incentive_cost = Column(Float, nullable=False)
    fatigue_penalty = Column(Float, nullable=False)
    risk_penalty = Column(Float, nullable=False)
    expected_net_value = Column(Float, nullable=False)
    selected_action = Column(String, nullable=False)
    decision_status = Column(String, nullable=False)  # AUTO_EXECUTE, RECOMMEND_FOR_APPROVAL, BLOCK
    approval_required = Column(Boolean, default=False)
    guardrail_results_json = Column(JSON, nullable=False)
    explanation_json = Column(JSON, nullable=False)
    execution_status = Column(String, default="PENDING_SIMULATION")

    payment = relationship("PaymentDB", back_populates="decisions")

class RecoveryOutcomeDB(Base):
    __tablename__ = "recovery_outcomes"
    
    outcome_id = Column(String, primary_key=True, index=True)
    payment_id = Column(String, ForeignKey("payments.payment_id"), nullable=False)
    decision_id = Column(String, nullable=False, unique=True, index=True)
    selected_action = Column(String, nullable=False)
    actual_outcome = Column(String, nullable=False)  # SUCCESS, FAILED
    recovered_amount = Column(Float, default=0.0)
    actual_cost = Column(Float, default=0.0)
    time_to_recovery_hours = Column(Float, default=0.0)
    recorded_at = Column(DateTime, default=datetime.utcnow)

    payment = relationship("PaymentDB", back_populates="outcomes")

class ExperimentDB(Base):
    __tablename__ = "experiments"
    
    experiment_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    sample_size = Column(Integer, nullable=False)
    random_seed = Column(Integer, nullable=False)
    baseline_policy_json = Column(JSON, nullable=False)
    ai_policy_json = Column(JSON, nullable=False)
    baseline_recovered_revenue = Column(Float, nullable=False)
    ai_recovered_revenue = Column(Float, nullable=False)
    incremental_revenue = Column(Float, nullable=False)
    gross_recovery_lift_pct = Column(Float, nullable=False)
    incremental_intervention_cost = Column(Float, nullable=False)
    net_incremental_value = Column(Float, nullable=False)
    roi = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class AgentEventDB(Base):
    __tablename__ = "agent_events"
    
    event_id = Column(String, primary_key=True, index=True)
    payment_id = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    stage = Column(String, nullable=False)
    status = Column(String, nullable=False)
    message = Column(String, nullable=False)
    metadata_json = Column(JSON, nullable=True)
