"""PostgreSQL repository layer — persistent storage for procurement agent state.

Stores:
  - Vendor master data and scorecards (with trend history)
  - Purchase order recommendations and approvals
  - Material prices with timestamps
  - Agent state checkpoints
  - Immutable audit logs

Uses asyncpg for async PostgreSQL access.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from config.settings import settings

logger = logging.getLogger(__name__)

try:
    import asyncpg
except ImportError:
    asyncpg = None  # type: ignore[assignment]
    logger.warning("asyncpg not installed — repository will use in-memory fallback")


class ProcurementRepository:
    """PostgreSQL repository for procurement agent data.

    Provides async CRUD operations with connection pooling.
    Falls back to in-memory storage if PostgreSQL is unavailable.
    """

    def __init__(self) -> None:
        self._pool: Any = None
        self._in_memory_store: dict[str, list[dict[str, Any]]] = {
            "vendor_scorecards": [],
            "po_recommendations": [],
            "price_history": [],
            "sourcing_options": [],
            "audit_log": [],
        }
        self._using_fallback = False

    async def connect(self) -> None:
        """Initialize connection pool to PostgreSQL."""
        if asyncpg is None:
            self._using_fallback = True
            logger.warning("asyncpg unavailable — using in-memory fallback")
            return

        try:
            self._pool = await asyncpg.create_pool(
                dsn=settings.database.postgres_dsn,
                min_size=settings.database.pool_min_size,
                max_size=settings.database.pool_max_size,
                command_timeout=5,
            )
            await self._init_schema()
            logger.info("PostgreSQL connection pool established")
        except Exception:
            logger.warning("PostgreSQL connection failed — using in-memory fallback")
            self._using_fallback = True

    async def disconnect(self) -> None:
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            logger.info("PostgreSQL connection pool closed")

    async def _init_schema(self) -> None:
        """Initialize database schema if not exists."""
        if not self._pool or self._using_fallback:
            return

        async with self._pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS vendor_scorecards (
                    id SERIAL PRIMARY KEY,
                    vendor_id VARCHAR(50) NOT NULL,
                    vendor_name VARCHAR(200) NOT NULL,
                    period VARCHAR(10) NOT NULL,
                    overall_score FLOAT NOT NULL,
                    trend VARCHAR(20),
                    risk_flags JSONB DEFAULT '[]',
                    metrics JSONB DEFAULT '[]',
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(vendor_id, period)
                );

                CREATE TABLE IF NOT EXISTS po_recommendations (
                    id SERIAL PRIMARY KEY,
                    po_id VARCHAR(50) UNIQUE NOT NULL,
                    vendor_id VARCHAR(50),
                    vendor_name VARCHAR(200),
                    material_id VARCHAR(50) NOT NULL,
                    material_name VARCHAR(200),
                    quantity FLOAT NOT NULL,
                    unit VARCHAR(20),
                    unit_price FLOAT,
                    total_value FLOAT,
                    status VARCHAR(30) DEFAULT 'draft',
                    hitl_required BOOLEAN DEFAULT FALSE,
                    hitl_ticket_id VARCHAR(100),
                    hitl_status VARCHAR(30),
                    reasoning TEXT,
                    confidence FLOAT,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    updated_at TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS price_history (
                    id SERIAL PRIMARY KEY,
                    material_id VARCHAR(50) NOT NULL,
                    material_name VARCHAR(200),
                    price FLOAT NOT NULL,
                    unit VARCHAR(20),
                    source VARCHAR(100),
                    recorded_at TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS audit_log (
                    id SERIAL PRIMARY KEY,
                    agent_id VARCHAR(50) NOT NULL,
                    action VARCHAR(100) NOT NULL,
                    entity_type VARCHAR(50),
                    entity_id VARCHAR(100),
                    snapshot JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_vendor_scorecards_vendor
                    ON vendor_scorecards(vendor_id, period);
                CREATE INDEX IF NOT EXISTS idx_po_recommendations_material
                    ON po_recommendations(material_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_price_history_material
                    ON price_history(material_id, recorded_at);
                CREATE INDEX IF NOT EXISTS idx_audit_log_agent
                    ON audit_log(agent_id, created_at);
            """)

    # ── Vendor Scorecards ──

    async def save_vendor_scorecard(self, scorecard: dict[str, Any]) -> bool:
        """Persist a vendor scorecard."""
        self._in_memory_store["vendor_scorecards"].append(scorecard)

        if not self._pool or self._using_fallback:
            return True

        try:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO vendor_scorecards (vendor_id, vendor_name, period, overall_score, trend, risk_flags, metrics)
                    VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7::jsonb)
                    ON CONFLICT (vendor_id, period)
                    DO UPDATE SET overall_score = $4, trend = $5, risk_flags = $6::jsonb, metrics = $7::jsonb
                    """,
                    scorecard.get("vendor_id"),
                    scorecard.get("vendor_name"),
                    scorecard.get("period"),
                    scorecard.get("overall_score", 0.0),
                    scorecard.get("trend", "stable"),
                    json.dumps(scorecard.get("risk_flags", [])),
                    json.dumps(scorecard.get("metrics", [])),
                )
            return True
        except Exception:
            logger.exception("Failed to save vendor scorecard to PostgreSQL")
            return False

    async def get_vendor_scorecards(
        self, vendor_id: str, limit: int = 12
    ) -> list[dict[str, Any]]:
        """Get scorecard history for a vendor."""
        if not self._pool or self._using_fallback:
            return [
                s for s in self._in_memory_store["vendor_scorecards"]
                if s.get("vendor_id") == vendor_id
            ][-limit:]

        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM vendor_scorecards
                    WHERE vendor_id = $1
                    ORDER BY period DESC
                    LIMIT $2
                    """,
                    vendor_id,
                    limit,
                )
                return [dict(row) for row in rows]
        except Exception:
            logger.exception("Failed to query vendor scorecards")
            return []

    # ── Purchase Orders ──

    async def save_po_recommendation(self, po: dict[str, Any]) -> bool:
        """Persist a PO recommendation."""
        self._in_memory_store["po_recommendations"].append(po)

        if not self._pool or self._using_fallback:
            return True

        try:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO po_recommendations
                        (po_id, vendor_id, vendor_name, material_id, material_name,
                         quantity, unit, unit_price, total_value, status,
                         hitl_required, reasoning, confidence)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                    ON CONFLICT (po_id)
                    DO UPDATE SET status = $10, reasoning = $12, updated_at = NOW()
                    """,
                    po.get("po_id"),
                    po.get("vendor_id"),
                    po.get("vendor_name"),
                    po.get("material_id"),
                    po.get("material_name"),
                    po.get("quantity", 0),
                    po.get("unit"),
                    po.get("unit_price", 0),
                    po.get("total_value", 0),
                    po.get("status", "draft"),
                    po.get("hitl_required", False),
                    po.get("reasoning"),
                    po.get("confidence", 0.85),
                )
            return True
        except Exception:
            logger.exception("Failed to save PO recommendation to PostgreSQL")
            return False

    async def get_po_recommendations(
        self, material_id: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Get PO recommendations, optionally filtered by material."""
        if not self._pool or self._using_fallback:
            results = self._in_memory_store["po_recommendations"]
            if material_id:
                results = [r for r in results if r.get("material_id") == material_id]
            return results[-limit:]

        try:
            async with self._pool.acquire() as conn:
                if material_id:
                    rows = await conn.fetch(
                        """
                        SELECT * FROM po_recommendations
                        WHERE material_id = $1
                        ORDER BY created_at DESC
                        LIMIT $2
                        """,
                        material_id,
                        limit,
                    )
                else:
                    rows = await conn.fetch(
                        """
                        SELECT * FROM po_recommendations
                        ORDER BY created_at DESC
                        LIMIT $1
                        """,
                        limit,
                    )
                return [dict(row) for row in rows]
        except Exception:
            logger.exception("Failed to query PO recommendations")
            return []

    # ── Sourcing Options ──

    async def get_sourcing_options(
        self, material_id: str
    ) -> dict[str, Any] | None:
        """Get cached sourcing options for a material."""
        for opts in reversed(self._in_memory_store["sourcing_options"]):
            if opts.get("material_id") == material_id:
                return opts
        return None

    async def save_sourcing_options(self, options: dict[str, Any]) -> None:
        """Cache sourcing options in memory (primary cache is Redis)."""
        # Remove old entry
        self._in_memory_store["sourcing_options"] = [
            o for o in self._in_memory_store["sourcing_options"]
            if o.get("material_id") != options.get("material_id")
        ]
        self._in_memory_store["sourcing_options"].append(options)

    # ── Audit Log ──

    async def write_audit_log(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        snapshot: dict[str, Any] | None = None,
    ) -> bool:
        """Write an immutable audit log entry."""
        entry = {
            "agent_id": settings.agent_id,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "snapshot": snapshot,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._in_memory_store["audit_log"].append(entry)

        if not self._pool or self._using_fallback:
            return True

        try:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO audit_log (agent_id, action, entity_type, entity_id, snapshot)
                    VALUES ($1, $2, $3, $4, $5::jsonb)
                    """,
                    settings.agent_id,
                    action,
                    entity_type,
                    entity_id,
                    json.dumps(snapshot) if snapshot else None,
                )
            return True
        except Exception:
            logger.exception("Failed to write audit log to PostgreSQL")
            return False

    async def get_audit_log(
        self, limit: int = 100, entity_type: str | None = None
    ) -> list[dict[str, Any]]:
        """Get audit log entries."""
        if not self._pool or self._using_fallback:
            results = self._in_memory_store["audit_log"]
            if entity_type:
                results = [r for r in results if r.get("entity_type") == entity_type]
            return results[-limit:]

        try:
            async with self._pool.acquire() as conn:
                if entity_type:
                    rows = await conn.fetch(
                        """
                        SELECT * FROM audit_log
                        WHERE entity_type = $1
                        ORDER BY created_at DESC
                        LIMIT $2
                        """,
                        entity_type,
                        limit,
                    )
                else:
                    rows = await conn.fetch(
                        """
                        SELECT * FROM audit_log
                        ORDER BY created_at DESC
                        LIMIT $1
                        """,
                        limit,
                    )
                return [dict(row) for row in rows]
        except Exception:
            logger.exception("Failed to query audit log")
            return []
