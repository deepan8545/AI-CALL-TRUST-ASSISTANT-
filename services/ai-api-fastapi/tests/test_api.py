import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


# ── Health ──

def test_health_returns_200():
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "healthy"
    assert body["version"] == "0.1.0"
    assert "services" in body


# ── Score Call ──

VALID_SCORE_CALL = {
    "phone_number_hash": "hash_abc123",
    "carrier_id": "carrier_001",
    "timestamp": "2026-04-27T10:30:00Z",
    "call_duration_seconds": 0,
    "user_region": "US-IL",
    "business_identity_id": "business_123",
    "call_metadata": {
        "call_frequency_24h": 42,
        "call_frequency_7d": 300,
        "spoofing_signal": True,
        "answered_before": False,
    },
}


def test_score_call_valid():
    res = client.post("/score-call", json=VALID_SCORE_CALL)
    assert res.status_code == 200
    body = res.json()
    assert "call_id" in body
    assert 0.0 <= body["risk_score"] <= 1.0
    assert body["risk_label"] in ["Safe", "Unknown", "Suspicious", "High Risk"]
    assert isinstance(body["reason_codes"], list)
    assert isinstance(body["recommended_action"], str)
    assert isinstance(body["explanation"], str)


def test_score_call_missing_phone_hash():
    payload = {**VALID_SCORE_CALL, "phone_number_hash": ""}
    res = client.post("/score-call", json=payload)
    assert res.status_code == 422


def test_score_call_missing_carrier():
    payload = {**VALID_SCORE_CALL}
    del payload["carrier_id"]
    res = client.post("/score-call", json=payload)
    assert res.status_code == 422


def test_score_call_negative_duration():
    payload = {**VALID_SCORE_CALL, "call_duration_seconds": -1}
    res = client.post("/score-call", json=payload)
    assert res.status_code == 422


def test_score_call_missing_metadata():
    payload = {**VALID_SCORE_CALL}
    del payload["call_metadata"]
    res = client.post("/score-call", json=payload)
    assert res.status_code == 422


def test_score_call_optional_business_id_null():
    payload = {**VALID_SCORE_CALL, "business_identity_id": None}
    res = client.post("/score-call", json=payload)
    assert res.status_code == 200


# ── Ingest Call Event ──

VALID_INGEST = {
    "phone_number_hash": "hash_xyz789",
    "carrier_id": "carrier_002",
    "timestamp": "2026-04-27T11:00:00Z",
    "call_duration_seconds": 120,
    "user_region": "US-CA",
    "business_identity_id": None,
    "answered": True,
}


def test_ingest_call_event_valid():
    res = client.post("/ingest-call-event", json=VALID_INGEST)
    assert res.status_code == 201
    body = res.json()
    assert body["status"] == "ingested"
    assert "event_id" in body


def test_ingest_call_event_missing_hash():
    payload = {**VALID_INGEST}
    del payload["phone_number_hash"]
    res = client.post("/ingest-call-event", json=payload)
    assert res.status_code == 422


# ── Analyze Transcript ──

VALID_TRANSCRIPT = {
    "call_id": "call_001",
    "transcript": "This is your bank. Send the verification code now.",
}


def test_analyze_transcript_valid():
    res = client.post("/analyze-transcript", json=VALID_TRANSCRIPT)
    assert res.status_code == 200
    body = res.json()
    assert isinstance(body["detected_intents"], list)
    assert 0.0 <= body["transcript_risk_score"] <= 1.0
    assert isinstance(body["reason_codes"], list)


def test_analyze_transcript_empty_text():
    payload = {"call_id": "call_001", "transcript": ""}
    res = client.post("/analyze-transcript", json=payload)
    assert res.status_code == 422


# ── Summarize Call ──

VALID_SUMMARY = {
    "call_id": "call_001",
    "transcript": "This is your bank. Send the verification code now.",
    "risk_label": "High Risk",
    "reason_codes": ["VERIFICATION_CODE_REQUEST"],
}


def test_summarize_call_valid():
    res = client.post("/summarize-call", json=VALID_SUMMARY)
    assert res.status_code == 200
    body = res.json()
    assert isinstance(body["summary"], str)
    assert isinstance(body["action_items"], list)
    assert isinstance(body["sensitive_request_detected"], bool)


def test_summarize_call_invalid_risk_label():
    payload = {**VALID_SUMMARY, "risk_label": "INVALID"}
    res = client.post("/summarize-call", json=payload)
    assert res.status_code == 422


# ── Graph Risk ──

def test_graph_risk_valid():
    res = client.post("/graph-risk", json={"phone_number_hash": "hash_abc123"})
    assert res.status_code == 200
    body = res.json()
    assert isinstance(body["complaint_count"], int)
    assert 0.0 <= body["community_risk_score"] <= 1.0
    assert isinstance(body["graph_reason_codes"], list)


def test_graph_risk_empty_hash():
    res = client.post("/graph-risk", json={"phone_number_hash": ""})
    assert res.status_code == 422


# ── List Calls ──

def test_list_calls_default():
    res = client.get("/calls")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 0
    assert body["limit"] == 20
    assert body["offset"] == 0
    assert isinstance(body["calls"], list)


def test_list_calls_custom_params():
    res = client.get("/calls?limit=5&offset=10")
    assert res.status_code == 200
    body = res.json()
    assert body["limit"] == 5
    assert body["offset"] == 10


def test_list_calls_invalid_limit():
    res = client.get("/calls?limit=0")
    assert res.status_code == 422
