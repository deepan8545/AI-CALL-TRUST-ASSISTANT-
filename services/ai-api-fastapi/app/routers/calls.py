import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Query

from app.schemas.models import (
    ScoreCallRequest, ScoreCallResponse,
    IngestCallEventRequest, IngestCallEventResponse,
    AnalyzeTranscriptRequest, AnalyzeTranscriptResponse,
    SummarizeCallRequest, SummarizeCallResponse,
    GraphRiskRequest, GraphRiskResponse,
    ListCallsResponse, CallSummaryItem,
    HealthResponse, ServiceStatus,
    RiskLabel,
)
from app.modules.database import db
from app.modules.redis_reputation import redis_service
from app.modules.kafka_producer import kafka_producer
from app.modules.neo4j_graph import neo4j_service

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        services=ServiceStatus(
            database="connected" if db.is_connected else "not_connected",
            redis="connected" if redis_service.is_connected else "not_connected",
            kafka="connected" if kafka_producer.is_connected else "not_connected",
            neo4j="connected" if neo4j_service.is_connected else "not_connected",
        ),
    )


@router.post("/score-call", response_model=ScoreCallResponse)
async def score_call(request: ScoreCallRequest):
    """Score an incoming call using rules + graph intelligence."""
    from app.modules.rules_scorer import score_call as rules_score_call

    call_id = f"call_{uuid.uuid4().hex[:8]}"

    # Attempt Redis reputation lookup (graceful fallback to None)
    reputation = await redis_service.get_number_reputation(request.phone_number_hash)

    # Attempt Neo4j graph features (graceful fallback to None)
    graph_features = await neo4j_service.get_graph_risk_features(request.phone_number_hash)

    # Run rule-based scoring
    result = rules_score_call(
        call_frequency_24h=request.call_metadata.call_frequency_24h,
        call_frequency_7d=request.call_metadata.call_frequency_7d,
        spoofing_signal=request.call_metadata.spoofing_signal,
        answered_before=request.call_metadata.answered_before,
        business_identity_id=request.business_identity_id,
        reputation=reputation,
    )

    # Blend graph score into final score (Day 7)
    final_score = result.risk_score
    all_reason_codes = list(result.reason_codes)

    if graph_features and graph_features.graph_reason_codes:
        graph_weight = 0.25
        rules_weight = 0.75
        final_score = round(
            (rules_weight * result.risk_score) + (graph_weight * graph_features.community_risk_score),
            3,
        )
        final_score = max(0.0, min(1.0, final_score))
        # Merge graph reason codes (deduplicated)
        for code in graph_features.graph_reason_codes:
            if code not in all_reason_codes:
                all_reason_codes.append(code)

    # Re-derive label from blended score
    from app.modules.rules_scorer import _label_from_score, RECOMMENDATIONS
    final_label = _label_from_score(final_score)

    explanation_parts = [f"Risk score {final_score:.2f} ({final_label})"]
    explanation_parts.append(f"Signals: {', '.join(all_reason_codes)}")
    if graph_features and graph_features.graph_reason_codes:
        explanation_parts.append(
            f"Graph: {graph_features.complaint_count} complaints, "
            f"{graph_features.direct_campaign_count} campaign links, "
            f"community risk {graph_features.community_risk_score:.2f}"
        )

    response = ScoreCallResponse(
        call_id=call_id,
        risk_score=final_score,
        risk_label=RiskLabel(final_label),
        reason_codes=all_reason_codes,
        recommended_action=RECOMMENDATIONS[final_label],
        explanation=". ".join(explanation_parts) + ".",
    )

    # Publish to Kafka if available
    try:
        await kafka_producer.publish_scored_call(call_id, request, response)
    except Exception:
        pass  # Kafka not connected — graceful skip

    return response


@router.post("/ingest-call-event", response_model=IngestCallEventResponse, status_code=201)
async def ingest_call_event(request: IngestCallEventRequest):
    """Ingest a raw call event for processing."""
    event_id = f"evt_{uuid.uuid4().hex[:8]}"
    return IngestCallEventResponse(
        event_id=event_id,
        status="ingested",
        timestamp=request.timestamp,
    )


@router.post("/analyze-transcript", response_model=AnalyzeTranscriptResponse)
async def analyze_transcript(request: AnalyzeTranscriptRequest):
    """Analyze a call transcript for scam signals. Stubbed."""
    return AnalyzeTranscriptResponse(
        detected_intents=["STUB_INTENT"],
        transcript_risk_score=0.0,
        reason_codes=["STUB_RESPONSE"],
    )


@router.post("/summarize-call", response_model=SummarizeCallResponse)
async def summarize_call(request: SummarizeCallRequest):
    """Generate a human-readable call summary. Stubbed."""
    return SummarizeCallResponse(
        summary="Stub summary — LLM provider not yet connected.",
        action_items=["Connect LLM provider to enable real summaries."],
        sensitive_request_detected=False,
        user_warning="",
    )


@router.post("/graph-risk", response_model=GraphRiskResponse)
async def graph_risk(request: GraphRiskRequest):
    """Get graph-derived risk features from Neo4j."""
    features = await neo4j_service.get_graph_risk_features(request.phone_number_hash)
    if features is None:
        # Neo4j unavailable — return empty defaults
        return GraphRiskResponse(
            complaint_count=0,
            direct_campaign_count=0,
            similar_campaign_count=0,
            community_risk_score=0.0,
            centrality_score=0.0,
            graph_reason_codes=["NEO4J_UNAVAILABLE"],
        )
    return GraphRiskResponse(
        complaint_count=features.complaint_count,
        direct_campaign_count=features.direct_campaign_count,
        similar_campaign_count=features.similar_campaign_count,
        community_risk_score=features.community_risk_score,
        centrality_score=features.centrality_score,
        graph_reason_codes=features.graph_reason_codes,
    )


@router.get("/calls", response_model=ListCallsResponse)
async def list_calls(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    risk_label: str | None = Query(default=None),
):
    """List recent call events. Stubbed with empty results."""
    return ListCallsResponse(
        calls=[],
        total=0,
        limit=limit,
        offset=offset,
    )
