"""Storage repository — PostgreSQL persistence with in-memory fallback.

Stores production schedules, OEE reports, quality alerts, maintenance triggers,
and audit trail data. Falls back to in-memory dict when PostgreSQL is unavailable.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from config.settings import settings

logger = logging.getLogger(__name__)


class ProductionRepository:
    """Production data persistence layer.

    Writes to PostgreSQL when available; falls back to in-memory dict
    for read operations during outages.
    """

    def __init__(self) -> None:
        self._pool: Any = None
        self._connected = False
        self._in_memory_store: dict[str, list[dict[str, Any]]] = {
            "oee_reports": [],
            "quality_alerts": [],
            "production_schedules": [],
            "maintenance_triggers": [],
            "bottleneck_analyses": [],
            "yield_recommendations": [],
            "machine_states": [],
            "audit_log": [],
        }

    async def connect(self) -> None:
        """Connect to PostgreSQL."""
        try:
            import asyncpg  # type: ignore[import-untyped]

            dsn = settings.database.postgres_dsn
            # Parse asyncpg DSN from SQLAlchemy-style URL
            pg_dsn = dsn.replace("postgresql+asyncpg://", "postgresql://")
            self._pool = await asyncpg.create_pool(
                dsn=pg_dsn,
                min_size=settings.database.pool_min_size,
                max_size=settings.database.pool_max_size,
            )
            self._connected = True
            await self._init_schema()
            logger.info("Connected to PostgreSQL")
        except ImportError:
            logger.warning("asyncpg not installed — using in-memory storage")
        except Exception:
            logger.exception("Failed to connect to PostgreSQL — using in-memory storage")

    async def _init_schema(self) -> None:
        """Create tables if they don't exist."""
        if not self._pool or not self._connected:
            return

        async with self._pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS oee_reports (
                    id SERIAL PRIMARY KEY,
                    report_id TEXT UNIQUE,
                    production_line TEXT NOT NULL,
                    shift_id TEXT,
                    period_start TIMESTAMP,
                    period_end TIMESTAMP,
                    availability_pct DOUBLE PRECISION,
                    performance_pct DOUBLE PRECISION,
                    quality_pct DOUBLE PRECISION,
                    oee_pct DOUBLE PRECISION,
                    total_units_produced INTEGER,
                    total_good_units INTEGER,
                    total_defective_units INTEGER,
                    data JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS quality_alerts (
                    id SERIAL PRIMARY KEY,
                    alert_id TEXT UNIQUE,
                    machine_id TEXT NOT NULL,
                    production_line TEXT,
                    severity TEXT,
                    defect_type TEXT,
                    defect_rate_pct DOUBLE PRECISION,
                    data JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS production_schedules (
                    id SERIAL PRIMARY KEY,
                    schedule_id TEXT UNIQUE,
                    production_line TEXT NOT NULL,
                    variance_hours DOUBLE PRECISION,
                    hitl_required BOOLEAN,
                    data JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS maintenance_triggers (
                    id SERIAL PRIMARY KEY,
                    trigger_id TEXT UNIQUE,
                    machine_id TEXT NOT NULL,
                    failure_probability DOUBLE PRECISION,
                    priority TEXT,
                    data JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS audit_log (
                    id SERIAL PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    agent_id TEXT,
                    data JSONB,
                    created_at TIMESTAMP DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_oee_line ON oee_reports(production_line);
                CREATE INDEX IF NOT EXISTS idx_qa_machine ON quality_alerts(machine_id);
                CREATE INDEX IF NOT EXISTS idx_sched_line ON production_schedules(production_line);
                CREATE INDEX IF NOT EXISTS idx_mt_machine ON maintenance_triggers(machine_id);
            """)
            logger.info("Database schema initialized")

    async def disconnect(self) -> None:
        """Close PostgreSQL connection."""
        if self._pool:
            await self._pool.close()
            self._connected = False
            logger.info("Disconnected from PostgreSQL")

    async def save_oee_report(self, data: dict[str, Any]) -> None:
        """Persist an OEE report."""
        self._in_memory_store["oee_reports"].append(data)
        if self._connected and self._pool:
            try:
                async with self._pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO oee_reports (report_id, production_line, shift_id, period_start, period_end,
                            availability_pct, performance_pct, quality_pct, oee_pct, total_units_produced,
                            total_good_units, total_defective_units, data)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                        ON CONFLICT (report_id) DO NOTHING
                        """,
                        data.get("report_id"),
                        data.get("production_line"),
                        data.get("shift_id"),
                        data.get("period_start"),
                        data.get("period_end"),
                        data.get("availability_pct"),
                        data.get("performance_pct"),
                        data.get("quality_pct"),
                        data.get("oee_pct"),
                        data.get("total_units_produced"),
                        data.get("total_good_units"),
                        data.get("total_defective_units"),
                        json.dumps(data),
                    )
            except Exception:
                logger.exception("Failed to persist OEE report to PostgreSQL")

    async def save_quality_alert(self, data: dict[str, Any]) -> None:
        """Persist a quality alert."""
        self._in_memory_store["quality_alerts"].append(data)
        if self._connected and self._pool:
            try:
                async with self._pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO quality_alerts (alert_id, machine_id, production_line, severity, defect_type,
                            defect_rate_pct, data)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                        ON CONFLICT (alert_id) DO NOTHING
                        """,
                        data.get("alert_id"),
                        data.get("machine_id"),
                        data.get("production_line"),
                        data.get("severity"),
                        data.get("defect_type"),
                        data.get("defect_rate_pct"),
                        json.dumps(data),
                    )
            except Exception:
                logger.exception("Failed to persist quality alert to PostgreSQL")

    async def save_production_schedule(self, data: dict[str, Any]) -> None:
        """Persist a production schedule."""
        self._in_memory_store["production_schedules"].append(data)
        if self._connected and self._pool:
            try:
                async with self._pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO production_schedules (schedule_id, production_line, variance_hours, hitl_required, data)
                        VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT (schedule_id) DO NOTHING
                        """,
                        data.get("schedule_id"),
                        data.get("production_line"),
                        data.get("variance_hours"),
                        data.get("hitl_required", False),
                        json.dumps(data),
                    )
            except Exception:
                logger.exception("Failed to persist production schedule to PostgreSQL")

    async def save_maintenance_trigger(self, data: dict[str, Any]) -> None:
        """Persist a maintenance trigger."""
        self._in_memory_store["maintenance_triggers"].append(data)
        if self._connected and self._pool:
            try:
                async with self._pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO maintenance_triggers (trigger_id, machine_id, failure_probability, priority, data)
                        VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT (trigger_id) DO NOTHING
                        """,
                        data.get("trigger_id"),
                        data.get("machine_id"),
                        data.get("probability", data.get("failure_probability")),
                        data.get("priority"),
                        json.dumps(data),
                    )
            except Exception:
                logger.exception("Failed to persist maintenance trigger to PostgreSQL")

    async def log_audit_event(self, event_type: str, agent_id: str, data: dict[str, Any]) -> None:
        """Log an immutable audit event."""
        record = {
            "event_type": event_type,
            "agent_id": agent_id,
            "data": data,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._in_memory_store["audit_log"].append(record)
        if self._connected and self._pool:
            try:
                async with self._pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO audit_log (event_type, agent_id, data)
                        VALUES ($1, $2, $3)
                        """,
                        event_type,
                        agent_id,
                        json.dumps(data),
                    )
            except Exception:
                logger.exception("Failed to persist audit event to PostgreSQL")

    async def get_oee_reports(
        self,
        production_line: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Get OEE reports, optionally filtered by production line."""
        reports = self._in_memory_store["oee_reports"]
        if production_line:
            reports = [r for r in reports if r.get("production_line") == production_line]
        return reports[-limit:]

    async def get_recent_alerts(
        self,
        production_line: str | None = None,
        severity: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Get recent quality alerts."""
        alerts = self._in_memory_store["quality_alerts"]
        if production_line:
            alerts = [a for a in alerts if a.get("production_line") == production_line]
        if severity:
            alerts = [a for a in alerts if a.get("severity") == severity]
        return alerts[-limit:]

    async def get_active_schedule(self, production_line: str) -> dict[str, Any] | None:
        """Get the most recent schedule for a production line."""
        schedules = [
            s for s in self._in_memory_store["production_schedules"]
            if s.get("production_line") == production_line
        ]
        return schedules[-1] if schedules else None
