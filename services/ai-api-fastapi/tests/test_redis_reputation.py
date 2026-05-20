import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from app.modules.redis_reputation import RedisReputationService, ReputationPayload


# ── ReputationPayload Tests ──

class TestReputationPayload:
    def test_default_payload(self):
        p = ReputationPayload(phone_number_hash="hash_123")
        assert p.phone_number_hash == "hash_123"
        assert p.complaint_count_7d == 0
        assert p.known_business is False
        assert p.business_verified is False
        assert p.known_scam_cluster is False
        assert p.blocklist_match is False
        assert p.allowlist_match is False

    def test_full_payload(self):
        p = ReputationPayload(
            phone_number_hash="hash_scam",
            complaint_count_7d=25,
            complaint_count_30d=100,
            known_business=False,
            business_verified=False,
            known_scam_cluster=True,
            campaign_cluster_id="campaign_42",
            previous_risk_label="High Risk",
            previous_risk_score=0.92,
            blocklist_match=True,
            allowlist_match=False,
            first_seen_days_ago=3,
            number_age_days=3,
        )
        assert p.complaint_count_7d == 25
        assert p.known_scam_cluster is True
        assert p.previous_risk_score == 0.92

    def test_serialize_deserialize(self):
        original = ReputationPayload(
            phone_number_hash="hash_test",
            complaint_count_7d=10,
            known_business=True,
            business_verified=True,
            business_name="Test Corp",
        )
        json_str = original.to_json()
        restored = ReputationPayload.from_json(json_str)
        assert restored.phone_number_hash == "hash_test"
        assert restored.complaint_count_7d == 10
        assert restored.known_business is True
        assert restored.business_name == "Test Corp"

    def test_json_roundtrip_preserves_all_fields(self):
        original = ReputationPayload(
            phone_number_hash="hash_rt",
            complaint_count_7d=5,
            complaint_count_30d=20,
            known_scam_cluster=True,
            campaign_cluster_id="c_99",
            blocklist_match=True,
        )
        restored = ReputationPayload.from_json(original.to_json())
        assert restored.complaint_count_30d == 20
        assert restored.campaign_cluster_id == "c_99"
        assert restored.blocklist_match is True


# ── RedisReputationService Tests (Mocked) ──

class TestRedisServiceGracefulFallback:
    """Tests that the service handles Redis being unavailable gracefully."""

    def test_not_connected_by_default(self):
        service = RedisReputationService()
        assert service.is_connected is False

    @pytest.mark.asyncio
    async def test_get_reputation_returns_none_when_disconnected(self):
        service = RedisReputationService()
        result = await service.get_number_reputation("hash_123")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_reputation_returns_false_when_disconnected(self):
        service = RedisReputationService()
        payload = ReputationPayload(phone_number_hash="hash_123")
        result = await service.set_number_reputation("hash_123", payload)
        assert result is False

    @pytest.mark.asyncio
    async def test_get_business_returns_none_when_disconnected(self):
        service = RedisReputationService()
        result = await service.get_business_identity("biz_001")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_recent_risk_returns_none_when_disconnected(self):
        service = RedisReputationService()
        result = await service.get_recent_risk("hash_123")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_carrier_risk_returns_none_when_disconnected(self):
        service = RedisReputationService()
        result = await service.get_carrier_risk("carrier_001")
        assert result is None


class TestRedisServiceWithMockClient:
    """Tests with a mocked Redis client to verify correct behavior."""

    def _make_service_with_mock(self):
        service = RedisReputationService()
        mock_client = AsyncMock()
        service._client = mock_client
        return service, mock_client

    @pytest.mark.asyncio
    async def test_get_reputation_found(self):
        service, mock_client = self._make_service_with_mock()
        payload = ReputationPayload(
            phone_number_hash="hash_abc",
            complaint_count_7d=15,
            known_scam_cluster=True,
        )
        mock_client.get = AsyncMock(return_value=payload.to_json())

        result = await service.get_number_reputation("hash_abc")
        assert result is not None
        assert result.phone_number_hash == "hash_abc"
        assert result.complaint_count_7d == 15
        assert result.known_scam_cluster is True
        mock_client.get.assert_called_once_with("reputation:hash_abc")

    @pytest.mark.asyncio
    async def test_get_reputation_not_found(self):
        service, mock_client = self._make_service_with_mock()
        mock_client.get = AsyncMock(return_value=None)

        result = await service.get_number_reputation("hash_unknown")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_reputation_success(self):
        service, mock_client = self._make_service_with_mock()
        mock_client.set = AsyncMock(return_value=True)
        payload = ReputationPayload(phone_number_hash="hash_new", complaint_count_7d=3)

        result = await service.set_number_reputation("hash_new", payload, ttl=600)
        assert result is True
        mock_client.set.assert_called_once()
        call_args = mock_client.set.call_args
        assert call_args[0][0] == "reputation:hash_new"
        assert call_args[1]["ex"] == 600

    @pytest.mark.asyncio
    async def test_get_reputation_handles_exception(self):
        service, mock_client = self._make_service_with_mock()
        mock_client.get = AsyncMock(side_effect=Exception("Connection lost"))

        result = await service.get_number_reputation("hash_err")
        assert result is None  # Graceful fallback

    @pytest.mark.asyncio
    async def test_set_reputation_handles_exception(self):
        service, mock_client = self._make_service_with_mock()
        mock_client.set = AsyncMock(side_effect=Exception("Connection lost"))
        payload = ReputationPayload(phone_number_hash="hash_err")

        result = await service.set_number_reputation("hash_err", payload)
        assert result is False  # Graceful fallback

    @pytest.mark.asyncio
    async def test_set_and_get_business_identity(self):
        service, mock_client = self._make_service_with_mock()
        biz_data = {"name": "Chase Bank", "verified": True}
        mock_client.set = AsyncMock(return_value=True)
        mock_client.get = AsyncMock(return_value=json.dumps(biz_data))

        await service.set_business_identity("biz_001", biz_data)
        result = await service.get_business_identity("biz_001")
        assert result["name"] == "Chase Bank"
        assert result["verified"] is True

    @pytest.mark.asyncio
    async def test_set_and_get_recent_risk(self):
        service, mock_client = self._make_service_with_mock()
        risk_data = {"risk_score": 0.87, "risk_label": "High Risk"}
        mock_client.set = AsyncMock(return_value=True)
        mock_client.get = AsyncMock(return_value=json.dumps(risk_data))

        await service.set_recent_risk("hash_risk", risk_data)
        result = await service.get_recent_risk("hash_risk")
        assert result["risk_score"] == 0.87
        assert result["risk_label"] == "High Risk"

    @pytest.mark.asyncio
    async def test_set_and_get_carrier_risk(self):
        service, mock_client = self._make_service_with_mock()
        carrier_data = {"risk_level": "medium", "spam_rate": 0.15}
        mock_client.set = AsyncMock(return_value=True)
        mock_client.get = AsyncMock(return_value=json.dumps(carrier_data))

        await service.set_carrier_risk("carrier_001", carrier_data)
        result = await service.get_carrier_risk("carrier_001")
        assert result["risk_level"] == "medium"
