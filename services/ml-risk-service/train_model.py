"""
ML Training Script — AI Call Trust Assistant
Trains XGBoost and LightGBM models on synthetic call event data.

Usage:
    python train_model.py

Outputs:
    models/xgboost_binary.json          — XGBoost binary classifier
    models/lightgbm_binary.txt          — LightGBM binary classifier
    models/xgboost_multiclass.json      — XGBoost multiclass classifier
    models/training_metrics.json        — All metrics
"""

import os
import sys
import json
import time
import numpy as np

# Add parent to path for feature_extraction import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from feature_extraction import load_dataset, FEATURE_NAMES, LABEL_MAP
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
)
import xgboost as xgb
import lightgbm as lgb

# --- Config ---
DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "synthetic", "call_events.csv"
)
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
RANDOM_STATE = 42
TEST_SIZE = 0.2

# Try MLflow (optional)
try:
    import mlflow
    import mlflow.xgboost
    import mlflow.lightgbm
    HAS_MLFLOW = True
except ImportError:
    HAS_MLFLOW = False


def train_xgboost_binary(X_train, X_test, y_train, y_test):
    """Train XGBoost binary classifier (high_risk vs not)."""
    print("\n" + "=" * 60)
    print("TRAINING: XGBoost Binary Classifier")
    print("=" * 60)

    params = {
        "objective": "binary:logistic",
        "eval_metric": "auc",
        "max_depth": 6,
        "learning_rate": 0.1,
        "n_estimators": 200,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "min_child_weight": 3,
        "random_state": RANDOM_STATE,
        "verbosity": 0,
    }

    model = xgb.XGBClassifier(**params)

    start = time.time()
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False,
    )
    train_time = round(time.time() - start, 2)

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    metrics = compute_binary_metrics(y_test, y_pred, y_prob, train_time)
    print_metrics("XGBoost Binary", metrics)
    print_feature_importance(model.feature_importances_, "XGBoost Binary")

    # Save model
    model_path = os.path.join(MODEL_DIR, "xgboost_binary.json")
    model.save_model(model_path)
    print(f"  → Saved: {model_path}")

    return model, metrics


def train_lightgbm_binary(X_train, X_test, y_train, y_test):
    """Train LightGBM binary classifier."""
    print("\n" + "=" * 60)
    print("TRAINING: LightGBM Binary Classifier")
    print("=" * 60)

    params = {
        "objective": "binary",
        "metric": "auc",
        "max_depth": 6,
        "learning_rate": 0.1,
        "n_estimators": 200,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "min_child_weight": 3,
        "random_state": RANDOM_STATE,
        "verbose": -1,
    }

    model = lgb.LGBMClassifier(**params)

    start = time.time()
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
    )
    train_time = round(time.time() - start, 2)

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    metrics = compute_binary_metrics(y_test, y_pred, y_prob, train_time)
    print_metrics("LightGBM Binary", metrics)
    print_feature_importance(model.feature_importances_, "LightGBM Binary")

    # Save model
    model_path = os.path.join(MODEL_DIR, "lightgbm_binary.txt")
    model.booster_.save_model(model_path)
    print(f"  → Saved: {model_path}")

    return model, metrics


def train_xgboost_multiclass(X_train, X_test, y_train, y_test):
    """Train XGBoost multiclass classifier (Safe/Unknown/Suspicious/High Risk)."""
    print("\n" + "=" * 60)
    print("TRAINING: XGBoost Multiclass Classifier")
    print("=" * 60)

    params = {
        "objective": "multi:softprob",
        "eval_metric": "mlogloss",
        "num_class": 4,
        "max_depth": 6,
        "learning_rate": 0.1,
        "n_estimators": 200,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "random_state": RANDOM_STATE,
        "verbosity": 0,
    }

    model = xgb.XGBClassifier(**params)

    start = time.time()
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False,
    )
    train_time = round(time.time() - start, 2)

    y_pred = model.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    f1_macro = f1_score(y_test, y_pred, average="macro")
    f1_weighted = f1_score(y_test, y_pred, average="weighted")

    label_names = list(LABEL_MAP.keys())
    report = classification_report(y_test, y_pred, target_names=label_names)

    metrics = {
        "accuracy": round(acc, 4),
        "f1_macro": round(f1_macro, 4),
        "f1_weighted": round(f1_weighted, 4),
        "train_time_seconds": train_time,
    }

    print(f"  Accuracy:    {acc:.4f}")
    print(f"  F1 Macro:    {f1_macro:.4f}")
    print(f"  F1 Weighted: {f1_weighted:.4f}")
    print(f"  Train time:  {train_time}s")
    print(f"\n{report}")

    # Save model
    model_path = os.path.join(MODEL_DIR, "xgboost_multiclass.json")
    model.save_model(model_path)
    print(f"  → Saved: {model_path}")

    return model, metrics


def compute_binary_metrics(y_true, y_pred, y_prob, train_time):
    return {
        "accuracy": round(accuracy_score(y_true, y_pred), 4),
        "precision": round(precision_score(y_true, y_pred), 4),
        "recall": round(recall_score(y_true, y_pred), 4),
        "f1": round(f1_score(y_true, y_pred), 4),
        "roc_auc": round(roc_auc_score(y_true, y_prob), 4),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
        "train_time_seconds": train_time,
    }


def print_metrics(model_name, metrics):
    print(f"  Accuracy:  {metrics['accuracy']}")
    print(f"  Precision: {metrics['precision']}")
    print(f"  Recall:    {metrics['recall']}")
    print(f"  F1:        {metrics['f1']}")
    print(f"  ROC AUC:   {metrics['roc_auc']}")
    print(f"  Train time: {metrics['train_time_seconds']}s")
    cm = metrics["confusion_matrix"]
    print(f"  Confusion Matrix:")
    print(f"    TN={cm[0][0]}  FP={cm[0][1]}")
    print(f"    FN={cm[1][0]}  TP={cm[1][1]}")


