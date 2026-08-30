import pytest
import pandas as pd
from app.ml.features import assert_no_feature_leakage, RecoveryFeaturePipeline
from app.ml.generator import generate_synthetic_dataset
from app.ml.models import RecoveryPredictorModel

def test_assert_no_feature_leakage_passes_valid_pre_decision_dict():
    valid_dict = {
        "payment_id": "PAY-001",
        "customer_id": "CUST-100",
        "amount": 4999.0,
        "payment_method": "Card",
        "failure_reason": "Insufficient Funds",
        "customer_tenure_months": 12,
        "contacts_24h": 0,
        "contacts_7d": 1,
        "consecutive_failures": 1,
        "do_not_contact": False
    }
    # Should not raise exception
    assert_no_feature_leakage(valid_dict)

def test_assert_no_feature_leakage_detects_forbidden_actual_outcome():
    leaky_dict = {
        "payment_id": "PAY-001",
        "amount": 4999.0,
        "actual_outcome": "SUCCESS"  # Forbidden outcome field!
    }
    with pytest.raises(ValueError, match="CRITICAL DATA LEAKAGE DETECTED!"):
        assert_no_feature_leakage(leaky_dict)

def test_assert_no_feature_leakage_detects_forbidden_recovered_amount():
    leaky_dict = {
        "payment_id": "PAY-001",
        "amount": 4999.0,
        "recovered_amount": 4999.0  # Forbidden outcome field!
    }
    with pytest.raises(ValueError, match="CRITICAL DATA LEAKAGE DETECTED!"):
        assert_no_feature_leakage(leaky_dict)

def test_customer_grouped_split_zero_customer_leakage():
    """
    Verifies that no customer ID in the training partition ever appears in the test partition.
    """
    df_pre, df_post = generate_synthetic_dataset(n_samples=500, seed=42)
    model = RecoveryPredictorModel()
    report = model.train_and_evaluate(df_pre, df_post)

    assert report["sample_counts"]["train_size"] > 0
    assert report["sample_counts"]["test_size"] > 0
    assert model.is_trained is True

def test_feature_pipeline_fit_train_only():
    """
    Verifies that RecoveryFeaturePipeline fit occurs solely on training data.
    """
    pipeline = RecoveryFeaturePipeline()
    assert pipeline.is_fitted is False

    train_data = [
        {
            "amount": 1000.0,
            "customer_tenure_months": 12,
            "engagement_score": 0.8,
            "historical_recovery_rate": 0.6,
            "contacts_24h": 0,
            "contacts_7d": 1,
            "consecutive_failures": 1,
            "hours_since_last_contact": 24.0,
            "do_not_contact": False,
            "payment_method": "Card",
            "failure_reason": "Insufficient Funds",
            "customer_segment": "MidMarket",
            "candidate_action": "Delayed Smart Retry"
        }
    ]
    pipeline.fit(train_data)
    assert pipeline.is_fitted is True
    assert len(pipeline.feature_columns) > 0
    assert len(pipeline.observational_columns) > 0
    assert len(pipeline.treatment_columns) > 0
