import os
import logging
from contextlib import asynccontextmanager
from typing import Optional

try:
    import asyncpg
    HAS_ASYNCPG = True
except ImportError:
    HAS_ASYNCPG = False

logger = logging.getLogger(__name__)


class Database:
    """PostgreSQL connection pool manager."""

    def __init__(self):
        self.pool: Optional[object] = None
        self._dsn = os.getenv(
            "DATABASE_URL",
            "postgresql://call_trust_user:call_trust_pass@localhost:5432/call_trust"
        )

    async def connect(self):
        if not HAS_ASYNCPG:
            logger.warning("asyncpg not installed — database disabled")
            return
        try:
            self.pool = await asyncpg.create_pool(self._dsn, min_size=2, max_size=10)
            logger.info("PostgreSQL connection pool created")
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            self.pool = None

    async def disconnect(self):
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL connection pool closed")

    @property
    def is_connected(self) -> bool:
        return self.pool is not None

    async def fetch(self, query: str, *args):
        if not self.pool:
            raise ConnectionError("Database not connected")
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        if not self.pool:
            raise ConnectionError("Database not connected")
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def execute(self, query: str, *args):
        if not self.pool:
            raise ConnectionError("Database not connected")
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)


# Singleton instance
db = Database()
