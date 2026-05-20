"""
Neo4j graph intelligence module.
Queries graph-derived risk features for phone numbers.
Graceful fallback if Neo4j is unavailable.
"""

import os
import logging
from typing import Optional
from dataclasses import dataclass, field

try:
    from neo4j import AsyncGraphDatabase
    HAS_NEO4J = True
except ImportError:
    HAS_NEO4J = False

logger = logging.getLogger(__name__)


@dataclass
class GraphRiskFeatures:
    complaint_count: int = 0
    direct_campaign_count: int = 0
    similar_campaign_count: int = 0
    community_risk_score: float = 0.0
    centrality_score: float = 0.0
    graph_reason_codes: list[str] = field(default_factory=list)


GRAPH_RISK_QUERY = """
MATCH (p:PhoneNumber {phone_number_hash: $phone_number_hash})
OPTIONAL MATCH (p)-[:PART_OF_CAMPAIGN]->(c:ScamCampaign)
OPTIONAL MATCH (p)-[:REPORTED_IN]->(r:Complaint)
OPTIONAL MATCH (p)-[:SIMILAR_BEHAVIOR_TO]->(other:PhoneNumber)-[:PART_OF_CAMPAIGN]->(oc:ScamCampaign)
OPTIONAL MATCH (p)-[:MATCHES_PATTERN]->(pat:ScamPattern)
RETURN
  p.phone_number_hash AS phone_number_hash,
  p.reputation_score AS reputation_score,
  count(DISTINCT r) AS complaint_count,
  count(DISTINCT c) AS direct_campaign_count,
  count(DISTINCT oc) AS similar_campaign_count,
  count(DISTINCT pat) AS pattern_match_count,
  collect(DISTINCT c.campaign_id) AS campaign_ids,
  collect(DISTINCT pat.category) AS matched_patterns
"""


class Neo4jService:
    """Neo4j graph database connector with graceful fallback."""

    def __init__(self):
        self._driver = None
        self._uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self._user = os.getenv("NEO4J_USER", "neo4j")
        self._password = os.getenv("NEO4J_PASSWORD", "calltrust_pass")

    async def connect(self):
        if not HAS_NEO4J:
            logger.warning("neo4j driver not installed — Neo4j disabled")
            return
        try:
            self._driver = AsyncGraphDatabase.driver(
                self._uri, auth=(self._user, self._password)
            )
            await self._driver.verify_connectivity()
            logger.info("Neo4j connected")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self._driver = None

    async def disconnect(self):
        if self._driver:
            await self._driver.close()
            logger.info("Neo4j disconnected")

    @property
    def is_connected(self) -> bool:
        return self._driver is not None

    async def get_graph_risk_features(self, phone_number_hash: str) -> Optional[GraphRiskFeatures]:
        """Query Neo4j for graph-derived risk features. Returns None if unavailable."""
        if not self._driver:
            logger.debug("Neo4j not available — returning None")
            return None
        try:
            async with self._driver.session() as session:
                result = await session.run(GRAPH_RISK_QUERY, phone_number_hash=phone_number_hash)
                record = await result.single()

                if record is None:
                    return GraphRiskFeatures()  # Number not in graph

                complaint_count = record["complaint_count"]
                direct_campaign_count = record["direct_campaign_count"]
                similar_campaign_count = record["similar_campaign_count"]
                pattern_match_count = record["pattern_match_count"]
                reputation_score = record["reputation_score"] or 0.5

                # Build reason codes from graph signals
                reason_codes = []
                if direct_campaign_count > 0:
                    reason_codes.append("PART_OF_KNOWN_CAMPAIGN")
                if similar_campaign_count > 0:
                    reason_codes.append("SIMILAR_TO_SCAM_CLUSTER")
                if complaint_count >= 10:
                    reason_codes.append("HIGH_COMPLAINT_DEGREE")
                elif complaint_count >= 3:
                    reason_codes.append("MODERATE_COMPLAINT_DEGREE")
                if pattern_match_count > 0:
                    reason_codes.append("MATCHES_KNOWN_SCAM_PATTERN")

                # Community risk score (simplified — placeholder for GDS algorithms)
                total_signals = direct_campaign_count + similar_campaign_count + complaint_count + pattern_match_count
                community_risk = min(1.0, total_signals * 0.08)

                # Centrality score (simplified placeholder)
                centrality = min(1.0, (direct_campaign_count * 0.2 + similar_campaign_count * 0.1))

                return GraphRiskFeatures(
                    complaint_count=complaint_count,
                    direct_campaign_count=direct_campaign_count,
                    similar_campaign_count=similar_campaign_count,
                    community_risk_score=round(community_risk, 3),
                    centrality_score=round(centrality, 3),
                    graph_reason_codes=reason_codes,
                )
        except Exception as e:
            logger.warning(f"Neo4j query failed (graceful fallback): {e}")
            return None


# Singleton
neo4j_service = Neo4jService()
