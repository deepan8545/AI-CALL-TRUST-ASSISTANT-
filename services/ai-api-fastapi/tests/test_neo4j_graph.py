import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.modules.neo4j_graph import Neo4jService, GraphRiskFeatures


class TestGraphRiskFeatures:
    def test_default_features(self):
        f = GraphRiskFeatures()
        assert f.complaint_count == 0
        assert f.direct_campaign_count == 0
        assert f.similar_campaign_count == 0
        assert f.community_risk_score == 0.0
        assert f.centrality_score == 0.0
        assert f.graph_reason_codes == []

    def test_custom_features(self):
        f = GraphRiskFeatures(
            complaint_count=15,
            direct_campaign_count=2,
            similar_campaign_count=5,
            community_risk_score=0.78,
            centrality_score=0.45,
            graph_reason_codes=["PART_OF_KNOWN_CAMPAIGN", "HIGH_COMPLAINT_DEGREE"],
        )
        assert f.complaint_count == 15
        assert f.direct_campaign_count == 2
        assert len(f.graph_reason_codes) == 2


class TestNeo4jGracefulFallback:
    def test_not_connected_by_default(self):
        service = Neo4jService()
        assert service.is_connected is False

    @pytest.mark.asyncio
    async def test_get_features_returns_none_when_disconnected(self):
        service = Neo4jService()
        result = await service.get_graph_risk_features("hash_123")
        assert result is None

    @pytest.mark.asyncio
    async def test_disconnect_when_no_driver(self):
        service = Neo4jService()
        await service.disconnect()  # Should not raise


class TestNeo4jWithMockDriver:
    def _make_service_with_mock(self, record_data=None):
        service = Neo4jService()
        mock_driver = AsyncMock()
        mock_session = AsyncMock()
        mock_result = AsyncMock()

        if record_data is not None:
            mock_record = MagicMock()
            mock_record.__getitem__ = lambda self, key: record_data[key]
            mock_result.single = AsyncMock(return_value=mock_record)
        else:
            mock_result.single = AsyncMock(return_value=None)

        mock_session.run = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_driver.session = MagicMock(return_value=mock_session)

        service._driver = mock_driver
        return service

    @pytest.mark.asyncio
    async def test_scam_number_returns_high_risk_features(self):
        service = self._make_service_with_mock({
            "phone_number_hash": "hash_scam_001",
            "reputation_score": 0.08,
            "complaint_count": 22,
            "direct_campaign_count": 1,
            "similar_campaign_count": 3,
            "pattern_match_count": 2,
            "campaign_ids": ["campaign_bank_verify"],
            "matched_patterns": ["bank_impersonation"],
        })

        result = await service.get_graph_risk_features("hash_scam_001")
        assert result is not None
        assert result.complaint_count == 22
        assert result.direct_campaign_count == 1
        assert result.similar_campaign_count == 3
        assert "PART_OF_KNOWN_CAMPAIGN" in result.graph_reason_codes
        assert "SIMILAR_TO_SCAM_CLUSTER" in result.graph_reason_codes
        assert "HIGH_COMPLAINT_DEGREE" in result.graph_reason_codes
        assert "MATCHES_KNOWN_SCAM_PATTERN" in result.graph_reason_codes
        assert result.community_risk_score > 0
        assert result.centrality_score > 0

    @pytest.mark.asyncio
    async def test_safe_number_returns_clean_features(self):
        service = self._make_service_with_mock({
            "phone_number_hash": "hash_united_001",
            "reputation_score": 0.95,
            "complaint_count": 0,
            "direct_campaign_count": 0,
            "similar_campaign_count": 0,
            "pattern_match_count": 0,
            "campaign_ids": [],
            "matched_patterns": [],
        })

        result = await service.get_graph_risk_features("hash_united_001")
        assert result is not None
        assert result.complaint_count == 0
        assert result.direct_campaign_count == 0
        assert result.graph_reason_codes == []
        assert result.community_risk_score == 0.0
        assert result.centrality_score == 0.0

    @pytest.mark.asyncio
    async def test_unknown_number_not_in_graph(self):
        service = self._make_service_with_mock(record_data=None)
        result = await service.get_graph_risk_features("hash_unknown")
        assert result is not None  # Returns empty defaults
        assert result.complaint_count == 0
        assert result.graph_reason_codes == []

    @pytest.mark.asyncio
    async def test_moderate_complaints_reason_code(self):
        service = self._make_service_with_mock({
            "phone_number_hash": "hash_mod",
            "reputation_score": 0.5,
            "complaint_count": 5,
            "direct_campaign_count": 0,
            "similar_campaign_count": 0,
            "pattern_match_count": 0,
            "campaign_ids": [],
            "matched_patterns": [],
        })

        result = await service.get_graph_risk_features("hash_mod")
        assert "MODERATE_COMPLAINT_DEGREE" in result.graph_reason_codes

    @pytest.mark.asyncio
    async def test_handles_driver_exception(self):
        service = Neo4jService()
        mock_driver = AsyncMock()
        mock_session = AsyncMock()
        mock_session.run = AsyncMock(side_effect=Exception("Connection lost"))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_driver.session = MagicMock(return_value=mock_session)
        service._driver = mock_driver

        result = await service.get_graph_risk_features("hash_err")
        assert result is None  # Graceful fallback

    @pytest.mark.asyncio
    async def test_community_risk_score_capped_at_one(self):
        service = self._make_service_with_mock({
            "phone_number_hash": "hash_max",
            "reputation_score": 0.01,
            "complaint_count": 50,
            "direct_campaign_count": 5,
            "similar_campaign_count": 10,
            "pattern_match_count": 8,
            "campaign_ids": ["c1", "c2", "c3", "c4", "c5"],
            "matched_patterns": ["a", "b", "c"],
        })

        result = await service.get_graph_risk_features("hash_max")
        assert result.community_risk_score <= 1.0
        assert result.centrality_score <= 1.0
