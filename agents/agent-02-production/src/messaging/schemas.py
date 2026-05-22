"""CloudEvent schemas and payload models for Agent-02 Production & MES."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class ProductionEventType(str, Enum):
    """CloudEvent type strings for production domain events."""

    MES_MACHINE_STATE = "com.manufacturing.mes.machine-state"
    MES_CYCLE_COMPLETE = "com.manufacturing.mes.cycle-complete"
    PRODUCTION_SCHEDULE = "com.manufacturing.production.schedule"
    OEE_REPORT = "com.manufacturing.production.oee-report"
    QUALITY_ALERT = "com.manufacturing.production.quality-alert"
    MAINTENANCE_TRIGGER = "com.manufacturing.production.maintenance-trigger"
    BOTTLENECK_ANALYSIS = "com.manufacturing.production.bottleneck-analysis"
    YIELD_RECOMMENDATION = "com.manufacturing.production.yield-recommendation"
    DOWNTIME_EVENT = "com.manufacturing.production.downtime.v1"
    PRODUCTION_COMPLETED = "com.manufacturing.production.completed.v1"
    HITL_DECISION = "com.manufacturing.production.hitl-decision"
    ORCHESTRATOR_COMMAND = "com.manufacturing.orchestrator.command"
    INVENTORY_SNAPSHOT = "com.manufacturing.inventory.stock-snapshot"
    FORECAST_EVENT = "com.manufacturing.forecast.demand-projection"


class MachineState(str, Enum):
    """Operational state of a production machine/line."""

    RUNNING = "running"
    IDLE = "idle"
    SCHEDULED_DOWNTIME = "scheduled_downtime"
    UNSCHEDULED_DOWNTIME = "unscheduled_downtime"
    CHANGEOVER = "changeover"
    QUALITY_HOLD = "quality_hold"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"


class QualityAlertSeverity(str, Enum):
    """Severity levels for quality alerts."""

    INFO = "info"
    WARNING = "warning"
    ALERT = "alert"
    CRITICAL = "critical"


class MaintenancePriority(str, Enum):
    """Priority levels for maintenance triggers."""

    ROUTINE = "routine"
    PROACTIVE = "proactive"
    URGENT = "urgent"
    IMMEDIATE_HALT = "immediate_halt"


class MachineStatePayload(BaseModel):
    """Payload for MES machine state updates."""

    machine_id: str
    machine_name: str
    production_line: str
    state: MachineState
    previous_state: MachineState | None = None
    cycle_count: int = 0
    ideal_cycle_time_seconds: float = 0.0  # ideal cycle time per unit
    actual_cycle_time_seconds: float = 0.0  # actual cycle time
    run_hours: float = 0.0
    temperature_celsius: float | None = None
    vibration_mm_s: float | None = None
    current_draw_amps: float | None = None
    shift_id: str = ""
    operator_id: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OEEComponent(BaseModel):
    """Single OEE component (Availability, Performance, or Quality)."""

    name: str  # "availability", "performance", "quality"
    value_pct: float  # 0-100
    sub_metrics: dict[str, float] = Field(default_factory=dict)


class OEEReportPayload(BaseModel):
    """Payload for OEE report events."""

    report_id: str = Field(default_factory=lambda: f"oee-{uuid4().hex[:8]}")
    production_line: str
    shift_id: str
    period_start: datetime
    period_end: datetime
    availability_pct: float
    performance_pct: float
    quality_pct: float
    oee_pct: float  # availability × performance × quality
    components: list[OEEComponent] = Field(default_factory=list)
    total_units_produced: int = 0
    total_good_units: int = 0
    total_defective_units: int = 0
    total_downtime_minutes: float = 0.0
    planned_downtime_minutes: float = 0.0
    trend: str = "stable"  # "improving", "stable", "declining"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class QualityAlertPayload(BaseModel):
    """Payload for quality defect alerts."""

    alert_id: str = Field(default_factory=lambda: f"qa-{uuid4().hex[:8]}")
    machine_id: str
    production_line: str
    severity: QualityAlertSeverity
    defect_type: str  # e.g., "dimension_out_of_tolerance", "surface_defect"
    defect_rate_pct: float
    rule_violated: str = ""  # e.g., "Rule 1 — 1 point beyond ±3σ"
    units_affected: int = 0
    batch_id: str = ""
    material_id: str = ""
    parameter_name: str = ""  # e.g., "thickness", "temperature"
    parameter_value: float = 0.0
    upper_control_limit: float = 0.0
    lower_control_limit: float = 0.0
    recommendation: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MaintenanceTriggerPayload(BaseModel):
    """Payload for predictive maintenance alerts."""

    trigger_id: str = Field(default_factory=lambda: f"pm-{uuid4().hex[:8]}")
    machine_id: str
    machine_name: str
    priority: MaintenancePriority
    failure_probability: float  # 0.0-1.0
    predicted_failure_hours: float | None = None
    recommended_action: str = ""
    features: dict[str, float] = Field(default_factory=dict)  # vibration, temp, etc.
    confidence: float = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProductionSchedulePayload(BaseModel):
    """Payload for production schedule events."""

    schedule_id: str = Field(default_factory=lambda: f"sched-{uuid4().hex[:8]}")
    production_line: str
    sequence: list[dict[str, Any]] = Field(default_factory=list)
    original_sequence_hash: str = ""  # for tracking variance
    variance_hours: float = 0.0
    variance_reason: str = ""
    total_orders: int = 0
    total_units: int = 0
    optimization_score: float = 0.0  # 0-100
    hitl_required: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BottleneckAnalysisPayload(BaseModel):
    """Payload for bottleneck identification."""

    analysis_id: str = Field(default_factory=lambda: f"bn-{uuid4().hex[:8]}")
    production_line: str
    bottleneck_machine_id: str = ""
    constraint_type: str = ""  # "capacity", "quality", "material", "maintenance"
    cycle_time_delta_pct: float = 0.0
    queue_length: int = 0
    utilization_pct: float = 0.0
    estimated_throughput_loss_pct: float = 0.0
    recommendations: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class YieldOptimizationPayload(BaseModel):
    """Payload for yield improvement recommendations."""

    recommendation_id: str = Field(default_factory=lambda: f"yield-{uuid4().hex[:8]}")
    production_line: str
    material_id: str = ""
    current_yield_pct: float = 0.0
    target_yield_pct: float = 0.0
    parameter_adjustments: dict[str, float] = Field(default_factory=dict)
    expected_improvement_pct: float = 0.0
    confidence: float = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OrchestratorCommand(BaseModel):
    """Orchestrator commands for agent governance."""

    command_id: str = Field(default_factory=lambda: f"cmd-{uuid4().hex[:8]}")
    command_type: str  # pause, resume, rollback, circuit_breaker_status
    reason: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)
    issued_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class InventorySnapshotPayload(BaseModel):
    """Simplified inventory snapshot consumed from Agent-03."""

    material_id: str
    material_name: str
    current_stock: float
    safety_stock: float
    reorder_point: float
    unit: str = "units"
    available_for_wip: bool = True
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ForecastDemandPayload(BaseModel):
    """Simplified forecast consumed from Agent-06."""

    forecast_id: str = ""
    forecast_month: str = ""
    product_line: str = ""
    total_units: int = 0
    confidence_interval_lower: float = 0.0
    confidence_interval_upper: float = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
