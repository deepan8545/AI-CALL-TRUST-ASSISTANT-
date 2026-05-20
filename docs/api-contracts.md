# API Contracts — AI Call Trust Assistant

## GET /health

**Response 200:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "services": {
    "database": "connected",
    "redis": "connected",
    "kafka": "connected",
    "neo4j": "connected"
  }
}
```

## POST /score-call

Score an incoming call for fraud risk.

**Request:**
```json
{
  "phone_number_hash": "hash_abc123",
  "carrier_id": "carrier_001",
  "timestamp": "2026-04-27T10:30:00Z",
  "call_duration_seconds": 0,
  "user_region": "US-IL",
  "business_identity_id": "business_123",
  "call_metadata": {
    "call_frequency_24h": 42,
    "call_frequency_7d": 300,
    "spoofing_signal": true,
    "answered_before": false
  }
}
```

**Response 200:**
```json
{
  "call_id": "call_001",
  "risk_score": 0.87,
  "risk_label": "High Risk",
  "reason_codes": [
    "HIGH_COMPLAINT_VOLUME",
    "SIMILAR_TO_SCAM_CLUSTER",
    "SPOOFING_SIGNAL_DETECTED"
  ],
  "recommended_action": "Do not share personal, payment, or verification information.",
  "explanation": "This call appears risky because the number has behavior similar to known scam clusters and has strong spoofing signals."
}
```

## POST /ingest-call-event

Ingest a raw call event for processing.

**Request:**
```json
{
  "phone_number_hash": "hash_abc123",
  "carrier_id": "carrier_001",
  "timestamp": "2026-04-27T10:30:00Z",
  "call_duration_seconds": 120,
  "user_region": "US-IL",
  "business_identity_id": null,
  "answered": true
}
```

**Response 201:**
```json
{
  "event_id": "evt_001",
  "status": "ingested",
  "timestamp": "2026-04-27T10:30:00Z"
}
```

## POST /analyze-transcript

Analyze a call transcript for scam signals.

**Request:**
```json
{
  "call_id": "call_001",
  "transcript": "This is your bank. Send the verification code now or your account will be closed."
}
```

**Response 200:**
```json
{
  "detected_intents": [
    "BANK_IMPERSONATION",
    "VERIFICATION_CODE_REQUEST",
    "ACCOUNT_CLOSURE_THREAT"
  ],
  "transcript_risk_score": 0.91,
  "reason_codes": [
    "CREDENTIAL_REQUEST_LANGUAGE",
    "URGENT_PRESSURE_LANGUAGE"
  ]
}
```

## POST /summarize-call

Generate a human-readable call summary.

**Request:**
```json
{
  "call_id": "call_001",
  "transcript": "...",
  "risk_label": "High Risk",
  "reason_codes": ["VERIFICATION_CODE_REQUEST"]
}
```

**Response 200:**
```json
{
  "summary": "The caller claimed to represent a bank and requested a verification code.",
  "action_items": [
    "Do not share the code",
    "Contact the bank through the official app or website"
  ],
  "sensitive_request_detected": true,
  "user_warning": "This call may be an impersonation attempt."
}
```

## POST /graph-risk

Get graph-derived risk features from Neo4j.

**Request:**
```json
{
  "phone_number_hash": "hash_abc123"
}
```

**Response 200:**
```json
{
  "complaint_count": 15,
  "direct_campaign_count": 2,
  "similar_campaign_count": 5,
  "community_risk_score": 0.78,
  "centrality_score": 0.45,
  "graph_reason_codes": [
    "PART_OF_KNOWN_CAMPAIGN",
    "HIGH_COMPLAINT_DEGREE"
  ]
}
```

## GET /calls

List recent call events.

**Query Parameters:**
- `limit` (int, default 20)
- `offset` (int, default 0)
- `risk_label` (string, optional)

**Response 200:**
```json
{
  "calls": [
    {
      "call_id": "call_001",
      "phone_number_hash": "hash_abc123",
      "risk_score": 0.87,
      "risk_label": "High Risk",
      "timestamp": "2026-04-27T10:30:00Z"
    }
  ],
  "total": 150,
  "limit": 20,
  "offset": 0
}
```
