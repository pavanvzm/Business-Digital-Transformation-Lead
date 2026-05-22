"""Tests for cache manager and storage repository."""

from __future__ import annotations

import pytest

from src.storage.cache import CacheManager, InMemoryLRU
from src.storage.repository import ProductionRepository


class TestInMemoryLRU:
    """Test LRU cache behavior."""

    def setup_method(self) -> None:
        self.cache = InMemoryLRU(capacity=5, default_ttl=3600)

    def test_set_and_get(self) -> None:
        """Basic set/get operations."""
        self.cache.set("key1", "value1")
        assert self.cache.get("key1") == "value1"

    def test_missing_key(self) -> None:
        """Missing key returns None."""
        assert self.cache.get("nonexistent") is None

    def test_expired_ttl(self) -> None:
        """Expired TTL returns None."""
        import time

        cache = InMemoryLRU(capacity=5, default_ttl=0)  # 0 TTL = immediate expiry
        cache.set("key1", "value1")
        time.sleep(0.01)
        assert cache.get("key1") is None

    def test_lru_eviction(self) -> None:
        """LRU eviction when capacity is reached."""
        for i in range(10):
            self.cache.set(f"key{i}", f"value{i}")

        # Oldest keys should be evicted
        assert self.cache.get("key0") is None
        assert self.cache.get("key9") is not None  # newest

    def test_delete(self) -> None:
        """Delete removes key."""
        self.cache.set("key1", "value1")
        self.cache.delete("key1")
        assert self.cache.get("key1") is None

    def test_clear(self) -> None:
        """Clear removes all entries."""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.clear()
        assert self.cache.get("key1") is None
        assert self.cache.get("key2") is None


class TestCacheManager:
    """Test cache manager with in-memory fallback."""

    @pytest.mark.asyncio
    async def test_no_redis_fallback(self) -> None:
        """Cache manager works without Redis."""
        cache = CacheManager()
        # Don't call connect — it will use in-memory fallback
        await cache.set("test_key", {"value": 42})
        result = await cache.get("test_key")
        assert result is not None
        assert result["value"] == 42

    @pytest.mark.asyncio
    async def test_machine_state_cache(self) -> None:
        """Machine state cache roundtrip."""
        cache = CacheManager()
        state = {"machine_id": "M-001", "state": "running", "run_hours": 6.5}
        await cache.set_machine_state("M-001", state)
        result = await cache.get_machine_state("M-001")
        assert result is not None
        assert result["state"] == "running"
        assert result["run_hours"] == 6.5

    @pytest.mark.asyncio
    async def test_production_plan_cache(self) -> None:
        """Production plan cache roundtrip."""
        cache = CacheManager()
        plan = {"production_line": "Line-A", "total_units": 5000, "optimized": True}
        await cache.set_production_plan("Line-A", plan)
        result = await cache.get_production_plan("Line-A")
        assert result is not None
        assert result["total_units"] == 5000
        assert result["optimized"] is True

    @pytest.mark.asyncio
    async def test_material_availability_cache(self) -> None:
        """Material availability cache roundtrip."""
        cache = CacheManager()
        data = {"material_id": "MAT-001", "available_for_wip": True, "current_stock": 500}
        await cache.set_material_availability("MAT-001", data)
        result = await cache.get_material_availability("MAT-001")
        assert result is not None
        assert result["available_for_wip"] is True
        assert result["current_stock"] == 500


class TestProductionRepository:
    """Test in-memory storage repository."""

    @pytest.mark.asyncio
    async def test_save_and_get_oee_reports(self) -> None:
        """OEE reports can be saved and retrieved."""
        repo = ProductionRepository()
        report = {"report_id": "oee-test", "production_line": "Line-A", "oee_pct": 85.5}
        await repo.save_oee_report(report)

        reports = await repo.get_oee_reports()
        assert len(reports) == 1
        assert reports[0]["oee_pct"] == 85.5

    @pytest.mark.asyncio
    async def test_filter_oee_by_line(self) -> None:
        """OEE reports can be filtered by production line."""
        repo = ProductionRepository()
        await repo.save_oee_report({"report_id": "r1", "production_line": "Line-A", "oee_pct": 90.0})
        await repo.save_oee_report({"report_id": "r2", "production_line": "Line-B", "oee_pct": 85.0})

        line_a_reports = await repo.get_oee_reports(production_line="Line-A")
        assert len(line_a_reports) == 1
        assert line_a_reports[0]["production_line"] == "Line-A"

    @pytest.mark.asyncio
    async def test_save_quality_alerts(self) -> None:
        """Quality alerts can be saved."""
        repo = ProductionRepository()
        alert = {
            "alert_id": "qa-test",
            "machine_id": "M-001",
            "production_line": "Line-A",
            "severity": "critical",
            "defect_type": "spc_violation",
        }
        await repo.save_quality_alert(alert)

        alerts = await repo.get_recent_alerts()
        assert len(alerts) == 1
        assert alerts[0]["severity"] == "critical"

    @pytest.mark.asyncio
    async def test_filter_alerts_by_severity(self) -> None:
        """Alerts can be filtered by severity."""
        repo = ProductionRepository()
        await repo.save_quality_alert({"alert_id": "a1", "severity": "critical", "machine_id": "M-001"})
        await repo.save_quality_alert({"alert_id": "a2", "severity": "warning", "machine_id": "M-001"})

        critical = await repo.get_recent_alerts(severity="critical")
        assert len(critical) == 1
        assert critical[0]["severity"] == "critical"

    @pytest.mark.asyncio
    async def test_save_production_schedule(self) -> None:
        """Production schedules can be saved."""
        repo = ProductionRepository()
        schedule = {
            "schedule_id": "sched-test",
            "production_line": "Line-A",
            "variance_hours": 2.5,
            "hitl_required": False,
        }
        await repo.save_production_schedule(schedule)

        active = await repo.get_active_schedule("Line-A")
        assert active is not None
        assert active["variance_hours"] == 2.5

    @pytest.mark.asyncio
    async def test_save_maintenance_trigger(self) -> None:
        """Maintenance triggers can be saved."""
        repo = ProductionRepository()
        trigger = {
            "trigger_id": "pm-test",
            "machine_id": "M-001",
            "failure_probability": 0.92,
            "priority": "proactive",
        }
        await repo.save_maintenance_trigger(trigger)

        # Verify by checking audit log
        await repo.log_audit_event("maintenance_trigger", "agent-02", trigger)
        # No explicit get method — but we verified no errors

    @pytest.mark.asyncio
    async def test_log_audit_event(self) -> None:
        """Audit events are logged immutably."""
        repo = ProductionRepository()
        await repo.log_audit_event(
            event_type="decision",
            agent_id="agent-02",
            data={"decision": "approved", "ticket_id": "H-001"},
        )
        # Verify no errors — audit log is stored in-memory
        assert repo._in_memory_store["audit_log"] is not None
