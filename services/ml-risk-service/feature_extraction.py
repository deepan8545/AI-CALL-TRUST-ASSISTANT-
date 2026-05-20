"""
Shared feature extraction module.
Used by BOTH training (offline) and serving (online) to ensure consistency.

Feature vector: 15 numeric features in fixed order.
"""

import csv
from typing import Optional

# Canonical feature order — must match training and serving
FEATURE_NAMES = [
    "call_frequency_24h",
    "call_frequency_7d",
    "spoofing_signal",
    "complaint_count_7d",
    "complaint_count_30d",
    "known_business",
    "business_verified",
    "known_scam_cluster",
    "blocklist_match",
    "allowlist_match",
    "first_seen_days_ago",
    "answered",
    "call_duration_seconds",
    "direct_campaign_count",
    "community_risk_score",
]

TARGET_BINARY = "high_risk_binary"
TARGET_MULTICLASS = "risk_label"
LABEL_MAP = {"Safe": 0, "Unknown": 1, "Suspicious": 2, "High Risk": 3}


def extract_features_from_row(row: dict) -> list[float]:
    """Extract feature vector from a CSV row or API request dict.
    Returns a list of 15 floats in canonical order."""
    return [
        float(row.get("call_frequency_24h", 0)),
        float(row.get("call_frequency_7d", 0)),
        float(row.get("spoofing_signal", 0)),
        float(row.get("complaint_count_7d", 0)),
        float(row.get("complaint_count_30d", 0)),
        float(row.get("known_business", 0)),
        float(row.get("business_verified", 0)),
        float(row.get("known_scam_cluster", 0)),
        float(row.get("blocklist_match", 0)),
        float(row.get("allowlist_match", 0)),
        float(row.get("first_seen_days_ago", 0)),
        float(row.get("answered", 0)),
        float(row.get("call_duration_seconds", 0)),
        float(row.get("direct_campaign_count", 0)),
        float(row.get("community_risk_score", 0.0)),
    ]


def extract_features_from_api(
    call_frequency_24h: int = 0,
    call_frequency_7d: int = 0,
    spoofing_signal: bool = False,
    complaint_count_7d: int = 0,
    complaint_count_30d: int = 0,
    known_business: bool = False,
    business_verified: bool = False,
    known_scam_cluster: bool = False,
    blocklist_match: bool = False,
    allowlist_match: bool = False,
    first_seen_days_ago: int = 0,
    answered: bool = False,
    call_duration_seconds: int = 0,
    direct_campaign_count: int = 0,
    community_risk_score: float = 0.0,
) -> list[float]:
    """Extract feature vector from API-style keyword arguments."""
    return [
        float(call_frequency_24h),
        float(call_frequency_7d),
        float(int(spoofing_signal)),
        float(complaint_count_7d),
        float(complaint_count_30d),
        float(int(known_business)),
        float(int(business_verified)),
        float(int(known_scam_cluster)),
        float(int(blocklist_match)),
        float(int(allowlist_match)),
        float(first_seen_days_ago),
        float(int(answered)),
        float(call_duration_seconds),
        float(direct_campaign_count),
        float(community_risk_score),
    ]


def load_dataset(csv_path: str):
    """Load CSV and return (X, y_binary, y_multiclass) arrays."""
    X = []
    y_binary = []
    y_multiclass = []

    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            X.append(extract_features_from_row(row))
            y_binary.append(int(row[TARGET_BINARY]))
            y_multiclass.append(LABEL_MAP[row[TARGET_MULTICLASS]])

    return X, y_binary, y_multiclass
