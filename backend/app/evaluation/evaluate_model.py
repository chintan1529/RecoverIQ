#!/usr/bin/env python
"""
Reproducible ML Evaluation Script for RecoverIQ.
Usage:
    python -m app.evaluation.evaluate_model
    or from project root:
    python backend/app/evaluation/evaluate_model.py
"""
import os
import sys
import json

# Ensure backend root is on sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from app.ml.models import RecoveryPredictorModel
from app.ml.generator import generate_synthetic_dataset

def run_evaluation(n_samples: int = 5000, seed: int = 42) -> dict:
    print("=" * 70)
    print("RECOVERIQ SCIENTIFIC MODEL EVALUATION PIPELINE")
    print("=" * 70)
    print(f"Generating synthetic dataset: {n_samples:,} payments (Seed: {seed})")
    
    df_pre, df_post = generate_synthetic_dataset(n_samples=n_samples, seed=seed)
    
    print(f"Pre-decision features shape: {df_pre.shape}")
    print(f"Post-action outcomes shape: {df_post.shape}")
    print("\nTraining & Calibrating Model with Chronological Split (70% Train / 15% Val / 15% Test)...")
    
    model = RecoveryPredictorModel()
    report = model.train_and_evaluate(df_pre, df_post)
    
    counts = report["sample_counts"]
    base = report["baseline_logistic"]
    raw = report["primary_raw_gradient_boosting"]
    cal = report["primary_calibrated_gradient_boosting"]
    
    print("\n" + "=" * 70)
    print("DATASET PARTITIONING (CHRONOLOGICAL SPLIT)")
    print("=" * 70)
    print(f"  Total Dataset Size:      {counts['total']:,} records")
    print(f"  Training Split (70%):     {counts['train_size']:,} records")
    print(f"  Validation Split (15%):   {counts['val_size']:,} records (Used for Platt Calibration & Permutation Importance)")
    print(f"  Test Split (15%):         {counts['test_size']:,} records (Untouched Out-of-Time Holdout)")
    print(f"  Positive Class Prevalence: {cal['positive_prevalence']:.1%}")

    print("\n" + "=" * 70)
    print("BENCHMARK METRIC COMPARISON TABLE (UNTOUCHED TEST SET)")
    print("=" * 70)
    print(f"{'Metric':<32} | {'Baseline (Logistic)':<20} | {'Primary (Uncalibrated)':<22} | {'RecoverIQ (Calibrated)':<22}")
    print("-" * 105)
    print(f"{'ROC-AUC (Discrimination)':<32} | {base['roc_auc']:<20.4f} | {raw['roc_auc']:<22.4f} | {cal['roc_auc']:<22.4f}")
    print(f"{'PR-AUC (Precision-Recall)':<32} | {base['pr_auc']:<20.4f} | {raw['pr_auc']:<22.4f} | {cal['pr_auc']:<22.4f}")
    print(f"{'Brier Score (Lower is better)':<32} | {base['brier_score']:<20.4f} | {raw['brier_score']:<22.4f} | {cal['brier_score']:<22.4f}")
    print(f"{'Expected Calibration Error':<32} | {base['expected_calibration_error']:<20.4f} | {raw['expected_calibration_error']:<22.4f} | {cal['expected_calibration_error']:<22.4f}")
    print(f"{'F1 Score (at threshold 0.50)':<32} | {base['f1']:<20.4f} | {raw['f1']:<22.4f} | {cal['f1']:<22.4f}")
    print(f"{'Precision':<32} | {base['precision']:<20.4f} | {raw['precision']:<22.4f} | {cal['precision']:<22.4f}")
    print(f"{'Recall':<32} | {base['recall']:<20.4f} | {raw['recall']:<22.4f} | {cal['recall']:<22.4f}")
    print("-" * 105)
    print(f"Brier Score Improvement via Calibration: {report['brier_improvement_pct']:+.2f}%")

    print("\n" + "=" * 70)
    print("TOP MODEL SIGNALS (PERMUTATION IMPORTANCE ON VALIDATION SET)")
    print("=" * 70)
    for rank, (feat, imp) in enumerate(report["top_features"][:8], 1):
        print(f"  {rank}. {feat:<35}: {imp:.4f} ({imp*100:.1f}%)")
    print("  *Note: Labeled as predictive model signals, not causal parameters.")

    print("\n" + "=" * 70)
    print("CONFUSION MATRIX ON TEST SET (Threshold = 0.50)")
    print("=" * 70)
    cm = cal["confusion_matrix"]
    print(f"  [[True Neg: {cm[0][0]:<5}  False Pos: {cm[0][1]:<5}]")
    print(f"   [False Neg: {cm[1][0]:<5} True Pos: {cm[1][1]:<5}]]")
    print("=" * 70)
    
    return report

if __name__ == "__main__":
    run_evaluation()
