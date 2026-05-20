import pytest
from unittest.mock import AsyncMock, MagicMock
from app.modules.kafka_producer import KafkaProducerService


class TestKafkaGracefulFallback:
    def test_not_connected_by_default(self):
        service = KafkaProducerService()
        assert service.is_connected is False

    @pytest.mark.asyncio
    async def test_publish_returns_false_when_disconnected(self):
        service = KafkaProducerService()
        result = await service.publish_scored_call("call_1", MagicMock(), MagicMock())
        assert result is False

    @pytest.mark.asyncio
    async def test_publish_event_returns_false_when_disconnected(self):
        service = KafkaProducerService()
        result = await service.publish_call_event({"test": True})
        assert result is False


class TestKafkaWithMockProducer:
    def _make_service(self):
        service = KafkaProducerService()
        mock_producer = AsyncMock()
        mock_producer.send_and_wait = AsyncMock(return_value=True)
        service._producer = mock_producer
        return service, mock_producer

    @pytest.mark.asyncio
    async def test_publish_scored_call_success(self):
        service, mock = self._make_service()

        request = MagicMock()
        request.phone_number_hash = "hash_123"
        request.carrier_id = "carrier_001"
        request.timestamp.isoformat.return_value = "2026-05-10T10:00:00Z"
        request.user_region = "US-IL"

        response = MagicMock()
        response.risk_score = 0.87
        response.risk_label.value = "High Risk"
        response.reason_codes = ["HIGH_COMPLAINT_VOLUME"]

        result = await service.publish_scored_call("call_001", request, response)
        assert result is True
        mock.send_and_wait.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_scored_call_handles_exception(self):
        service, mock = self._make_service()
        mock.send_and_wait = AsyncMock(side_effect=Exception("Kafka down"))

        result = await service.publish_scored_call("call_err", MagicMock(), MagicMock())
        assert result is False

    @pytest.mark.asyncio
    async def test_publish_call_event_success(self):
        service, mock = self._make_service()
        result = await service.publish_call_event({"event": "test"})
        assert result is True

    @pytest.mark.asyncio
    async def test_publish_call_event_handles_exception(self):
        service, mock = self._make_service()
        mock.send_and_wait = AsyncMock(side_effect=Exception("Kafka down"))
        result = await service.publish_call_event({"event": "fail"})
        assert result is False
