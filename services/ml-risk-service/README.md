# ML Risk Service

XGBoost and LightGBM fraud risk models trained on synthetic call event data.

**Status:** Built — Day 9

## Models

| Model | File | Task | Metric |
|---|---|---|---|
| XGBoost Binary | `models/xgboost_binary.json` | High-risk detection | ROC AUC |
| LightGBM Binary | `models/lightgbm_binary.txt` | High-risk detection | ROC AUC |
| XGBoost Multiclass | `models/xgboost_multiclass.json` | 4-class risk label | F1 Weighted |

## Usage

```bash
# Generate synthetic data first
cd ../../scripts
python generate_synthetic_data.py

# Train models
cd ../services/ml-risk-service
pip install -r requirements.txt
python train_model.py
```

## Feature Vector (15 features)

call_frequency_24h, call_frequency_7d, spoofing_signal, complaint_count_7d, complaint_count_30d, known_business, business_verified, known_scam_cluster, blocklist_match, allowlist_match, first_seen_days_ago, answered, call_duration_seconds, direct_campaign_count, community_risk_score

## Experiment Tracking

MLflow experiments are logged automatically if MLflow is installed. View with:
```bash
mlflow ui
```
