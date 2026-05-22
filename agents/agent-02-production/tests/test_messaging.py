"""Tests for message schema serialization and deserialization."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.messaging.schemas import (
    BottleneckAnalysisPayload,
    MachineState,
    MachineStatePayload,
    MaintenancePriority,
    MaintenanceTriggerPayload,
    OEEComponent,
    OEEReportPayload,
    ProductionEventType,
    ProductionSchedulePayload,
    QualityAlertPayload,
    QualityAlertSeverity,
    YieldOptimizationPayload,
)


class TestMachineStatePayload:
    """Test machine state payload serialization."""

    def test_default_fields(self) -> None:
        """Payload sets reasonable defaults."""
        payload = MachineStatePayload(
            machine_id="M-001",
            machine_name="CNC Machine 1",
            production_line="Line-A",
            state=MachineState.RUNNING,
        )

        assert payload.machine_id == "M-001"
        assert payload.state == MachineState.RUNNING
        assert payload.cycle_count == 0
        assert payload.timestamp is not None

    def test_full_construction(self) -> None:
        """Payload with all fields populated."""
        now = datetime.now(timezone.utc)
        payload = MachineStatePayload(
            machine_id="M-002",
            machine_name="Press Machine 2",
            production_line="Line-B",
            state=MachineState.UNSCHEDULED_DOWNTIME,
            previous_state=MachineState.RUNNING,
            cycle_count=1500,
            ideal_cycle_time_seconds=45.0,
            actual_cycle_time_seconds=52.0,
            run_hours=6.5,
            temperature_celsius=185.0,
            vibration_mm_s=2.3,
            current_draw_amps=45.0,
            shift_id="S1",
            operator_id="OP-001",
            timestamp=now,
        )

        assert payload.previous_state == MachineState.RUNNING
        assert payload.run_hours == 6.5
        assert payload.operator_id == "OP-001"

    def test_model_dump(self) -> None:
        """Payload can be serialized to dict."""
        payload = MachineStatePayload(
            machine_id="M-001",
            machine_name="Test",
            production_line="Line-A",
            state=MachineState.IDLE,
        )
        d = payload.model_dump(mode="json")
        assert d["machine_id"] == "M-001"
        assert d["state"] == "idle"
        assert "timestamp" in d


class TestOEEReportPayload:
    """Test OEE report payload."""

    def test_default_report_id(self) -> None:
        """Report ID is auto-generated."""
        payload = OEEReportPayload(
            production_line="Line-A",
            shift_id="S1",
            period_start=datetime.now(timezone.utc),
            period_end=datetime.now(timezone.utc),
            availability_pct=95.0,
            performance_pct=92.0,
            quality_pct=98.0,
            oee_pct=85.65,
        )

        assert payload.report_id.startswith("oee-")
        assert payload.production_line == "Line-A"

    def test_with_components(self) -> None:
        """Report with sub-components."""
        components = [
            OEEComponent(name="availability", value_pct=95.0, sub_metrics={"operating_time": 456.0}),
            OEEComponent(name="performance", value_pct=92.0, sub_metrics={"speed_loss": 8.0}),
            OEEComponent(name="quality", value_pct=98.0, sub_metrics={"scrap_rate": 2.0}),
        ]

        payload = OEEReportPayload(
            production_line="Line-A",
            shift_id="S1",
            period_start=datetime.now(timezone.utc),
            period_end=datetime.now(timezone.utc),
            availability_pct=95.0,
            performance_pct=92.0,
            quality_pct=98.0,
            oee_pct=85.65,
            components=components,
        )

        assert len(payload.components) == 3
        assert payload.total_good_units == 0  # default


class TestQualityAlertPayload:
    """Test quality alert payload."""

    def test_alert_with_spc_violation(self) -> None:
        """Alert with SPC rule violation details."""
        payload = QualityAlertPayload(
            machine_id="M-001",
            production_line="Line-A",
            severity=QualityAlertSeverity.CRITICAL,
            defect_type="spc_violation",
            defect_rate_pct=8.5,
            rule_violated="Rule 1 — 1 point beyond ±3σ",
            units_affected=45,
            batch_id="B-2041",
            parameter_name="temperature",
            parameter_value=210.0,
            upper_control_limit=200.0,
            lower_control_limit=180.0,
            recommendation="Immediate investigation required",
        )

        assert payload.severity == QualityAlertSeverity.CRITICAL
        assert payload.units_affected == 45
        assert payload.alert_id.startswith("qa-")
        assert payload.parameter_value == 210.0

    def test_model_dump(self) -> None:
        """Alert serialized to dict."""
        payload = QualityAlertPayload(
            machine_id="M-001",
            production_line="Line-A",
            severity=QualityAlertSeverity.WARNING,
            defect_type="surface_defect",
            defect_rate_pct=3.2,
        )
        d = payload.model_dump(mode="json")
        assert d["machine_id"] == "M-001"
        assert d["severity"] == "warning"
        assert d["defect_type"] == "surface_defect"


class TestMaintenanceTriggerPayload:
    """Test maintenance trigger payload."""

    def test_immediate_halt_trigger(self) -> None:
        """Immediate halt maintenance trigger."""
        payload = MaintenanceTriggerPayload(
            machine_id="M-001",
            machine_name="Critical Press",
            priority=MaintenancePriority.IMMEDIATE_HALT,
            failure_probability=0.97,
            predicted_failure_hours=1.5,
            recommended_action="Immediate halt and manual inspection",
            features={"vibration": 8.5, "temperature": 195.0, "current_draw": 55.0},
            confidence=0.95,
        )

        assert payload.priority == MaintenancePriority.IMMEDIATE_HALT
        assert payload.failure_probability == 0.97
        assert payload.trigger_id.startswith("pm-")
        assert len(payload.features) == 3


class TestOtherPayloads:
    """Test remaining payload types."""

    def test_production_schedule(self) -> None:
        """Production schedule payload."""
        payload = ProductionSchedulePayload(
            production_line="Line-A",
            sequence=[{"order_id": "ORD-001", "start_time": "2026-01-15T08:00:00"}],
            variance_hours=2.5,
            total_orders=1,
            total_units=500,
        )

        assert payload.schedule_id.startswith("sched-")
        assert payload.variance_hours == 2.5
        assert not payload.hitl_required

    def test_bottleneck_analysis(self) -> None:
        """Bottleneck analysis payload."""
        payload = BottleneckAnalysisPayload(
            production_line="Line-A",
            bottleneck_machine_id="M-003",
            constraint_type="capacity",
            cycle_time_delta_pct=25.0,
            queue_length=12,
            utilization_pct=95.0,
            estimated_throughput_loss_pct=18.5,
            recommendations=["Increase throughput on M-003", "Consider parallel operation"],
        )

        assert payload.analysis_id.startswith("bn-")
        assert payload.constraint_type == "capacity"
        assert len(payload.recommendations) == 2

    def test_yield_optimization(self) -> None:
        """Yield optimization payload."""
        payload = YieldOptimizationPayload(
            production_line="Line-A",
            material_id="MAT-001",
            current_yield_pct=92.0,
            target_yield_pct=97.0,
            parameter_adjustments={"temperature": -5.0, "pressure": 2.0},
            expected_improvement_pct=3.5,
            confidence=0.82,
        )

        assert payload.recommendation_id.startswith("yield-")
        assert len(payload.parameter_adjustments) == 2
        assert payload.expected_improvement_pct == 3.5
