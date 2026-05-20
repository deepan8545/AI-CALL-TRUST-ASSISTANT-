import pytest
from app.modules.rules_scorer import score_call, ScoringResult
from app.modules.redis_reputation import ReputationPayload


# ── Safe Scenarios ──

class TestSafeCalls:
    def test_verified_business_clean_reputation(self):
        rep = ReputationPayload(
            phone_number_hash="hash_safe",
            business_verified=True,
            known_business=True,
            complaint_count_7d=0,
            first_seen_days_ago=365,
        )
        result = score_call(
            call_frequency_24h=2, call_frequency_7d=10,
            spoofing_signal=False, answered_before=True,
            business_identity_id="biz_001", reputation=rep,
        )
        assert result.risk_label == "Safe"
        assert result.risk_score < 0.25
        assert "VERIFIED_BUSINESS" in result.reason_codes

    def test_allowlist_overrides_everything(self):
        rep = ReputationPayload(
            phone_number_hash="hash_allow",
            allowlist_match=True,
            complaint_count_7d=50,  # would normally be high risk
        )
        result = score_call(
            call_frequency_24h=100, spoofing_signal=True, reputation=rep,
        )
        assert result.risk_label == "Safe"
        assert result.risk_score == 0.02
        assert result.reason_codes == ["ALLOWLIST_MATCH"]

    def test_previously_safe_reduces_score(self):
        rep = ReputationPayload(
            phone_number_hash="hash_prev_safe",
            business_verified=True,
            previous_risk_label="Safe",
            first_seen_days_ago=100,
        )
        result = score_call(reputation=rep)
        assert result.risk_label == "Safe"
        assert "PREVIOUSLY_SAFE" in result.reason_codes


# ── Unknown Scenarios ──

class TestUnknownCalls:
    def test_no_reputation_no_business(self):
        result = score_call(
            call_frequency_24h=5, call_frequency_7d=30,
            spoofing_signal=False, answered_before=False,
            business_identity_id=None, reputation=None,
        )
        assert result.risk_label == "Unknown"
        assert "NO_BUSINESS_IDENTITY" in result.reason_codes

    def test_known_business_unverified(self):
        rep = ReputationPayload(
            phone_number_hash="hash_unverified",
            known_business=True,
            business_verified=False,
            first_seen_days_ago=60,
        )
        result = score_call(reputation=rep)
        assert result.risk_score < 0.50
        assert "KNOWN_BUSINESS_UNVERIFIED" in result.reason_codes


# ── Suspicious Scenarios ──

class TestSuspiciousCalls:
    def test_moderate_complaints_high_frequency(self):
        rep = ReputationPayload(
            phone_number_hash="hash_sus",
            complaint_count_7d=12,
            first_seen_days_ago=30,
        )
        result = score_call(
            call_frequency_24h=25, call_frequency_7d=100,
            spoofing_signal=False, reputation=rep,
        )
        assert result.risk_label == "Suspicious"
        assert "MODERATE_COMPLAINT_VOLUME" in result.reason_codes
        assert "HIGH_FREQUENCY_24H" in result.reason_codes

    def test_new_number_some_complaints(self):
        rep = ReputationPayload(
            phone_number_hash="hash_new_sus",
            complaint_count_7d=5,
            first_seen_days_ago=2,
        )
        result = score_call(reputation=rep)
        assert result.risk_label in ["Suspicious", "Unknown"]
        assert "NEW_NUMBER" in result.reason_codes
        assert "SOME_COMPLAINTS" in result.reason_codes


# ── High Risk Scenarios ──

