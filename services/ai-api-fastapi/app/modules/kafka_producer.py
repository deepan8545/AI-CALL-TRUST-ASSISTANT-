"""
Kafka producer for publishing scored call events.
Publishes to call.scored topic after each successful /score-call.
Graceful fallback if Kafka is unavailable.
"""

import os
import json
import logging
from typing import Optional
from datetime import datetime, timezone

try:
    from aiokafka import AIOKafkaProducer
    HAS_KAFKA = True
except ImportError:
    HAS_KAFKA = False

logger = logging.getLogger(__name__)


class KafkaProducerService:
    """Async Kafka producer with graceful fallback."""

    def __init__(self):
        self._producer: Optional[object] = None
        self._bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self._topic_scored = os.getenv("KAFKA_TOPIC_CALL_SCORED", "call.scored")
        self._topic_events = os.getenv("KAFKA_TOPIC_CALL_EVENTS", "call.events")

    async def connect(self):
        if not HAS_KAFKA:
            logger.warning("aiokafka not installed — Kafka disabled")
            return
        try:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self._bootstrap_servers,
                value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
                request_timeout_ms=5000,
            )
            await self._producer.start()
            logger.info("Kafka producer connected")
        except Exception as e:
            logger.error(f"Failed to connect Kafka producer: {e}")
            self._producer = None

    async def disconnect(self):
        if self._producer:
            await self._producer.stop()
            logger.info("Kafka producer disconnected")

    @property
    def is_connected(self) -> bool:
        return self._producer is not None

    async def publish_scored_call(self, call_id: str, request, response) -> bool:
        """Publish a scored call event to Kafka. Returns False if unavailable."""
        if not self._producer:
            logger.debug("Kafka not available — skipping publish")
            return False
        try:
            event = {
                "call_id": call_id,
                "phone_number_hash": request.phone_number_hash,
                "carrier_id": request.carrier_id,
                "timestamp": request.timestamp.isoformat(),
                "user_region": request.user_region,
                "risk_score": response.risk_score,
                "risk_label": response.risk_label.value if hasattr(response.risk_label, 'value') else response.risk_label,
                "reason_codes": response.reason_codes,
                "scored_at": datetime.now(timezone.utc).isoformat(),
            }
            await self._producer.send_and_wait(self._topic_scored, event)
            logger.info(f"Published scored call {call_id} to {self._topic_scored}")
            return True
        except Exception as e:
            logger.warning(f"Kafka publish failed (graceful fallback): {e}")
            return False

    async def publish_call_event(self, event_data: dict) -> bool:
        """Publish a raw call event to Kafka."""
        if not self._producer:
            return False
        try:
            await self._producer.send_and_wait(self._topic_events, event_data)
            return True
        except Exception as e:
            logger.warning(f"Kafka publish call event failed: {e}")
            return False


# Singleton
kafka_producer = KafkaProducerService()
