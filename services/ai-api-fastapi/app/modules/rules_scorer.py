"""
Rule-based risk scoring engine.

Inputs: call metadata, Redis reputation, business verification status.
Outputs: risk_score (0-1), risk_label, reason_codes, recommended_action.

Rules:
  - High complaint count → increases risk
  - Verified business → decreases risk
  - Known scam cluster → increases risk
  - Spoofing signal → increases risk
  - High call frequency → increases risk
  - Blocklist match → max risk
  - Allowlist match → min risk
"""

from dataclasses import dataclass, field
from typing import Optional
from app.modules.redis_reputation import ReputationPayload


@dataclass
class ScoringResult:
    risk_score: float
    risk_label: str
    reason_codes: list[str] = field(default_factory=list)
    recommended_action: str = ""


# --- Thresholds ---

LABEL_THRESHOLDS = {
    "Safe": (0.0, 0.25),
    "Unknown": (0.25, 0.50),
    "Suspicious": (0.50, 0.75),
    "High Risk": (0.75, 1.0),
}

RECOMMENDATIONS = {
    "Safe": "This call appears safe. You can answer normally.",
    "Unknown": "This caller is not recognized. Be cautious with personal information.",
    "Suspicious": "This call has suspicious signals. Do not share sensitive information.",
    "High Risk": "This call is likely fraudulent. Do not share personal, payment, or verification information.",
}


def _label_from_score(score: float) -> str:
    score = max(0.0, min(1.0, score))
    for label, (low, high) in LABEL_THRESHOLDS.items():
        if low <= score < high:
            return label
    return "High Risk"


def score_call(
    call_frequency_24h: int = 0,
    call_frequency_7d: int = 0,
    spoofing_signal: bool = False,
    answered_before: bool = False,
    business_identity_id: Optional[str] = None,
    reputation: Optional[ReputationPayload] = None,
) -> ScoringResult:
    """
    Deterministic rule-based scoring.
    Returns a ScoringResult with score, label, reason codes, and recommendation.
    """
    score = 0.30  # Base score: Unknown territory
    reason_codes: list[str] = []

    # === ALLOWLIST / BLOCKLIST (override everything) ===
    if reputation and reputation.allowlist_match:
        return ScoringResult(
            risk_score=0.02,
            risk_label="Safe",
            reason_codes=["ALLOWLIST_MATCH"],
            recommended_action=RECOMMENDATIONS["Safe"],
        )

    if reputation and reputation.blocklist_match:
        return ScoringResult(
            risk_score=0.98,
            risk_label="High Risk",
            reason_codes=["BLOCKLIST_MATCH"],
            recommended_action=RECOMMENDATIONS["High Risk"],
        )

    # === BUSINESS VERIFICATION ===
    if reputation and reputation.business_verified:
        score -= 0.30
        reason_codes.append("VERIFIED_BUSINESS")
    elif reputation and reputation.known_business:
        score -= 0.15
        reason_codes.append("KNOWN_BUSINESS_UNVERIFIED")
    elif business_identity_id:
        score -= 0.05
        reason_codes.append("BUSINESS_IDENTITY_PROVIDED")
    else:
        score += 0.05
        reason_codes.append("NO_BUSINESS_IDENTITY")

    # === COMPLAINT VOLUME ===
    complaint_7d = reputation.complaint_count_7d if reputation else 0
    complaint_30d = reputation.complaint_count_30d if reputation else 0

    if complaint_7d >= 20:
        score += 0.30
        reason_codes.append("HIGH_COMPLAINT_VOLUME")
    elif complaint_7d >= 10:
        score += 0.20
        reason_codes.append("MODERATE_COMPLAINT_VOLUME")
    elif complaint_7d >= 3:
        score += 0.10
        reason_codes.append("SOME_COMPLAINTS")

    if complaint_30d >= 50:
        score += 0.10
        reason_codes.append("HIGH_COMPLAINT_VOLUME_30D")

    # === SCAM CLUSTER ===
    if reputation and reputation.known_scam_cluster:
        score += 0.25
        reason_codes.append("SIMILAR_TO_SCAM_CLUSTER")

    # === SPOOFING SIGNAL ===
    if spoofing_signal:
        score += 0.20
        reason_codes.append("SPOOFING_SIGNAL_DETECTED")

    # === CALL FREQUENCY ===
    if call_frequency_24h >= 50:
        score += 0.20
        reason_codes.append("VERY_HIGH_FREQUENCY_24H")
    elif call_frequency_24h >= 20:
        score += 0.10
        reason_codes.append("HIGH_FREQUENCY_24H")

    if call_frequency_7d >= 300:
        score += 0.10
        reason_codes.append("VERY_HIGH_FREQUENCY_7D")

    # === NUMBER AGE ===
    if reputation and reputation.first_seen_days_ago <= 3:
        score += 0.10
        reason_codes.append("NEW_NUMBER")
    elif reputation and reputation.first_seen_days_ago <= 7:
        score += 0.05
        reason_codes.append("RECENT_NUMBER")

    # === PREVIOUS INTERACTIONS ===
    if answered_before:
        score -= 0.05
        reason_codes.append("PREVIOUSLY_ANSWERED")

    if reputation and reputation.previous_risk_label == "High Risk":
        score += 0.15
        reason_codes.append("PREVIOUSLY_HIGH_RISK")
    elif reputation and reputation.previous_risk_label == "Safe":
        score -= 0.10
        reason_codes.append("PREVIOUSLY_SAFE")

    # === CLAMP AND LABEL ===
    score = max(0.0, min(1.0, round(score, 3)))
    label = _label_from_score(score)

    return ScoringResult(
        risk_score=score,
        risk_label=label,
        reason_codes=reason_codes,
        recommended_action=RECOMMENDATIONS[label],
    )
