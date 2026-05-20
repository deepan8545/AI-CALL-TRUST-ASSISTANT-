import pytest
from unittest.mock import AsyncMock
from app.modules.database import Database


class TestDatabaseModule:
    def test_not_connected_by_default(self):
        db = Database()
        assert db.is_connected is False

    @pytest.mark.asyncio
    async def test_fetch_raises_when_not_connected(self):
        db = Database()
        with pytest.raises(ConnectionError, match="Database not connected"):
            await db.fetch("SELECT 1")

    @pytest.mark.asyncio
    async def test_fetchrow_raises_when_not_connected(self):
        db = Database()
        with pytest.raises(ConnectionError, match="Database not connected"):
            await db.fetchrow("SELECT 1")

    @pytest.mark.asyncio
    async def test_execute_raises_when_not_connected(self):
        db = Database()
        with pytest.raises(ConnectionError, match="Database not connected"):
            await db.execute("SELECT 1")

    def test_is_connected_true_when_pool_set(self):
        db = Database()
        db.pool = "fake_pool"
        assert db.is_connected is True

    @pytest.mark.asyncio
    async def test_disconnect_when_no_pool(self):
        db = Database()
        await db.disconnect()  # Should not raise
