import os
import json
import logging
from typing import Optional
from dataclasses import dataclass, asdict

try:
    import redis.asyncio as aioredis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

logger = logging.getLogger(__name__)


@dataclass
class ReputationPayload:
    """Cached reputation data for a phone number."""
    phone_number_hash: str
    complaint_count_7d: int = 0
    complaint_count_30d: int = 0
    known_business: bool = False
    business_verified: bool = False
    business_name: Optional[str] = None
    known_scam_cluster: bool = False
    campaign_cluster_id: Optional[str] = None
    previous_risk_label: Optional[str] = None
    previous_risk_score: Optional[float] = None
    blocklist_match: bool = False
    allowlist_match: bool = False
    first_seen_days_ago: int = 0
    number_age_days: int = 0

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> "ReputationPayload":
        return cls(**json.loads(data))


class RedisReputationService:
    """Low-latency reputation lookup with graceful fallback."""

    DEFAULT_TTL = 3600  # 1 hour

    def __init__(self):
        self._client: Optional[object] = None
        self._host = os.getenv("REDIS_HOST", "localhost")
        self._port = int(os.getenv("REDIS_PORT", "6379"))
        self._db = int(os.getenv("REDIS_DB", "0"))
        self._password = os.getenv("REDIS_PASSWORD", None)

    async def connect(self):
        if not HAS_REDIS:
            logger.warning("redis package not installed — Redis disabled")
            return
        try:
            self._client = aioredis.Redis(
                host=self._host,
                port=self._port,
                db=self._db,
                password=self._password,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
            await self._client.ping()
            logger.info("Redis connected")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._client = None

    async def disconnect(self):
        if self._client:
            await self._client.close()
            logger.info("Redis disconnected")

    @property
    def is_connected(self) -> bool:
        return self._client is not None

    # --- Reputation ---

    async def get_number_reputation(self, phone_number_hash: str) -> Optional[ReputationPayload]:
        """Look up cached reputation. Returns None if Redis unavailable or key missing."""
        if not self._client:
            logger.debug("Redis not available — returning None for reputation lookup")
            return None
        try:
            key = f"reputation:{phone_number_hash}"
            data = await self._client.get(key)
            if data is None:
                return None
            return ReputationPayload.from_json(data)
        except Exception as e:
            logger.warning(f"Redis get failed (graceful fallback): {e}")
            return None

    async def set_number_reputation(
        self,
        phone_number_hash: str,
        payload: ReputationPayload,
        ttl: int = DEFAULT_TTL,
    ) -> bool:
        """Cache reputation data. Returns False if Redis unavailable."""
        if not self._client:
            logger.debug("Redis not available — skipping reputation cache write")
            return False
        try:
            key = f"reputation:{phone_number_hash}"
            await self._client.set(key, payload.to_json(), ex=ttl)
            return True
        except Exception as e:
            logger.warning(f"Redis set failed (graceful fallback): {e}")
            return False

    # --- Business Identity ---

    async def get_business_identity(self, business_identity_id: str) -> Optional[dict]:
        """Look up cached business identity."""
        if not self._client:
            return None
        try:
            key = f"business:{business_identity_id}"
            data = await self._client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.warning(f"Redis business lookup failed: {e}")
            return None

    async def set_business_identity(self, business_identity_id: str, payload: dict, ttl: int = 7200) -> bool:
        """Cache business identity data."""
        if not self._client:
            return False
        try:
            key = f"business:{business_identity_id}"
            await self._client.set(key, json.dumps(payload), ex=ttl)
            return True
        except Exception as e:
            logger.warning(f"Redis business set failed: {e}")
            return False

    # --- Recent Risk ---

    async def get_recent_risk(self, phone_number_hash: str) -> Optional[dict]:
        """Look up most recent risk score for a number."""
        if not self._client:
            return None
        try:
            key = f"recent-risk:{phone_number_hash}"
            data = await self._client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.warning(f"Redis recent-risk lookup failed: {e}")
            return None

    async def set_recent_risk(self, phone_number_hash: str, risk_data: dict, ttl: int = 1800) -> bool:
        """Cache recent risk score."""
        if not self._client:
            return False
        try:
            key = f"recent-risk:{phone_number_hash}"
            await self._client.set(key, json.dumps(risk_data), ex=ttl)
            return True
        except Exception as e:
            logger.warning(f"Redis recent-risk set failed: {e}")
            return False

    # --- Carrier Risk ---

    async def get_carrier_risk(self, carrier_id: str) -> Optional[dict]:
        """Look up carrier-level risk data."""
        if not self._client:
            return None
        try:
            key = f"carrier-risk:{carrier_id}"
            data = await self._client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.warning(f"Redis carrier-risk lookup failed: {e}")
            return None

    async def set_carrier_risk(self, carrier_id: str, payload: dict, ttl: int = 3600) -> bool:
        """Cache carrier risk data."""
        if not self._client:
            return False
        try:
            key = f"carrier-risk:{carrier_id}"
            await self._client.set(key, json.dumps(payload), ex=ttl)
            return True
        except Exception as e:
            logger.warning(f"Redis carrier-risk set failed: {e}")
            return False


# Singleton instance
redis_service = RedisReputationService()
