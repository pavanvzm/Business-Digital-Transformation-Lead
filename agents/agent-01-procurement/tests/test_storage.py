"""Tests for storage layer — cache manager and repository with fallback behavior."""

from __future__ import annotations

import pytest
from src.storage.cache import CacheManager, InMemoryLRU
from src.storage.repository import ProcurementRepository


@pytest.fixture
def cache() -> CacheManager:
    """CacheManager uses in-memory LRU fallback when Redis unavailable."""
    mgr = CacheManager()
    return mgr


@pytest.fixture
def repo() -> ProcurementRepository:
    """Repository uses in-memory fallback when PostgreSQL unavailable."""
    return ProcurementRepository()


class TestInMemoryLRU:
    """In-memory LRU cache with TTL."""

    @pytest.mark.asyncio
    async def test_basic_set_get(self) -> None:
        lru = InMemoryLRU()
        await lru.set("key1", "value1", ttl_seconds=60)
        result = await lru.get("key1")
        assert result == "value1"

    @pytest.mark.asyncio
    async def test_expired_key(self) -> None:
        lru = InMemoryLRU()
        await lru.set("key_expire", "value", ttl_seconds=0)  # expired immediately
        result = await lru.get("key_expire")
        assert result is None

    @pytest.mark.asyncio
    async def test_missing_key(self) -> None:
        lru = InMemoryLRU()
        result = await lru.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_key(self) -> None:
        lru = InMemoryLRU()
        await lru.set("delete_me", "value", ttl_seconds=60)
        await lru.delete("delete_me")
        result = await lru.get("delete_me")
        assert result is None

    @pytest.mark.asyncio
    async def test_exists(self) -> None:
        lru = InMemoryLRU()
        await lru.set("exists_key", "value", ttl_seconds=60)
        assert await lru.exists("exists_key")
        assert not await lru.exists("no_key")

    @pytest.mark.asyncio
    async def test_lru_eviction(self) -> None:
        lru = InMemoryLRU(maxsize=3)
        for i in range(5):
            await lru.set(f"key{i}", f"value{i}", ttl_seconds=60)

        # First keys should be evicted
        assert await lru.get("key0") is None
        assert await lru.get("key1") is None
        # Last keys should remain
        assert await lru.get("key3") == "value3"
        assert await lru.get("key4") == "value4"

    @pytest.mark.asyncio
    async def test_clear(self) -> None:
        lru = InMemoryLRU()
        await lru.set("key1", "v1", ttl_seconds=60)
        await lru.set("key2", "v2", ttl_seconds=60)
        await lru.clear()
        assert await lru.get("key1") is None
        assert await lru.get("key2") is None


class TestCacheManager:
    """CacheManager with in-memory fallback."""

    @pytest.mark.asyncio
    async def test_connect_fallback(self, cache: CacheManager) -> None:
        """Fallback to in-memory when Redis unavailable."""
        await cache.connect()
        assert cache._memory is not None

    @pytest.mark.asyncio
    async def test_price_cache(self, cache: CacheManager) -> None:
        await cache.connect()
        await cache.set_price("MAT-COPPER-001", 8.50)
        price = await cache.get_price("MAT-COPPER-001")
        assert price == 8.50

    @pytest.mark.asyncio
    async def test_price_cache_miss(self, cache: CacheManager) -> None:
        await cache.connect()
        price = await cache.get_price("NONEXISTENT")
        assert price is None

    @pytest.mark.asyncio
    async def test_forecast_cache(self, cache: CacheManager) -> None:
        await cache.connect()
        await cache.set_forecast_demand("MAT-STEEL-001", 5000.0, "2026-06")
        demand = await cache.get_forecast_demand("MAT-STEEL-001")
        assert demand == 5000.0

    @pytest.mark.asyncio
    async def test_inventory_cache(self, cache: CacheManager) -> None:
        await cache.connect()
        await cache.set_inventory_level("MAT-STEEL-001", 1500.0, 500.0)
        level = await cache.get_inventory_level("MAT-STEEL-001")
        assert level is not None
        assert level["stock"] == 1500.0
        assert level["safety_stock"] == 500.0

    @pytest.mark.asyncio
    async def test_vendor_cache(self, cache: CacheManager) -> None:
        await cache.connect()
        vendor_data = {"name": "Test Corp", "rating": 85.0}
        await cache.set_vendor("V001", vendor_data)
        result = await cache.get_vendor("V001")
        assert result is not None
        assert result["name"] == "Test Corp"

    @pytest.mark.asyncio
    async def test_sourcing_cache(self, cache: CacheManager) -> None:
        await cache.connect()
        options = {"primary": "V001", "alternatives": ["V002", "V003"]}
        await cache.set_sourcing_options("MAT-STEEL-001", options)
        result = await cache.get_sourcing_options("MAT-STEEL-001")
        assert result is not None
        assert result["primary"] == "V001"

    @pytest.mark.asyncio
    async def test_scorecard_cache(self, cache: CacheManager) -> None:
        await cache.connect()
        scorecard = {"overall_score": 85.0, "trend": "improving"}
        await cache.set_scorecard("V001", "2026-Q2", scorecard)
        result = await cache.get_scorecard("V001", "2026-Q2")
        assert result is not None
        assert result["overall_score"] == 85.0

    @pytest.mark.asyncio
    async def test_ping_fallback(self, cache: CacheManager) -> None:
        await cache.connect()
        assert await cache.ping()  # in-memory is always "alive"


class TestProcurementRepository:
    """PostgreSQL repository with in-memory fallback."""

    @pytest.mark.asyncio
    async def test_connect_fallback(self, repo: ProcurementRepository) -> None:
        """Fallback to in-memory when PostgreSQL unavailable."""
        await repo.connect()
        assert repo._using_fallback

    @pytest.mark.asyncio
    async def test_save_and_get_vendor_scorecard(self, repo: ProcurementRepository) -> None:
        await repo.connect()
        scorecard = {
            "vendor_id": "V001",
            "vendor_name": "Test Corp",
            "period": "2026-Q2",
            "overall_score": 85.0,
            "trend": "improving",
            "risk_flags": [],
            "metrics": [],
        }
        saved = await repo.save_vendor_scorecard(scorecard)
        assert saved

        results = await repo.get_vendor_scorecards("V001")
        assert len(results) == 1
        assert results[0]["overall_score"] == 85.0

    @pytest.mark.asyncio
    async def test_save_po_recommendation(self, repo: ProcurementRepository) -> None:
        await repo.connect()
        po = {
            "po_id": "PO-ABC123",
            "vendor_id": "V001",
            "vendor_name": "Test Corp",
            "material_id": "MAT-STEEL-001",
            "material_name": "Steel",
            "quantity": 1000.0,
            "unit": "kg",
            "unit_price": 850.0,
            "total_value": 850_000.0,
            "status": "draft",
            "hitl_required": True,
            "reasoning": "Test",
            "confidence": 0.85,
        }
        saved = await repo.save_po_recommendation(po)
        assert saved

        results = await repo.get_po_recommendations()
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_audit_log(self, repo: ProcurementRepository) -> None:
        await repo.connect()
        written = await repo.write_audit_log(
            action="vendor_scored",
            entity_type="vendor",
            entity_id="V001",
            snapshot={"score": 85.0},
        )
        assert written

        logs = await repo.get_audit_log()
        assert len(logs) >= 1
        assert logs[-1]["action"] == "vendor_scored"
