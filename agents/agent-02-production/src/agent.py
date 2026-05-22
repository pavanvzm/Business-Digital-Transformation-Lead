"""Core Production & MES Agent — orchestrates OEE calculation, quality alerting, maintenance triggers, and schedule optimization.

This is the main agent class that ties together all sub-modules:
- EventConsumer / EventProducer: Kafka pub/sub with CloudEvents
- OEECalculator: OEE computation and SPC rule checking
- ProductionScheduler: Constraint-based order sequencing
- HITLGate: Human-in-the-Loop integration
- ProductionRepository / CacheManager: PostgreSQL + Redis persistence
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from config.settings import settings
from src.hitl.gate import HITLGate, HITLPriority, HITLTicket
from src.messaging.consumer import EventConsumer
from src.messaging.producer import EventProducer
from src.messaging.schemas import (
    MachineState,
    MachineStatePayload,
    QualityAlertSeverity,
    MaintenancePriority,
    OrchestratorCommand,
    ProductionSchedulePayload,
    OEEReportPayload,
    QualityAlertPayload,
    MaintenanceTriggerPayload,
    BottleneckAnalysisPayload,
    YieldOptimizationPayload,
)
from src.scoring.oee_calculator import OEECalculator, OEEBreakdown, SPCViolation
from src.decisions.scheduler import ProductionScheduler, ProductionOrder
from src.storage.repository import ProductionRepository
from src.storage.cache import CacheManager

logger = logging.getLogger(__name__)


class AgentState:
    """Runtime state tracking for the production agent."""

    def __init__(self) -> None:
        self.started_at: datetime | None = None
        self.total_messages_consumed: int = 0
        self.total_published: int = 0
        self.total_oee_reports: int = 0
        self.total_quality_alerts: int = 0
        self.total_maintenance_triggers: int = 0
        self.total_schedule_optimizations: int = 0
        self.total_errors: int = 0
        self.fallback_mode: bool = False
        self.orchestrator_paused: bool = False
        self.active_hitl_tickets: list[str] = []
        self.last_oee_by_line: dict[str, float] = {}

    @property
    def uptime_seconds(self) -> float:
        if self.started_at is None:
            return 0.0
        return (datetime.now(timezone.utc) - self.started_at).total_seconds()

    def to_dict(self) -> dict[str, Any]:
        return {
            "uptime_seconds": self.uptime_seconds,
            "total_messages_consumed": self.total_messages_consumed,
            "total_published": self.total_published,
            "total_oee_reports": self.total_oee_reports,
            "total_quality_alerts": self.total_quality_alerts,
            "total_maintenance_triggers": self.total_maintenance_triggers,
            "total_schedule_optimizations": self.total_schedule_optimizations,
            "total_errors": self.total_errors,
            "fallback_mode": self.fallback_mode,
            "paused": self.orchestrator_paused,
            "active_hitl_tickets": self.active_hitl_tickets,
            "last_oee_by_line": self.last_oee_by_line,
        }


class ProductionMESAgent:
    """Main production & MES agent that coordinates all sub-modules.

    Architecture:
        Consumer ← Kafka (inventory, forecast, orchestrator, market events)
        Producer → Kafka (production events, dead-letter, quality alerts)
        OEECalculator → OEE computation per line/shift with SPC checking
        Scheduler → ProductionScheduler (order sequencing, constraint-based)
        HITL → HITLGate (human approval workflow)
        Repository → PostgreSQL (persistent state)
        Cache → Redis (performance caching)
    """

    def __init__(self) -> None:
        self.state = AgentState()
        self.settings = settings

        # Messaging layer
        self.producer = EventProducer()
        self.consumer = EventConsumer(producer=self.producer)

        # OEE calculation engine
        self.oee_calculator = OEECalculator(
            availability_target=settings.oee.availability_target_pct,
            performance_target=settings.oee.performance_target_pct,
            quality_target=settings.oee.quality_target_pct,
        )

        # Production scheduler
        self.scheduler = ProductionScheduler(
            schedule_variance_threshold_hours=settings.oee.schedule_variance_hours,
        )

        # HITL gate
        self.hitl = HITLGate(
            poll_interval_seconds=settings.hitl_poll_interval_seconds,
            default_timeout_seconds=settings.hitl_timeout_seconds,
        )

        # Storage layer
        self.repository = ProductionRepository()
        self.cache = CacheManager()

        # Shutdown event
        self._shutdown_event = asyncio.Event()

        # Internal state for machine data aggregation
        self._machine_states: dict[str, dict[str, Any]] = {}
        self._cycle_time_buffer: dict[str, list[float]] = {}
        self._quality_buffer: dict[str, list[float]] = {}

    async def start(self) -> None:
        """Start the production agent: connect sub-systems and begin consuming."""
        logger.info(
            "Starting Production & MES Agent",
            agent_id=settings.agent_id,
            version=settings.agent_version,
            environment=settings.environment,
        )

        self.state.started_at = datetime.now(timezone.utc)

        # Start storage connections
        await self._connect_storage()

        # Start messaging layer
        await self.producer.start()

        # Register event handlers
        self._register_handlers()

        await self.consumer.start()

        # Replay any locally queued messages
        replayed = await self.consumer.replay_local_queue()
        if replayed > 0:
            logger.info("Replayed queued messages from fallback", count=replayed)

        logger.info("Production & MES Agent started successfully")

    async def _connect_storage(self) -> None:
        """Connect to PostgreSQL and Redis."""
        try:
            await self.repository.connect()
            logger.info("Connected to PostgreSQL")
        except Exception:
            logger.warning("PostgreSQL unavailable — operating in degraded mode")
            self.state.fallback_mode = True

        try:
            await self.cache.connect()
            logger.info("Connected to Redis")
        except Exception:
            logger.warning("Redis unavailable — cache disabled")
            self.state.fallback_mode = True

    def _register_handlers(self) -> None:
        """Register CloudEvent handlers for incoming Kafka topics."""
        self.consumer.register_handler(
            "com.manufacturing.mes.machine-state", self._handle_machine_state
        )
        self.consumer.register_handler(
            "com.manufacturing.mes.cycle-complete", self._handle_cycle_complete
        )
        self.consumer.register_handler(
            "com.manufacturing.inventory.stock-snapshot", self._handle_inventory_snapshot
        )
        self.consumer.register_handler(
            "com.manufacturing.forecast.demand-projection", self._handle_demand_forecast
        )
        self.consumer.register_handler(
            "com.manufacturing.orchestrator.command", self._handle_orchestrator_command
        )

    async def run(self) -> None:
        """Main run loop — consumes events until shutdown."""
        try:
            consumer_task = asyncio.create_task(self.consumer.consume_loop())
            periodic_oee_task = asyncio.create_task(self._periodic_oee_calculation())
            health_task = asyncio.create_task(self._health_check_loop())
            hitl_task = asyncio.create_task(self.hitl.poll_pending_decisions(self._on_hitl_response))

            await asyncio.wait(
                [consumer_task, periodic_oee_task, health_task, hitl_task],
                return_when=asyncio.FIRST_COMPLETED,
            )
        except asyncio.CancelledError:
            logger.info("Run loop cancelled")
        finally:
            await self.shutdown()

    async def _periodic_oee_calculation(self) -> None:
        """Periodically compute OEE from aggregated machine data (every shift)."""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(3600)  # every hour
                for machine_id in list(self._machine_states.keys()):
                    await self._compute_and_publish_oee(machine_id)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Error in periodic OEE calculation")

    async def _health_check_loop(self) -> None:
        """Periodic health check and state reporting."""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(60)
                logger.debug("Health check OK", state=self.state.to_dict())
            except Exception:
                logger.exception("Health check error")

    async def shutdown(self) -> None:
        """Graceful shutdown of all sub-systems."""
        logger.info("Shutting down Production & MES Agent")

        await self.consumer.stop()
        await self.producer.stop()
        await self.repository.disconnect()
        await self.cache.disconnect()

        logger.info(
            "Production Agent shutdown complete",
            total_messages=self.state.total_messages_consumed,
            total_oee=self.state.total_oee_reports,
            uptime_seconds=self.state.uptime_seconds,
        )

    # ──────────────────────────────────────────────
    # Event Handlers
    # ──────────────────────────────────────────────

    async def _handle_machine_state(self, data: dict[str, Any]) -> None:
        """Handle MES machine state update events."""
        self.state.total_messages_consumed += 1

        try:
            payload = MachineStatePayload(**data)
        except Exception:
            logger.exception("Failed to deserialize machine state payload")
            return

        # Cache state
        self._machine_states[payload.machine_id] = data
        await self.cache.set_machine_state(payload.machine_id, data)

        # Check for state transitions that need action
        if payload.state == MachineState.UNSCHEDULED_DOWNTIME:
            logger.warning(
                "Unscheduled downtime detected",
                machine_id=payload.machine_id,
                line=payload.production_line,
            )

        if payload.state == MachineState.QUALITY_HOLD:
            await self._handle_quality_hold(payload)

    async def _handle_quality_hold(self, payload: MachineStatePayload) -> None:
        """Handle a quality hold event — check SPC rules and create alert."""
        # Access quality parameter buffer for this machine
        param_values = self._quality_buffer.get(payload.machine_id, [])
        if payload.temperature_celsius:
            param_values.append(payload.temperature_celsius)
            self._quality_buffer[payload.machine_id] = param_values[-50:]  # keep last 50

        # Check SPC rules if we have enough data
        if len(param_values) >= 5:
            violations = self.oee_calculator.check_spc_rules(
                machine_id=payload.machine_id,
                parameter_name="temperature",
                values=param_values,
            )

            for violation in violations:
                severity = QualityAlertSeverity(violation.severity)
                alert = QualityAlertPayload(
                    machine_id=payload.machine_id,
                    production_line=payload.production_line,
                    severity=severity,
                    defect_type="spc_violation",
                    defect_rate_pct=0.0,
                    rule_violated=violation.rule_name,
                    parameter_name=violation.parameter_name,
                    parameter_value=violation.value,
                    upper_control_limit=violation.upper_control_limit,
                    lower_control_limit=violation.lower_control_limit,
                    recommendation=f"Investigate {violation.rule_name} on {payload.machine_id}",
                )

                # Check if this needs HITL escalation
                hitl_required = severity in (QualityAlertSeverity.CRITICAL, QualityAlertSeverity.ALERT)

                # Publish quality alert
                await self.producer.publish_quality_alert(
                    data=alert.model_dump(mode="json"),
                    subject=f"quality/{payload.machine_id}/{alert.alert_id}",
                    hitl_required=hitl_required,
                )
                self.state.total_published += 1
                self.state.total_quality_alerts += 1

                # Persist
                await self.repository.save_quality_alert(alert.model_dump(mode="json"))

                if hitl_required and severity == QualityAlertSeverity.CRITICAL:
                    await self._create_quality_hitl_ticket(alert)

    async def _handle_cycle_complete(self, data: dict[str, Any]) -> None:
        """Handle cycle complete events for performance tracking."""
        self.state.total_messages_consumed += 1

        machine_id = data.get("machine_id", "")
        actual_cycle = data.get("actual_cycle_time_seconds", 0.0)
        ideal_cycle = data.get("ideal_cycle_time_seconds", 0.0)

        # Track cycle times for performance calculation
        if machine_id:
            if machine_id not in self._cycle_time_buffer:
                self._cycle_time_buffer[machine_id] = []
            self._cycle_time_buffer[machine_id].append(actual_cycle or ideal_cycle)

            # Keep buffer manageable
            if len(self._cycle_time_buffer[machine_id]) > 100:
                self._cycle_time_buffer[machine_id] = self._cycle_time_buffer[machine_id][-100:]

    async def _handle_inventory_snapshot(self, data: dict[str, Any]) -> None:
        """Handle inventory snapshot events from Agent-03."""
        self.state.total_messages_consumed += 1

        material_id = data.get("material_id", "")
        material_name = data.get("material_name", "")
        current_stock = data.get("current_stock", 0)
        available = data.get("available_for_wip", True)

        # Cache material availability
        await self.cache.set_material_availability(material_id, {
            "material_id": material_id,
            "material_name": material_name,
            "current_stock": current_stock,
            "available_for_wip": available,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    async def _handle_demand_forecast(self, data: dict[str, Any]) -> None:
        """Handle demand forecast events from Agent-06."""
        self.state.total_messages_consumed += 1

        product_line = data.get("product_line", "")
        total_units = data.get("total_units", 0)

        # Cache forecast for scheduler
        await self.cache.set_production_plan(product_line, {
            "product_line": product_line,
            "total_units": total_units,
            "forecast_month": data.get("forecast_month", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    async def _handle_orchestrator_command(self, data: dict[str, Any]) -> None:
        """Handle governance commands from Agent-09 (Orchestrator)."""
        self.state.total_messages_consumed += 1

        try:
            command = OrchestratorCommand(**data)
        except Exception:
            logger.exception("Failed to deserialize orchestrator command")
            return

        logger.info("Orchestrator command received", command_type=command.command_type)

        if command.command_type == "pause":
            self.state.orchestrator_paused = True
            logger.warning("Agent paused by orchestrator", reason=command.reason)
        elif command.command_type == "resume":
            self.state.orchestrator_paused = False
            logger.info("Agent resumed by orchestrator")
        elif command.command_type == "rollback":
            logger.warning("Rollback requested", parameters=command.parameters)
        elif command.command_type == "circuit_breaker_status":
            cb_open = command.parameters.get("open", False)
            if cb_open:
                self.state.fallback_mode = True
                logger.warning("Circuit breaker OPEN — entering fallback mode")
            else:
                self.state.fallback_mode = False
                logger.info("Circuit breaker CLOSED — resuming normal operation")

    # ──────────────────────────────────────────────
    # OEE Computation
    # ──────────────────────────────────────────────

    async def _compute_and_publish_oee(self, machine_id: str) -> None:
        """Compute OEE for a machine and publish the report."""
        machine_data = self._machine_states.get(machine_id)
        if not machine_data:
            return

        production_line = machine_data.get("production_line", "unknown")
        shift_id = machine_data.get("shift_id", "unknown")

        # Gather data from state buffer
        cycle_times = self._cycle_time_buffer.get(machine_id, [])
        avg_cycle = float(sum(cycle_times) / len(cycle_times)) if cycle_times else 60.0

        # Simplified OEE calculation with realistic defaults
        oee_result = self.oee_calculator.calculate_oee(
            production_line=production_line,
            shift_id=shift_id,
            period_start=datetime.now(timezone.utc).replace(hour=0, minute=0, second=0),
            period_end=datetime.now(timezone.utc),
            operating_time_minutes=machine_data.get("run_hours", 0) * 60,
            planned_production_time_minutes=480,  # 8-hour shift
            ideal_cycle_time_seconds=machine_data.get("ideal_cycle_time_seconds", 60),
            total_units_produced=machine_data.get("cycle_count", 0),
            total_good_units=int(machine_data.get("cycle_count", 0) * 0.97),  # 97% quality estimate
            total_defective_units=int(machine_data.get("cycle_count", 0) * 0.03),
            total_downtime_minutes=0.0,
            planned_downtime_minutes=0.0,
        )

        # Track last OEE by line
        self.state.last_oee_by_line[production_line] = oee_result.oee_pct

        # Publish OEE report
        report_data = oee_result.to_dict()
        await self.producer.publish_oee_report(
            data=report_data,
            subject=f"oee/{production_line}/{shift_id}",
        )
        self.state.total_published += 1
        self.state.total_oee_reports += 1

        # Persist
        await self.repository.save_oee_report(report_data)

        # Check critical OEE threshold
        if oee_result.oee_pct < settings.oee.oee_critical_threshold_pct:
            await self._handle_low_oee(production_line, oee_result)

    async def _handle_low_oee(self, production_line: str, oee_result: OEEBreakdown) -> None:
        """Handle OEE below critical threshold — escalate via HITL."""
        logger.warning(
            "OEE below critical threshold",
            line=production_line,
            oee=oee_result.oee_pct,
        )

        ticket = await self.hitl.create_ticket(
            title=f"OEE critical drop: {production_line} at {oee_result.oee_pct:.1f}%",
            description=(
                f"Production line {production_line} OEE has dropped to "
                f"{oee_result.oee_pct:.1f}% (threshold: {settings.oee.oee_critical_threshold_pct:.0f}%).\n\n"
                f"Availability: {oee_result.availability_pct:.1f}%\n"
                f"Performance: {oee_result.performance_pct:.1f}%\n"
                f"Quality: {oee_result.quality_pct:.1f}%\n\n"
                f"Action required: Operations Manager review needed immediately."
            ),
            priority=HITLPriority.P1_HIGH,
            source_agent="agent-02",
            context={
                "production_line": production_line,
                "oee_pct": oee_result.oee_pct,
                "availability_pct": oee_result.availability_pct,
                "performance_pct": oee_result.performance_pct,
                "quality_pct": oee_result.quality_pct,
            },
            sla_minutes=60,
        )
        self.state.active_hitl_tickets.append(ticket.ticket_id)

    async def _create_quality_hitl_ticket(self, alert: QualityAlertPayload) -> None:
        """Create HITL ticket for critical quality alert."""
        ticket = await self.hitl.create_ticket(
            title=f"Quality alert: {alert.defect_type} on {alert.machine_id} ({alert.severity.value})",
            description=(
                f"Quality violation detected on {alert.machine_id} "
                f"({alert.production_line}).\n\n"
                f"Rule violated: {alert.rule_violated}\n"
                f"Parameter: {alert.parameter_name} = {alert.parameter_value:.2f}\n"
                f"Control limits: [{alert.lower_control_limit:.2f}, {alert.upper_control_limit:.2f}]\n\n"
                f"Recommendation: {alert.recommendation}"
            ),
            priority=HITLPriority.P1_HIGH,
            source_agent="agent-02",
            context=alert.model_dump(mode="json"),
            sla_minutes=60,
        )
        self.state.active_hitl_tickets.append(ticket.ticket_id)
        logger.info("HITL ticket created for quality alert", ticket_id=ticket.ticket_id)

    async def _create_maintenance_hitl_ticket(
        self,
        machine_id: str,
        machine_name: str,
        failure_probability: float,
    ) -> None:
        """Create HITL ticket for immediate halt maintenance trigger."""
        ticket = await self.hitl.create_ticket(
            title=f"Immediate halt required: {machine_name} failure risk {failure_probability:.0%}",
            description=(
                f"Predictive maintenance model indicates {failure_probability:.0%} "
                f"probability of failure within 2 hours for {machine_name} ({machine_id}).\n\n"
                f"Recommended action: IMMEDIATE HALT — manual inspection required."
            ),
            priority=HITLPriority.P1_HIGH,
            source_agent="agent-02",
            context={
                "machine_id": machine_id,
                "machine_name": machine_name,
                "failure_probability": failure_probability,
            },
            sla_minutes=30,
        )
        self.state.active_hitl_tickets.append(ticket.ticket_id)
        logger.info("HITL ticket created for maintenance halt", ticket_id=ticket.ticket_id)

    # ──────────────────────────────────────────────
    # HITL Callback
    # ──────────────────────────────────────────────

    async def _on_hitl_response(self, ticket: HITLTicket) -> None:
        """Callback when a HITL decision is received."""
        self.state.active_hitl_tickets = [
            t for t in self.state.active_hitl_tickets if t != ticket.ticket_id
        ]

        logger.info(
            "HITL response received",
            ticket_id=ticket.ticket_id,
            status=ticket.status.value,
            decision=ticket.decision,
        )

        # Publish HITL outcome event
        await self.producer.publish(
            topic=self.settings.kafka.topic_production_events,
            event_type="com.manufacturing.production.hitl-decision",
            data={
                "ticket_id": ticket.ticket_id,
                "status": ticket.status.value,
                "decision": ticket.decision,
                "resolved_by": ticket.resolved_by,
                "context": ticket.context,
            },
            subject=f"hitl/{ticket.ticket_id}",
        )
        self.state.total_published += 1

    # ──────────────────────────────────────────────
    # Public API Methods
    # ──────────────────────────────────────────────

    async def compute_oee_for_line(
        self,
        production_line: str,
        shift_id: str,
        operating_time_minutes: float,
        planned_production_time_minutes: float,
        ideal_cycle_time_seconds: float,
        total_units_produced: int,
        total_good_units: int,
        total_defective_units: int,
        total_downtime_minutes: float,
        planned_downtime_minutes: float,
    ) -> dict[str, Any]:
        """Public API: Compute OEE for a specific line and shift."""
        oee_result = self.oee_calculator.calculate_oee(
            production_line=production_line,
            shift_id=shift_id,
            period_start=datetime.now(timezone.utc).replace(hour=0, minute=0, second=0),
            period_end=datetime.now(timezone.utc),
            operating_time_minutes=operating_time_minutes,
            planned_production_time_minutes=planned_production_time_minutes,
            ideal_cycle_time_seconds=ideal_cycle_time_seconds,
            total_units_produced=total_units_produced,
            total_good_units=total_good_units,
            total_defective_units=total_defective_units,
            total_downtime_minutes=total_downtime_minutes,
            planned_downtime_minutes=planned_downtime_minutes,
        )

        report_data = oee_result.to_dict()

        # Publish
        await self.producer.publish_oee_report(
            data=report_data,
            subject=f"oee/{production_line}/{shift_id}",
        )
        self.state.total_published += 1
        self.state.total_oee_reports += 1

        # Persist
        await self.repository.save_oee_report(report_data)

        return report_data

    async def trigger_maintenance_evaluation(
        self,
        machine_id: str,
        machine_name: str,
        failure_probability: float,
        confidence: float,
        features: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """Public API: Evaluate a predictive maintenance trigger."""
        evaluation = self.scheduler.evaluate_maintenance_trigger(
            machine_id=machine_id,
            machine_name=machine_name,
            failure_probability=failure_probability,
            confidence=confidence,
            features=features,
            proactive_threshold=settings.oee.pm_confidence_threshold,
            immediate_halt_threshold=settings.oee.pm_critical_confidence,
        )

        trigger_payload = MaintenanceTriggerPayload(
            machine_id=evaluation.machine_id,
            machine_name=evaluation.machine_name,
            priority=MaintenancePriority.IMMEDIATE_HALT if evaluation.immediate_halt
                    else MaintenancePriority.PROACTIVE if evaluation.action_required
                    else MaintenancePriority.ROUTINE,
            failure_probability=evaluation.failure_probability,
            predicted_failure_hours=evaluation.predicted_failure_hours,
            recommended_action=evaluation.recommended_action,
            features=features or {},
            confidence=evaluation.confidence,
        )

        # Publish maintenance trigger
        await self.producer.publish_maintenance_trigger(
            data=trigger_payload.model_dump(mode="json"),
            subject=f"maintenance/{machine_id}/{trigger_payload.trigger_id}",
        )
        self.state.total_published += 1
        self.state.total_maintenance_triggers += 1

        # Persist
        await self.repository.save_maintenance_trigger(trigger_payload.model_dump(mode="json"))

        # HITL if immediate halt required
        if evaluation.immediate_halt:
            await self._create_maintenance_hitl_ticket(
                machine_id=machine_id,
                machine_name=machine_name,
                failure_probability=failure_probability,
            )

        return trigger_payload.model_dump(mode="json")

    async def optimize_schedule(
        self,
        orders: list[dict[str, Any]],
        production_line: str,
        shift_start: datetime,
        shift_end: datetime | None = None,
    ) -> dict[str, Any]:
        """Public API: Optimize production schedule for a line."""
        # Convert dict orders to ProductionOrder objects
        production_orders = []
        for o in orders:
            production_orders.append(ProductionOrder(
                order_id=o.get("order_id", ""),
                product_id=o.get("product_id", ""),
                product_name=o.get("product_name", ""),
                quantity=o.get("quantity", 0),
                due_date=o.get("due_date", datetime.now(timezone.utc)),
                priority=o.get("priority", 50),
                setup_time_minutes=o.get("setup_time_minutes", 30.0),
                cycle_time_per_unit_seconds=o.get("cycle_time_per_unit_seconds", 60.0),
                material_available=o.get("material_available", True),
                customer_tier=o.get("customer_tier", 3),
                committed=o.get("committed", False),
            ))

        # Get cached production plan
        cached_plan = await self.cache.get_production_plan(production_line)
        last_hash = cached_plan.get("schedule_hash", "") if cached_plan else ""

        schedule = self.scheduler.schedule_production(
            orders=production_orders,
            production_line=production_line,
            shift_start=shift_start,
            shift_end=shift_end,
            last_sequence_hash=last_hash,
        )

        # Publish schedule
        schedule_data = schedule.to_dict()
        await self.producer.publish_production_schedule(
            data=schedule_data,
            subject=f"schedule/{production_line}/{schedule.schedule_id}",
        )
        self.state.total_published += 1
        self.state.total_schedule_optimizations += 1

        # Cache
        await self.cache.set_production_plan(production_line, {
            "schedule_hash": schedule_data.get("schedule_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        # HITL if required
        if schedule.hitl_required:
            ticket = await self.hitl.create_ticket(
                title=f"Schedule variance {schedule.variance_hours:.1f}h exceeds threshold on {production_line}",
                description=(
                    f"Production schedule for {production_line} has a variance of "
                    f"{schedule.variance_hours:.1f} hours from the previous plan "
                    f"(threshold: {settings.oee.schedule_variance_hours:.0f}h).\n\n"
                    f"Total orders: {schedule.total_orders}\n"
                    f"Optimization score: {schedule.optimization_score:.1f}/100\n\n"
                    f"Reason: {schedule.variance_reason or 'Schedule re-optimization'}"
                ),
                priority=HITLPriority.P2_MEDIUM,
                source_agent="agent-02",
                context=schedule_data,
                sla_minutes=120,
            )
            self.state.active_hitl_tickets.append(ticket.ticket_id)

        return schedule_data

    async def analyze_bottlenecks(
        self,
        machine_stats: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Public API: Identify bottleneck in a production line."""
        analysis = self.oee_calculator.identify_bottleneck(machine_stats)

        bottleneck_payload = BottleneckAnalysisPayload(
            production_line=machine_stats[0].get("production_line", "unknown") if machine_stats else "unknown",
            bottleneck_machine_id=analysis.get("bottleneck_machine_id", ""),
            constraint_type=analysis.get("constraint_type", ""),
            cycle_time_delta_pct=machine_stats[0].get("cycle_time_delta_pct", 0.0) if machine_stats else 0.0,
            queue_length=analysis.get("queue_length", 0),
            utilization_pct=analysis.get("utilization_pct", 0),
            recommendations=analysis.get("recommendations", []),
        )

        # Publish
        await self.producer.publish_bottleneck_analysis(
            data=bottleneck_payload.model_dump(mode="json"),
            subject=f"bottleneck/{bottleneck_payload.production_line}/{bottleneck_payload.analysis_id}",
        )
        self.state.total_published += 1

        return bottleneck_payload.model_dump(mode="json")

    async def get_health(self) -> dict[str, Any]:
        """Public API: Get agent health and metrics."""
        return self.state.to_dict()