def print_feature_importance(importances, model_name):
    print(f"\n  Feature Importance ({model_name}):")
    pairs = sorted(zip(FEATURE_NAMES, importances), key=lambda x: -x[1])
    for name, imp in pairs[:10]:
        bar = "█" * int(imp * 50)
        print(f"    {name:<25} {imp:.4f} {bar}")


def log_to_mlflow(model_name, metrics, model):
    """Log experiment to MLflow if available."""
    if not HAS_MLFLOW:
        return
    try:
        mlflow.set_experiment("call-trust-risk-models")
        with mlflow.start_run(run_name=model_name):
            for key, val in metrics.items():
                if isinstance(val, (int, float)):
                    mlflow.log_metric(key, val)
            mlflow.log_param("model_type", model_name)
            mlflow.log_param("features", len(FEATURE_NAMES))
            mlflow.log_param("feature_names", ",".join(FEATURE_NAMES))
            if "xgboost" in model_name.lower():
                mlflow.xgboost.log_model(model, model_name)
            elif "lightgbm" in model_name.lower():
                mlflow.lightgbm.log_model(model, model_name)
        print(f"  → Logged to MLflow: {model_name}")
    except Exception as e:
        print(f"  → MLflow logging skipped: {e}")


def main():
    print("=" * 60)
    print("AI Call Trust Assistant — ML Training Pipeline")
    print("=" * 60)

    # --- Load data ---
    print(f"\nLoading data from {DATA_PATH}...")
    X, y_binary, y_multiclass = load_dataset(DATA_PATH)
    X = np.array(X)
    y_binary = np.array(y_binary)
    y_multiclass = np.array(y_multiclass)

    print(f"  Samples: {len(X)}")
    print(f"  Features: {len(FEATURE_NAMES)}")
    print(f"  Binary positive rate: {y_binary.mean():.2%}")
    print(f"  Multiclass distribution: {dict(zip(LABEL_MAP.keys(), np.bincount(y_multiclass)))}")

    os.makedirs(MODEL_DIR, exist_ok=True)

    # --- Binary split ---
    X_train_b, X_test_b, y_train_b, y_test_b = train_test_split(
        X, y_binary, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y_binary,
    )

    # --- Multiclass split ---
    X_train_m, X_test_m, y_train_m, y_test_m = train_test_split(
        X, y_multiclass, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y_multiclass,
    )

    # --- Train all models ---
    xgb_model, xgb_metrics = train_xgboost_binary(X_train_b, X_test_b, y_train_b, y_test_b)
    lgb_model, lgb_metrics = train_lightgbm_binary(X_train_b, X_test_b, y_train_b, y_test_b)
    xgb_mc_model, xgb_mc_metrics = train_xgboost_multiclass(X_train_m, X_test_m, y_train_m, y_test_m)

    # --- Cross-validation ---
    print("\n" + "=" * 60)
    print("CROSS-VALIDATION (5-fold)")
    print("=" * 60)

    xgb_cv = cross_val_score(
        xgb.XGBClassifier(objective="binary:logistic", max_depth=6, n_estimators=200, verbosity=0, random_state=RANDOM_STATE),
        X, y_binary, cv=5, scoring="roc_auc",
    )
    print(f"  XGBoost Binary CV AUC: {xgb_cv.mean():.4f} (+/- {xgb_cv.std():.4f})")

    lgb_cv = cross_val_score(
        lgb.LGBMClassifier(objective="binary", max_depth=6, n_estimators=200, verbose=-1, random_state=RANDOM_STATE),
        X, y_binary, cv=5, scoring="roc_auc",
    )
    print(f"  LightGBM Binary CV AUC: {lgb_cv.mean():.4f} (+/- {lgb_cv.std():.4f})")

    # --- Save all metrics ---
    all_metrics = {
        "xgboost_binary": xgb_metrics,
        "lightgbm_binary": lgb_metrics,
        "xgboost_multiclass": xgb_mc_metrics,
        "cross_validation": {
            "xgboost_binary_cv_auc_mean": round(xgb_cv.mean(), 4),
            "xgboost_binary_cv_auc_std": round(xgb_cv.std(), 4),
            "lightgbm_binary_cv_auc_mean": round(lgb_cv.mean(), 4),
            "lightgbm_binary_cv_auc_std": round(lgb_cv.std(), 4),
        },
        "dataset": {
            "total_samples": len(X),
            "features": len(FEATURE_NAMES),
            "test_size": TEST_SIZE,
            "binary_positive_rate": round(float(y_binary.mean()), 4),
        },
    }

    metrics_path = os.path.join(MODEL_DIR, "training_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(all_metrics, f, indent=2)
    print(f"\n  → All metrics saved: {metrics_path}")

    # --- MLflow logging ---
    log_to_mlflow("xgboost_binary", xgb_metrics, xgb_model)
    log_to_mlflow("lightgbm_binary", lgb_metrics, lgb_model)
    log_to_mlflow("xgboost_multiclass", xgb_mc_metrics, xgb_mc_model)

    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)
    print(f"  Models saved to: {MODEL_DIR}/")
    print(f"  Best binary ROC AUC: {max(xgb_metrics['roc_auc'], lgb_metrics['roc_auc'])}")
    print(f"  Multiclass accuracy: {xgb_mc_metrics['accuracy']}")


if __name__ == "__main__":
    main()
