from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


# --- Enums ---

class RiskLabel(str, Enum):
    SAFE = "Safe"
    UNKNOWN = "Unknown"
    SUSPICIOUS = "Suspicious"
    HIGH_RISK = "High Risk"


# --- Score Call ---

class CallMetadata(BaseModel):
    call_frequency_24h: int = Field(ge=0, description="Calls from this number in last 24h")
    call_frequency_7d: int = Field(ge=0, description="Calls from this number in last 7d")
    spoofing_signal: bool = False
    answered_before: bool = False


class ScoreCallRequest(BaseModel):
    phone_number_hash: str = Field(min_length=1, description="Hashed phone number")
    carrier_id: str = Field(min_length=1)
    timestamp: datetime
    call_duration_seconds: int = Field(ge=0, default=0)
    user_region: str = Field(min_length=1)
    business_identity_id: Optional[str] = None
    call_metadata: CallMetadata


class ScoreCallResponse(BaseModel):
    call_id: str
    risk_score: float = Field(ge=0.0, le=1.0)
    risk_label: RiskLabel
    reason_codes: list[str]
    recommended_action: str
    explanation: str


# --- Ingest Call Event ---

class IngestCallEventRequest(BaseModel):
    phone_number_hash: str = Field(min_length=1)
    carrier_id: str = Field(min_length=1)
    timestamp: datetime
    call_duration_seconds: int = Field(ge=0, default=0)
    user_region: str = Field(min_length=1)
    business_identity_id: Optional[str] = None
    answered: bool = False


class IngestCallEventResponse(BaseModel):
    event_id: str
    status: str = "ingested"
    timestamp: datetime


# --- Analyze Transcript ---

class AnalyzeTranscriptRequest(BaseModel):
    call_id: str = Field(min_length=1)
    transcript: str = Field(min_length=1, description="Call transcript text")


class AnalyzeTranscriptResponse(BaseModel):
    detected_intents: list[str]
    transcript_risk_score: float = Field(ge=0.0, le=1.0)
    reason_codes: list[str]


# --- Summarize Call ---

class SummarizeCallRequest(BaseModel):
    call_id: str = Field(min_length=1)
    transcript: str = Field(min_length=1)
    risk_label: RiskLabel
    reason_codes: list[str]


class SummarizeCallResponse(BaseModel):
    summary: str
    action_items: list[str]
    sensitive_request_detected: bool
    user_warning: str


# --- Graph Risk ---

class GraphRiskRequest(BaseModel):
    phone_number_hash: str = Field(min_length=1)


class GraphRiskResponse(BaseModel):
    complaint_count: int = 0
    direct_campaign_count: int = 0
    similar_campaign_count: int = 0
    community_risk_score: float = Field(ge=0.0, le=1.0, default=0.0)
    centrality_score: float = Field(ge=0.0, le=1.0, default=0.0)
    graph_reason_codes: list[str] = []


# --- List Calls ---

class CallSummaryItem(BaseModel):
    call_id: str
    phone_number_hash: str
    risk_score: float
    risk_label: RiskLabel
    timestamp: datetime


class ListCallsResponse(BaseModel):
    calls: list[CallSummaryItem]
    total: int
    limit: int
    offset: int


# --- Health ---

class ServiceStatus(BaseModel):
    database: str = "not_connected"
    redis: str = "not_connected"
    kafka: str = "not_connected"
    neo4j: str = "not_connected"


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "0.1.0"
    services: ServiceStatus = ServiceStatus()
