import pandas as pd
import numpy as np
from typing import List, Dict, Any

# Strict List of Allowed Input Pre-Decision Feature Names
PRE_DECISION_FEATURE_NAMES = [
    "amount",
    "customer_tenure_months",
    "engagement_score",
    "historical_recovery_rate",
    "contacts_24h",
    "contacts_7d",
    "consecutive_failures",
    "hours_since_last_contact",
    "do_not_contact"
]

CATEGORICAL_FEATURE_NAMES = [
    "payment_method",
    "failure_reason",
    "customer_segment",
    "candidate_action"
]

OBSERVATIONAL_CATEGORICAL_NAMES = [
    "payment_method",
    "failure_reason",
    "customer_segment"
]

TREATMENT_FEATURE_NAME = "candidate_action"

FORBIDDEN_POST_ACTION_FIELDS = [
    "actual_outcome",
    "recovered_amount",
    "actual_cost",
    "time_to_recovery_hours",
    "ground_truth_p"
]

def assert_no_feature_leakage(df_or_dict: Any):
    """
    Automated test assertion verifying that post-action outcome fields are NEVER in feature inputs.
    """
    keys = df_or_dict.keys() if isinstance(df_or_dict, dict) else df_or_dict.columns
    for forbidden in FORBIDDEN_POST_ACTION_FIELDS:
        if forbidden in keys:
            raise ValueError(f"CRITICAL DATA LEAKAGE DETECTED! Forbidden outcome field '{forbidden}' found in feature inputs!")


class RecoveryFeaturePipeline:
    def __init__(self):
        self.feature_columns: List[str] = []
        self.col_to_idx: Dict[str, int] = {}
        self.observational_columns: List[str] = []
        self.treatment_columns: List[str] = []
        self.is_fitted: bool = False

    def fit(self, records: List[Dict[str, Any]]) -> "RecoveryFeaturePipeline":
        """
        Fits encoder solely on training partition records to prevent pre-split leakage.
        """
        for rec in records:
            assert_no_feature_leakage(rec)

        df = pd.DataFrame(records)

        # Base numeric features
        df_num = df[[
            "amount",
            "customer_tenure_months",
            "engagement_score",
            "historical_recovery_rate",
            "contacts_24h",
            "contacts_7d",
            "consecutive_failures",
            "hours_since_last_contact"
        ]].copy()

        df_num["do_not_contact"] = df["do_not_contact"].astype(int)
        df_num["propensity_score"] = (df_num["engagement_score"] * 0.5) + (df_num["historical_recovery_rate"] * 0.5)
        df_num["tenure_norm"] = np.minimum(df_num["customer_tenure_months"] / 36.0, 1.0)
        df_num["fatigue_index"] = (df_num["contacts_24h"] * 0.5) + (df_num["contacts_7d"] * 0.3) + (df_num["consecutive_failures"] * 0.2)

        # One-hot encode categoricals on train set
        df_cat = pd.get_dummies(df[[
            "payment_method",
            "failure_reason",
            "customer_segment",
            "candidate_action"
        ]], drop_first=False)

        encoded_df = pd.concat([df_num, df_cat], axis=1)
        self.feature_columns = list(encoded_df.columns)
        self.col_to_idx = {col: i for i, col in enumerate(self.feature_columns)}
        
        self.observational_columns = [c for c in self.feature_columns if not c.startswith("candidate_action_")]
        self.treatment_columns = [c for c in self.feature_columns if c.startswith("candidate_action_")]
        self.is_fitted = True
        return self

    def transform_records(self, records: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Transforms records using columns fitted strictly on the training partition.
        """
        if not self.is_fitted:
            # If not yet fitted, fit on these records
            self.fit(records)

        for rec in records:
            assert_no_feature_leakage(rec)

        df = pd.DataFrame(records)

        df_num = df[[
            "amount",
            "customer_tenure_months",
            "engagement_score",
            "historical_recovery_rate",
            "contacts_24h",
            "contacts_7d",
            "consecutive_failures",
            "hours_since_last_contact"
        ]].copy()

        df_num["do_not_contact"] = df["do_not_contact"].astype(int)
        df_num["propensity_score"] = (df_num["engagement_score"] * 0.5) + (df_num["historical_recovery_rate"] * 0.5)
        df_num["tenure_norm"] = np.minimum(df_num["customer_tenure_months"] / 36.0, 1.0)
        df_num["fatigue_index"] = (df_num["contacts_24h"] * 0.5) + (df_num["contacts_7d"] * 0.3) + (df_num["consecutive_failures"] * 0.2)

        df_cat = pd.get_dummies(df[[
            "payment_method",
            "failure_reason",
            "customer_segment",
            "candidate_action"
        ]], drop_first=False)

        encoded_df = pd.concat([df_num, df_cat], axis=1)
        encoded_df = encoded_df.reindex(columns=self.feature_columns, fill_value=0.0)
        return encoded_df.fillna(0.0).astype(np.float64)

    def transform_single_fast(self, rec: Dict[str, Any]) -> np.ndarray:
        """
        High-performance vectorized single record feature transformation.
        """
        assert_no_feature_leakage(rec)
        arr = np.zeros((1, len(self.feature_columns)), dtype=np.float32)

        eng = float(rec.get("engagement_score", 0.5))
        hist = float(rec.get("historical_recovery_rate", 0.5))
        tenure = float(rec.get("customer_tenure_months", 1))
        c24 = float(rec.get("contacts_24h", 0))
        c7 = float(rec.get("contacts_7d", 0))
        cf = float(rec.get("consecutive_failures", 1))

        num_fields = {
            "amount": float(rec.get("amount", 0.0)),
            "customer_tenure_months": tenure,
            "engagement_score": eng,
            "historical_recovery_rate": hist,
            "contacts_24h": c24,
            "contacts_7d": c7,
            "consecutive_failures": cf,
            "hours_since_last_contact": float(rec.get("hours_since_last_contact", 24.0)),
            "do_not_contact": 1.0 if rec.get("do_not_contact", False) else 0.0,
            "propensity_score": (eng * 0.5) + (hist * 0.5),
            "tenure_norm": min(tenure / 36.0, 1.0),
            "fatigue_index": (c24 * 0.5) + (c7 * 0.3) + (cf * 0.2)
        }

        for k, v in num_fields.items():
            if k in self.col_to_idx:
                arr[0, self.col_to_idx[k]] = v

        cats = [
            f"payment_method_{rec.get('payment_method')}",
            f"failure_reason_{rec.get('failure_reason')}",
            f"customer_segment_{rec.get('customer_segment')}",
            f"candidate_action_{rec.get('candidate_action')}"
        ]

        for cat in cats:
            if cat in self.col_to_idx:
                arr[0, self.col_to_idx[cat]] = 1.0

        return arr
