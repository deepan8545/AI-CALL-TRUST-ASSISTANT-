-- AI Call Trust Assistant — PostgreSQL Schema
-- Day 3: Initial schema creation

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================
-- businesses
-- =====================
CREATE TABLE IF NOT EXISTS businesses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    verification_status VARCHAR(50) NOT NULL DEFAULT 'unverified',
    verified_phone_hashes TEXT[] DEFAULT '{}',
    brand_display_name VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_businesses_verification_status ON businesses(verification_status);
CREATE INDEX idx_businesses_name ON businesses(name);

-- =====================
-- call_events
-- =====================
CREATE TABLE IF NOT EXISTS call_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone_number_hash VARCHAR(255) NOT NULL,
    carrier_id VARCHAR(100) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    user_region VARCHAR(20) NOT NULL,
    business_identity_id UUID REFERENCES businesses(id),
    call_duration_seconds INTEGER NOT NULL DEFAULT 0,
    answered BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_call_events_phone_hash ON call_events(phone_number_hash);
CREATE INDEX idx_call_events_timestamp ON call_events(timestamp DESC);
CREATE INDEX idx_call_events_carrier ON call_events(carrier_id);

-- =====================
-- risk_scores
-- =====================
CREATE TABLE IF NOT EXISTS risk_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    call_id UUID NOT NULL REFERENCES call_events(id),
    risk_score NUMERIC(4,3) NOT NULL CHECK (risk_score >= 0 AND risk_score <= 1),
    risk_label VARCHAR(50) NOT NULL,
    reason_codes TEXT[] NOT NULL DEFAULT '{}',
    model_version VARCHAR(50) DEFAULT 'rules_v1',
    graph_feature_version VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_risk_scores_call_id ON risk_scores(call_id);
CREATE INDEX idx_risk_scores_label ON risk_scores(risk_label);
CREATE INDEX idx_risk_scores_score ON risk_scores(risk_score DESC);

-- =====================
-- call_summaries
-- =====================
CREATE TABLE IF NOT EXISTS call_summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    call_id UUID NOT NULL REFERENCES call_events(id),
    summary TEXT NOT NULL,
    action_items TEXT[] DEFAULT '{}',
    sensitive_request_detected BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_call_summaries_call_id ON call_summaries(call_id);

-- =====================
-- scam_patterns
-- =====================
CREATE TABLE IF NOT EXISTS scam_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern_name VARCHAR(255) NOT NULL,
    pattern_text TEXT NOT NULL,
    embedding_id VARCHAR(255),
    category VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_scam_patterns_category ON scam_patterns(category);

-- =====================
-- model_decisions
-- =====================
CREATE TABLE IF NOT EXISTS model_decisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    call_id UUID NOT NULL REFERENCES call_events(id),
    rules_score NUMERIC(4,3),
    ml_score NUMERIC(4,3),
    graph_score NUMERIC(4,3),
    transcript_score NUMERIC(4,3),
    final_score NUMERIC(4,3) NOT NULL,
    final_label VARCHAR(50) NOT NULL,
    explanation TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_model_decisions_call_id ON model_decisions(call_id);
CREATE INDEX idx_model_decisions_label ON model_decisions(final_label);