class TestHighRiskCalls:
    def test_blocklist_overrides_everything(self):
        rep = ReputationPayload(
            phone_number_hash="hash_block",
            blocklist_match=True,
            business_verified=True,  # would normally be safe
        )
        result = score_call(reputation=rep)
        assert result.risk_label == "High Risk"
        assert result.risk_score == 0.98
        assert result.reason_codes == ["BLOCKLIST_MATCH"]

    def test_high_complaints_spoofing_scam_cluster(self):
        rep = ReputationPayload(
            phone_number_hash="hash_scam",
            complaint_count_7d=25,
            complaint_count_30d=60,
            known_scam_cluster=True,
            first_seen_days_ago=2,
        )
        result = score_call(
            call_frequency_24h=55, call_frequency_7d=350,
            spoofing_signal=True, reputation=rep,
        )
        assert result.risk_label == "High Risk"
        assert result.risk_score >= 0.75
        assert "HIGH_COMPLAINT_VOLUME" in result.reason_codes
        assert "SPOOFING_SIGNAL_DETECTED" in result.reason_codes
        assert "SIMILAR_TO_SCAM_CLUSTER" in result.reason_codes
        assert "VERY_HIGH_FREQUENCY_24H" in result.reason_codes

    def test_previously_high_risk_with_complaints(self):
        rep = ReputationPayload(
            phone_number_hash="hash_repeat",
            complaint_count_7d=15,
            previous_risk_label="High Risk",
            first_seen_days_ago=10,
        )
        result = score_call(
            call_frequency_24h=30, spoofing_signal=True, reputation=rep,
        )
        assert result.risk_label == "High Risk"
        assert "PREVIOUSLY_HIGH_RISK" in result.reason_codes

    def test_max_risk_all_signals(self):
        rep = ReputationPayload(
            phone_number_hash="hash_max",
            complaint_count_7d=30,
            complaint_count_30d=100,
            known_scam_cluster=True,
            previous_risk_label="High Risk",
            first_seen_days_ago=1,
        )
        result = score_call(
            call_frequency_24h=60, call_frequency_7d=400,
            spoofing_signal=True, reputation=rep,
        )
        assert result.risk_label == "High Risk"
        assert result.risk_score == 1.0  # clamped at 1.0


# ── Score Clamping and Labels ──

class TestScoreBoundaries:
    def test_score_never_below_zero(self):
        rep = ReputationPayload(
            phone_number_hash="hash_floor",
            business_verified=True,
            allowlist_match=False,
            previous_risk_label="Safe",
            first_seen_days_ago=500,
        )
        result = score_call(answered_before=True, reputation=rep)
        assert result.risk_score >= 0.0

    def test_score_never_above_one(self):
        rep = ReputationPayload(
            phone_number_hash="hash_ceiling",
            complaint_count_7d=50,
            complaint_count_30d=200,
            known_scam_cluster=True,
            previous_risk_label="High Risk",
            first_seen_days_ago=0,
        )
        result = score_call(
            call_frequency_24h=100, call_frequency_7d=500,
            spoofing_signal=True, reputation=rep,
        )
        assert result.risk_score <= 1.0

    def test_label_matches_score_range(self):
        """Every label should match its threshold range."""
        rep_safe = ReputationPayload(phone_number_hash="h1", business_verified=True, first_seen_days_ago=365)
        result = score_call(reputation=rep_safe)
        if result.risk_label == "Safe":
            assert result.risk_score < 0.25
        elif result.risk_label == "Unknown":
            assert 0.25 <= result.risk_score < 0.50
        elif result.risk_label == "Suspicious":
            assert 0.50 <= result.risk_score < 0.75
        elif result.risk_label == "High Risk":
            assert result.risk_score >= 0.75


# ── Reason Codes ──

class TestReasonCodes:
    def test_reason_codes_not_empty(self):
        result = score_call()
        assert len(result.reason_codes) > 0

    def test_recommendation_matches_label(self):
        result_safe = score_call(
            reputation=ReputationPayload(
                phone_number_hash="h", business_verified=True, first_seen_days_ago=365,
            ),
            answered_before=True,
        )
        assert "safe" in result_safe.recommended_action.lower() or result_safe.risk_label != "Safe"

    def test_high_complaint_30d_adds_reason(self):
        rep = ReputationPayload(
            phone_number_hash="hash_30d",
            complaint_count_7d=5,
            complaint_count_30d=55,
        )
        result = score_call(reputation=rep)
        assert "HIGH_COMPLAINT_VOLUME_30D" in result.reason_codes

    def test_recent_number_adds_reason(self):
        rep = ReputationPayload(
            phone_number_hash="hash_recent",
            first_seen_days_ago=5,
        )
        result = score_call(reputation=rep)
        assert "RECENT_NUMBER" in result.reason_codes
