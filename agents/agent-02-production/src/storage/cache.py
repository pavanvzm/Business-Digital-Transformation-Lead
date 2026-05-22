"""Cache manager — Redis caching with in-memory LRU fallback.

Caches MES machine state snapshots, production plans, material availability,
and computed OEE results for fast retrieval.
"""

from __future__ import annotations

import json
import logging
import time
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Any

from config.settings import settings

logger = logging.getLogger(__name__)


class InMemoryLRU:
    """Simple LRU (Least Recently Used) cache as Redis fallback."""

    def __init__(self, capacity: int = 1000, default_ttl: int = 300) -> None:
        self.capacity = capacity
        self.default_ttl = default_ttl
        self._store: OrderedDict[str, tuple[Any, float]] = OrderedDict()

    def get(self, key: str) -> Any | None:
        """Get a value from the cache."""
        if key not in self._store:
            return None
        value, expires_at = self._store[key]
        if time.time() > expires_at:
            del self._store[key]
            return None
        self._store.move_to_end(key)
        return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set a value in the cache with optional TTL (seconds)."""
        ttl = ttl or self.default_ttl
        if len(self._store) >= self.capacity:
            self._store.popitem(last=False)
        self._store[key] = (value, time.time() + ttl)
        self._store.move_to_end(key)

    def delete(self, key: str) -> None:
        """Delete a key from the cache."""
        self._store.pop(key, None)

    def clear(self) -> None:
        """Clear all cached values."""
        self._store.clear()


class CacheManager:
    """Cache manager with Redis primary and in-memory LRU fallback."""

    def __init__(self) -> None:
        self._redis: Any = None
        self._memory = InMemoryLRU(capacity=2000, default_ttl=300)
        self._connected = False

    async def connect(self) -> None:
        """Connect to Redis."""
        try:
            import redis.asyncio as aioredis  # type: ignore[import-untyped]

            self._redis = aioredis.from_url(
                settings.database.redis_url,
                decode_responses=True,
            )
            await self._redis.ping()
            self._connected = True
            logger.info("Connected to Redis")
        except ImportError:
            logger.warning("redis not installed — using in-memory cache")
        except Exception:
            logger.warning("Redis unavailable — using in-memory cache")

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._connected = False
            logger.info("Disconnected from Redis")

    async def _redis_get(self, key: str) -> str | None:
        """Get a value from Redis."""
        if self._redis and self._connected:
            try:
                return await self._redis.get(key)
            except Exception:
                return None
        return None

    async def _redis_set(self, key: str, value: str, ttl: int) -> None:
        """Set a value in Redis with TTL."""
        if self._redis and self._connected:
            try:
                await self._redis.setex(key, ttl, value)
            except Exception:
                pass

    # ──────────────────────────────────────────────
    # MES / Machine State Cache
    # ──────────────────────────────────────────────

    async def get_machine_state(self, machine_id: str) -> dict[str, Any] | None:
        """Get cached machine state."""
        key = f"agent-02:machine:{machine_id}"
        if self._connected:
            raw = await self._redis_get(key)
            if raw:
                return json.loads(raw)
        return self._memory.get(key)

    async def set_machine_state(self, machine_id: str, state: dict[str, Any]) -> None:
        """Cache machine state."""
        key = f"agent-02:machine:{machine_id}"
        ttl = settings.cache_ttl_mes_state
        if self._connected:
            await self._redis_set(key, json.dumps(state), ttl)
        self._memory.set(key, state, ttl)

    # ──────────────────────────────────────────────
    # Production Plan Cache
    # ──────────────────────────────────────────────

    async def get_production_plan(self, production_line: str) -> dict[str, Any] | None:
        """Get cached production plan for a line."""
        key = f"agent-02:plan:{production_line}"
        if self._connected:
            raw = await self._redis_get(key)
            if raw:
                return json.loads(raw)
        return self._memory.get(key)

    async def set_production_plan(self, production_line: str, plan: dict[str, Any]) -> None:
        """Cache production plan."""
        key = f"agent-02:plan:{production_line}"
        ttl = settings.cache_ttl_production_plan
        if self._connected:
            await self._redis_set(key, json.dumps(plan), ttl)
        self._memory.set(key, plan, ttl)

    # ──────────────────────────────────────────────
    # Material Availability Cache
    # ──────────────────────────────────────────────

    async def get_material_availability(self, material_id: str) -> dict[str, Any] | None:
        """Get cached material availability."""
        key = f"agent-02:material:{material_id}"
        if self._connected:
            raw = await self._redis_get(key)
            if raw:
                return json.loads(raw)
        return self._memory.get(key)

    async def set_material_availability(self, material_id: str, data: dict[str, Any]) -> None:
        """Cache material availability."""
        key = f"agent-02:material:{material_id}"
        ttl = settings.cache_ttl_material_availability
        if self._connected:
            await self._redis_set(key, json.dumps(data), ttl)
        self._memory.set(key, data, ttl)

    # ──────────────────────────────────────────────
    # Generic Cache
    # ──────────────────────────────────────────────

    async def get(self, key: str) -> Any | None:
        """Get any cached value by key."""
        if self._connected:
            raw = await self._redis_get(key)
            if raw:
                return json.loads(raw)
        return self._memory.get(key)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Cache any value by key with optional TTL."""
        ttl = ttl or 300
        serialized = json.dumps(value)
        if self._connected:
            await self._redis_set(key, serialized, ttl)
        self._memory.set(key, value, ttl)

    async def clear(self) -> None:
        """Clear all cached values."""
        self._memory.clear()
        if self._redis and self._connected:
            try:
                await self._redis.flushdb()
            except Exception:
                pass
