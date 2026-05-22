"""Agent-02 messaging layer — Kafka consumer, producer, and CloudEvent schemas."""

from __future__ import annotations

from .consumer import EventConsumer
from .producer import EventProducer
from .schemas import (
    BottleneckAnalysisPayload,
    ForecastDemandPayload,
    InventorySnapshotPayload,
    MachineState,
    MachineStatePayload,
    MaintenancePriority,
    MaintenanceTriggerPayload,
    OEEComponent,
    OEEReportPayload,
    OrchestratorCommand,
    ProductionEventType,
    ProductionSchedulePayload,
    QualityAlertPayload,
    QualityAlertSeverity,
    YieldOptimizationPayload,
)

__all__ = [
    "EventConsumer",
    "EventProducer",
    "BottleneckAnalysisPayload",
    "ForecastDemandPayload",
    "InventorySnapshotPayload",
    "MachineState",
    "MachineStatePayload",
    "MaintenancePriority",
    "MaintenanceTriggerPayload",
    "OEEComponent",
    "OEEReportPayload",
    "OrchestratorCommand",
    "ProductionEventType",
    "ProductionSchedulePayload",
    "QualityAlertPayload",
    "QualityAlertSeverity",
    "YieldOptimizationPayload",
]
