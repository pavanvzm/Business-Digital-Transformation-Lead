"""Redis cache manager — high-performance caching layer for market prices,
vendor scores, forecast demand, and inventory snapshots.

TTL-based expiry with fallback to in-memory LRU if Redis is unavailable.
"""

from __future__ import annotations

import json
import logging
from collections import OrderedDict
from typing import Any

from config.settings import settings

logger = logging.getLogger(__name__)

try:
    import redis.asyncio as redis_async
except ImportError:
    redis_async = None  # type: ignore[assignment]
    logger.warning("redis.asyncio not installed — cache will use in-memory LRU fallback")


class InMemoryLRU:
    """Simple in-memory LRU cache with TTL support (fallback when Redis unavailable)."""

    def __init__(self, maxsize: int = 10_000) -> None:
        self._store: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._maxsize = maxsize

    async def get(self, key: str) -> Any | None:
        if key not in self._store:
            return None
        value, expiry = self._store[key]
        if expiry > 0 and expiry < __import__("time").time():
            del self._store[key]
            return None
        self._store.move_to_end(key)
        return value

    async def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        expiry = __import__("time").time() + ttl_seconds if ttl_seconds > 0 else 0
        self._store[key] = (value, expiry)
        self._store.move_to_end(key)
        while len(self._store) > self._maxsize:
            self._store.popitem(last=False)

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def exists(self, key: str) -> bool:
        return key in self._store

    async def clear(self) -> None:
        self._store.clear()


# Cache key prefixes
_KEY_PRICE = "agent01:price:"
_KEY_FORECAST = "agent01:forecast:"
_KEY_INVENTORY = "agent01:inventory:"
_KEY_VENDOR = "agent01:vendor:"
_KEY_SOURCING = "agent01:sourcing:"
_KEY_SCORECARD = "agent01:scorecard:"


class CacheManager:
    """Distributed cache layer using Redis with in-memory LRU fallback.

    Cache key naming: agent01:<entity>:<id> — namespaced per agent for multi-tenant safety.
    """

    def __init__(self) -> None:
        self._redis: Any = None
        self._memory: InMemoryLRU | None = None
        self._using_redis = False

    async def connect(self) -> None:
        """Connect to Redis server."""
        if redis_async is None:
            self._memory = InMemoryLRU()
            logger.warning("Redis client unavailable — using in-memory cache")
            return

        try:
            self._redis = redis_async.from_url(
                settings.database.redis_url,
                socket_connect_timeout=2,
                socket_timeout=2,
                decode_responses=True,
            )
            await self._redis.ping()
            self._using_redis = True
            logger.info("Connected to Redis cache")
        except Exception:
            logger.warning("Redis connection failed — using in-memory cache")
            self._memory = InMemoryLRU()
            self._using_redis = False

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._redis and self._using_redis:
            await self._redis.close()
            logger.info("Redis cache connection closed")

    async def _get(self, key: str) -> Any | None:
        """Get value from cache (Redis first, fallback to memory)."""
        if self._using_redis and self._redis:
            try:
                value = await self._redis.get(key)
                if value is not None:
                    return json.loads(value)
            except Exception:
                logger.warning("Redis get failed, falling back to memory", key=key)
        if self._memory:
            return await self._memory.get(key)
        return None

    async def _set(self, key: str, value: Any, ttl: int) -> None:
        """Set value in cache (Redis first, fallback to memory)."""
        if self._using_redis and self._redis:
            try:
                await self._redis.setex(key, ttl, json.dumps(value))
                return
            except Exception:
                logger.warning("Redis set failed, falling back to memory", key=key)
        if self._memory:
            await self._memory.set(key, value, ttl)

    # ── Market Prices ──

    async def set_price(self, material_id: str, price: float) -> None:
        """Cache material price with configured TTL."""
        key = f"{_KEY_PRICE}{material_id}"
        await self._set(key, price, settings.cache_ttl_market_prices)

    async def get_price(self, material_id: str) -> float | None:
        """Get cached material price."""
        key = f"{_KEY_PRICE}{material_id}"
        value = await self._get(key)
        if value is not None:
            return float(value)
        return None

    # ── Forecast Demand ──

    async def set_forecast_demand(self, material_id: str, quantity: float, month: str) -> None:
        """Cache forecast demand for a material."""
        key = f"{_KEY_FORECAST}{material_id}"
        await self._set(key, {"quantity": quantity, "month": month}, settings.cache_ttl_forecast)

    async def get_forecast_demand(self, material_id: str) -> float | None:
        """Get cached forecast demand quantity."""
        key = f"{_KEY_FORECAST}{material_id}"
        value = await self._get(key)
        if value is not None:
            return float(value.get("quantity", 0))
        return None

    # ── Inventory Levels ──

    async def set_inventory_level(self, material_id: str, stock: float, safety_stock: float) -> None:
        """Cache current inventory level for a material."""
        key = f"{_KEY_INVENTORY}{material_id}"
        await self._set(key, {"stock": stock, "safety_stock": safety_stock}, ttl=300)

    async def get_inventory_level(self, material_id: str) -> dict[str, float] | None:
        """Get cached inventory level."""
        key = f"{_KEY_INVENTORY}{material_id}"
        value = await self._get(key)
        if value is not None:
            return {"stock": float(value.get("stock", 0)), "safety_stock": float(value.get("safety_stock", 0))}
        return None

    # ── Vendor Master Data ──

    async def set_vendor(self, vendor_id: str, data: dict[str, Any]) -> None:
        """Cache vendor master data."""
        key = f"{_KEY_VENDOR}{vendor_id}"
        await self._set(key, data, settings.cache_ttl_vendor_master)

    async def get_vendor(self, vendor_id: str) -> dict[str, Any] | None:
        """Get cached vendor master data."""
        key = f"{_KEY_VENDOR}{vendor_id}"
        return await self._get(key)

    # ── Sourcing Options ──

    async def set_sourcing_options(self, material_id: str, options: dict[str, Any]) -> None:
        """Cache alternative sourcing options."""
        key = f"{_KEY_SOURCING}{material_id}"
        await self._set(key, options, ttl=14400)  # 4 hours

    async def get_sourcing_options(self, material_id: str) -> dict[str, Any] | None:
        """Get cached sourcing options."""
        key = f"{_KEY_SOURCING}{material_id}"
        return await self._get(key)

    # ── Scorecard Cache ──

    async def set_scorecard(self, vendor_id: str, period: str, scorecard: dict[str, Any]) -> None:
        """Cache a vendor scorecard."""
        key = f"{_KEY_SCORECARD}{vendor_id}:{period}"
        await self._set(key, scorecard, ttl=86400)

    async def get_scorecard(self, vendor_id: str, period: str) -> dict[str, Any] | None:
        """Get cached vendor scorecard."""
        key = f"{_KEY_SCORECARD}{vendor_id}:{period}"
        return await self._get(key)

    # ── Health ──

    async def ping(self) -> bool:
        """Check cache connectivity."""
        if self._using_redis and self._redis:
            try:
                return await self._redis.ping()
            except Exception:
                return False
        return self._memory is not None
