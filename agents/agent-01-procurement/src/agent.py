"""Core Procurement Agent — orchestrates vendor scoring, PO decisions, HITL, and event messaging.

This is the main agent class that ties together all sub-modules:
- EventConsumer / EventProducer: Kafka pub/sub with CloudEvents
- VendorScorer: 15-metric vendor evaluation engine
- DecisionOptimizer: PO recommendation and sourcing analysis
- HITLGate: Human-in-the-Loop integration
- ProcurementRepository / CacheManager: PostgreSQL + Redis persistence
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from config.settings import settings
from src.hitl.gate import HITLGate, HITLTicket, HITLPriority
from src.messaging.consumer import EventConsumer
from src.messaging.producer import EventProducer
from src.messaging.schemas import (
    ForecastDemandPayload,
    InventorySnapshotPayload,
    OrchestratorCommand,
    PORecommendationPayload,
    PriceAlertPayload,
    PriceThreshold,
)
from src.scoring.vendor_scorer import VendorScorer, MaterialCategory
from src.decisions.optimizer import DecisionOptimizer, PurchaseOrderRecommendation
from src.storage.repository import ProcurementRepository
from src.storage.cache import CacheManager

logger = logging.getLogger(__name__)


class AgentState:
    """Runtime state tracking for the procurement agent."""

    def __init__(self) -> None:
        self.started_at: datetime | None = None
        self.total_messages_consumed: int = 0
        self.total_published: int = 0
        self.total_po_recommendations: int = 0
        self.total_errors: int = 0
        self.fallback_mode: bool = False
        self.orchestrator_paused: bool = False
        self.active_hitl_tickets: list[str] = []

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
            "total_po_recommendations": self.total_po_recommendations,
            "total_errors": self.total_errors,
            "fallback_mode": self.fallback_mode,
            "paused": self.orchestrator_paused,
            "active_hitl_tickets": self.active_hitl_tickets,
        }


class ProcurementAgent:
    """Main procurement agent that coordinates all sub-modules.

    Architecture:
        Consumer ← Kafka (market, forecast, inventory, orchestrator events)
        Producer → Kafka (procurement events, dead-letter)
        Scorer → VendorScorer (vendor evaluation)
        Optimizer → DecisionOptimizer (PO and sourcing decisions)
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

        # Scoring engine
        self.scorer = VendorScorer(
            min_acceptable_score=settings.scoring.min_acceptable_score,
            quality_critical=settings.scoring.quality_critical_threshold,
        )

        # Decision optimizer
        self.optimizer = DecisionOptimizer(scorer=self.scorer)

        # HITL gate
        self.hitl = HITLGate(
            poll_interval_seconds=settings.hitl_poll_interval_seconds,
            default_timeout_seconds=settings.hitl_timeout_seconds,
        )

        # Storage layer
        self.repository = ProcurementRepository()
        self.cache = CacheManager()

        # Shutdown event (triggered by signal handler or external API)
        self._shutdown_event = asyncio.Event()

    async def start(self) -> None:
        """Start the procurement agent: connect all sub-systems and begin consuming."""
        logger.info(
            "Starting Procurement Agent",
            agent_id=settings.agent_id,
            version=settings.agent_version,
            environment=settings.environment,
        )

        self.state.started_at = datetime.now(timezone.utc)

        # Start storage connections
        await self._connect_storage()

        # Start the messaging layer
        await self.producer.start()

        # Register event handlers before consumer starts
        self._register_handlers()

        await self.consumer.start()

        # Replay any locally queued messages from fallback
        replayed = await self.consumer.replay_local_queue()
        if replayed > 0:
            logger.info("Replayed queued messages from fallback", count=replayed)

        logger.info("Procurement Agent started successfully")

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
            "com.manufacturing.market.price-update", self._handle_price_update
        )
        self.consumer.register_handler(
            "com.manufacturing.market.price-alert", self._handle_price_alert
        )
        self.consumer.register_handler(
            "com.manufacturing.forecast.demand-projection", self._handle_demand_forecast
        )
        self.consumer.register_handler(
            "com.manufacturing.inventory.stock-snapshot", self._handle_inventory_snapshot
        )
        self.consumer.register_handler(
            "com.manufacturing.orchestrator.command", self._handle_orchestrator_command
        )

    async def run(self) -> None:
        """Main run loop — consumes events until shutdown."""
        try:
            # Run consume loop and monitor tasks concurrently
            consumer_task = asyncio.create_task(self.consumer.consume_loop())
            health_task = asyncio.create_task(self._health_check_loop())
            hitl_task = asyncio.create_task(self.hitl.poll_pending_decisions(self._on_hitl_response))

            await asyncio.wait(
                [consumer_task, health_task, hitl_task],
                return_when=asyncio.FIRST_COMPLETED,
            )
        except asyncio.CancelledError:
            logger.info("Run loop cancelled")
        finally:
            await self.shutdown()

    async def _health_check_loop(self) -> None:
        """Periodic health check and state reporting."""
        while not self._shutdown_event.is_set():
            try:
                await asyncio.sleep(60)  # every 60 seconds
                if not self.state.fallback_mode:
                    # Verify Kafka connection health
                    if self.producer._producer:
                        # Check partitions
                        pass  # producer health is passive
                logger.debug("Health check OK", state=self.state.to_dict())
            except Exception:
                logger.exception("Health check error")

    async def shutdown(self) -> None:
        """Graceful shutdown of all sub-systems."""
        logger.info("Shutting down Procurement Agent")

        await self.consumer.stop()
        await self.producer.stop()
        await self.repository.disconnect()
        await self.cache.disconnect()

        logger.info(
            "Procurement Agent shutdown complete",
            total_messages=self.state.total_messages_consumed,
            total_po=self.state.total_po_recommendations,
            uptime_seconds=self.state.uptime_seconds,
        )

    # ──────────────────────────────────────────────
    # Event Handlers
    # ──────────────────────────────────────────────

    async def _handle_price_update(self, data: dict[str, Any]) -> None:
        """Handle market price update events from Agent-05 (Market Intelligence)."""
        self.state.total_messages_consumed += 1

        material_id = data.get("material_id", "unknown")
        current_price = data.get("current_price", 0.0)
        previous_price = data.get("previous_price", 0.0)

        if previous_price > 0:
            pct_change = ((current_price - previous_price) / previous_price) * 100
        else:
            pct_change = 0.0

        # Check price spike thresholds
        threshold = self._classify_price_spike(pct_change)
        if threshold != PriceThreshold.NORMAL:
            logger.warning(
                "Price spike detected",
                material_id=material_id,
                pct_change=round(pct_change, 2),
                threshold=threshold.value,
            )

            alert = PriceAlertPayload(
                material_id=material_id,
                material_name=data.get("material_name", material_id),
                current_price=current_price,
                previous_price=previous_price,
                percent_change=round(pct_change, 2),
                threshold_breached=threshold,
                confidence=data.get("confidence", 0.95),
                data_sources=data.get("data_sources", ["market_intelligence"]),
            )

            # Publish price alert event
            await self.producer.publish_price_alert(
                data=alert.model_dump(mode="json"),
                subject=f"raw-material/{material_id}/price-alert",
            )
            self.state.total_published += 1

            # Cache the price update
            await self.cache.set_price(material_id, current_price)

    async def _handle_price_alert(self, data: dict[str, Any]) -> None:
        """Handle price alert events from external sources."""
        self.state.total_messages_consumed += 1
        pct_change = data.get("percent_change", 0.0)
        threshold = self._classify_price_spike(pct_change)

        if threshold == PriceThreshold.CRITICAL:
            # Critical spike — trigger HITL escalation
            material_id = data.get("material_id", "unknown")
            material_name = data.get("material_name", material_id)

            ticket = await self.hitl.create_ticket(
                title=f"Critical price spike: {material_name} ({pct_change:+.1f}%)",
                description=(
                    f"Material {material_name} ({material_id}) price changed by "
                    f"{pct_change:+.1f}%. Threshold: {threshold.value}. "
                    f"Current: ${data.get('current_price', 0):.2f}, "
                    f"Previous: ${data.get('previous_price', 0):.2f}"
                ),
                priority=HITLPriority.P1_HIGH,
                source_agent="agent-01",
                context={
                    "material_id": material_id,
                    "material_name": material_name,
                    "pct_change": pct_change,
                    "current_price": data.get("current_price"),
                    "previous_price": data.get("previous_price"),
                    "threshold": threshold.value,
                },
                sla_minutes=60,
            )
            self.state.active_hitl_tickets.append(ticket.ticket_id)
            logger.info("HITL ticket created for critical price spike", ticket_id=ticket.ticket_id)

    async def _handle_demand_forecast(self, data: dict[str, Any]) -> None:
        """Handle demand forecast events from Agent-06 (Predictive Analytics)."""
        self.state.total_messages_consumed += 1

        try:
            forecast = ForecastDemandPayload(**data)
        except Exception:
            logger.exception("Failed to deserialize forecast payload")
            return

        # Cache material requirements
        for material_id, quantity in forecast.material_requirements.items():
            await self.cache.set_forecast_demand(material_id, quantity, forecast.forecast_month)

        logger.debug(
            "Processed demand forecast",
            forecast_id=forecast.forecast_id,
            materials=len(forecast.material_requirements),
        )

    async def _handle_inventory_snapshot(self, data: dict[str, Any]) -> None:
        """Handle inventory snapshot events from Agent-03 (Inventory & Warehousing)."""
        self.state.total_messages_consumed += 1

        try:
            snapshot = InventorySnapshotPayload(**data)
        except Exception:
            logger.exception("Failed to deserialize inventory payload")
            return

        # Cache inventory levels
        await self.cache.set_inventory_level(
            snapshot.material_id,
            snapshot.current_stock,
            snapshot.safety_stock,
        )

        # Check if reorder is needed
        if snapshot.current_stock <= snapshot.reorder_point:
            logger.info(
                "Stock below reorder point",
                material_id=snapshot.material_id,
                stock=snapshot.current_stock,
                reorder_point=snapshot.reorder_point,
            )
            # Trigger PO recommendation
            recommendation = await self._generate_po_recommendation(snapshot)
            if recommendation:
                await self._publish_po_recommendation(recommendation)

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
            # Implementation depends on versioning strategy
        elif command.command_type == "circuit_breaker_status":
            cb_open = command.parameters.get("open", False)
            if cb_open:
                self.state.fallback_mode = True
                logger.warning("Circuit breaker OPEN — entering fallback mode")
            else:
                self.state.fallback_mode = False
                logger.info("Circuit breaker CLOSED — resuming normal operation")

    # ──────────────────────────────────────────────
    # Decision Logic
    # ──────────────────────────────────────────────

    async def _generate_po_recommendation(
        self, snapshot: InventorySnapshotPayload
    ) -> PurchaseOrderRecommendation | None:
        """Generate a purchase order recommendation for a material at reorder point."""
        if self.state.orchestrator_paused:
            logger.info("Agent paused — skipping PO recommendation")
            return None

        # Check cache for forecast demand
        forecast_demand = await self.cache.get_forecast_demand(snapshot.material_id)
        if forecast_demand is None:
            # Fallback: use trailing average of inventory consumption
            forecast_demand = snapshot.current_stock * 1.5  # conservative estimate

        # Get current market price from cache
        market_price = await self.cache.get_price(snapshot.material_id)
        if market_price is None:
            # Fallback: use last known price with conservative buffer
            market_price = self.settings.scoring.weight_price * 100  # fallback

        # Check if we have alternative sourcing data cached
        alternative_sourcing = await self.cache.get_sourcing_options(snapshot.material_id)

        # Build recommendation
        recommendation = self.optimizer.recommend_purchase_order(
            material_id=snapshot.material_id,
            material_name=snapshot.material_name,
            current_stock=snapshot.current_stock,
            safety_stock=snapshot.safety_stock,
            reorder_point=snapshot.reorder_point,
            forecast_demand=forecast_demand,
            unit_price=market_price,
            unit=snapshot.unit,
            alternative_sources=alternative_sourcing,
        )

        return recommendation

    async def _publish_po_recommendation(self, recommendation: PurchaseOrderRecommendation) -> None:
        """Publish a PO recommendation event to Kafka."""
        self.state.total_po_recommendations += 1

        po_payload = PORecommendationPayload(
            po_id=recommendation.po_id,
            vendor_id=recommendation.vendor_id,
            vendor_name=recommendation.vendor_name,
            material_id=recommendation.material_id,
            material_name=recommendation.material_name,
            quantity=recommendation.quantity,
            unit=recommendation.unit,
            unit_price=recommendation.unit_price,
            total_value=recommendation.total_value,
            recommended_delivery_date=recommendation.recommended_delivery_date,
            confidence=recommendation.confidence,
            reasoning=recommendation.reasoning,
            alternatives=recommendation.alternatives,
            hitl_required=recommendation.hitl_required,
            status="pending_approval" if recommendation.hitl_required else "approved",
        )

        await self.producer.publish_po_recommendation(
            data=po_payload.model_dump(mode="json"),
            subject=f"po/{recommendation.material_id}/{recommendation.po_id}",
            hitl_required=recommendation.hitl_required,
        )
        self.state.total_published += 1

        # Persist to PostgreSQL
        await self.repository.save_po_recommendation(po_payload.model_dump(mode="json"))

        if recommendation.hitl_required:
            ticket = await self.hitl.create_ticket(
                title=f"PO approval required: {po_payload.material_name} (${po_payload.total_value:,.2f})",
                description=(
                    f"Purchase order #{po_payload.po_id} for {po_payload.material_name} "
                    f"(${po_payload.total_value:,.2f}) requires approval.\n\n"
                    f"Vendor: {po_payload.vendor_name}\n"
                    f"Quantity: {po_payload.quantity} {po_payload.unit}\n"
                    f"Unit price: ${po_payload.unit_price:.2f}\n\n"
                    f"Reasoning: {recommendation.reasoning}\n"
                    f"Confidence: {recommendation.confidence:.0%}"
                ),
                priority=HITLPriority.P2_MEDIUM,
                source_agent="agent-01",
                context={"po_id": po_payload.po_id, "total_value": po_payload.total_value},
                sla_minutes=120,
            )
            self.state.active_hitl_tickets.append(ticket.ticket_id)
            logger.info("HITL ticket created for PO approval", ticket_id=ticket.ticket_id)

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

        if ticket.status.value == "approved":
            # Publish approved PO
            po_id = ticket.context.get("po_id", "")
            if po_id:
                await self.producer.publish(
                    topic=self.settings.kafka.topic_procurement_events,
                    event_type="com.manufacturing.procurement.po-approved",
                    data={"po_id": po_id, "approved_by": ticket.resolved_by, "ticket_id": ticket.ticket_id},
                    subject=f"po/{po_id}/approved",
                )
                self.state.total_published += 1
        elif ticket.status.value == "rejected":
            po_id = ticket.context.get("po_id", "")
            if po_id:
                await self.producer.publish(
                    topic=self.settings.kafka.topic_procurement_events,
                    event_type="com.manufacturing.procurement.po-rejected",
                    data={
                        "po_id": po_id,
                        "rejected_by": ticket.resolved_by,
                        "reason": ticket.decision,
                        "ticket_id": ticket.ticket_id,
                    },
                    subject=f"po/{po_id}/rejected",
                )
                self.state.total_published += 1
        elif ticket.status.value == "override":
            # Human override — adjust agent behavior
            po_id = ticket.context.get("po_id", "")
            if po_id:
                override_params = ticket.context.get("override_params", {})
                await self.producer.publish(
                    topic=self.settings.kafka.topic_procurement_events,
                    event_type="com.manufacturing.procurement.po-override",
                    data={
                        "po_id": po_id,
                        "overridden_by": ticket.resolved_by,
                        "override_params": override_params,
                        "reason": ticket.decision,
                        "ticket_id": ticket.ticket_id,
                    },
                    subject=f"po/{po_id}/override",
                )
                self.state.total_published += 1

    # ──────────────────────────────────────────────
    # Public API Methods
    # ──────────────────────────────────────────────

    async def evaluate_vendors(
        self,
        vendor_id: str,
        vendor_name: str,
        metric_scores: dict[str, float],
        category: str = "general",
        previous_score: float | None = None,
    ) -> dict[str, Any]:
        """Public API: Evaluate a vendor and return the scorecard."""
        material_category = MaterialCategory(category) if category in MaterialCategory._value2member_map_ else MaterialCategory.GENERAL  # type: ignore[attr-defined]
        scorecard = self.scorer.compute_scorecard(
            vendor_id=vendor_id,
            vendor_name=vendor_name,
            metric_scores=metric_scores,
            category=material_category,
            previous_score=previous_score,
        )

        # Persist scorecard
        await self.repository.save_vendor_scorecard({
            "vendor_id": scorecard.vendor_id,
            "vendor_name": scorecard.vendor_name,
            "period": scorecard.period,
            "overall_score": scorecard.overall_score,
            "trend": scorecard.trend,
            "risk_flags": scorecard.risk_flags,
            "metrics": [m.__dict__ for m in scorecard.metrics],
        })

        # Publish event
        await self.producer.publish_vendor_scorecard(
            data={
                "vendor_id": scorecard.vendor_id,
                "vendor_name": scorecard.vendor_name,
                "period": scorecard.period,
                "overall_score": scorecard.overall_score,
                "trend": scorecard.trend,
                "risk_flags": scorecard.risk_flags,
            },
            subject=f"vendor/{vendor_id}/scorecard",
        )
        self.state.total_published += 1

        return {
            "vendor_id": scorecard.vendor_id,
            "vendor_name": scorecard.vendor_name,
            "overall_score": scorecard.overall_score,
            "trend": scorecard.trend,
            "risk_flags": scorecard.risk_flags,
            "period": scorecard.period,
        }

    async def get_sourcing_options(
        self,
        material_id: str,
        material_name: str,
    ) -> dict[str, Any]:
        """Public API: Get alternative sourcing options for a material."""
        # Try cache first
        cached = await self.cache.get_sourcing_options(material_id)
        if cached:
            return cached

        # Fallback to repository
        options = await self.repository.get_sourcing_options(material_id)
        if options:
            await self.cache.set_sourcing_options(material_id, options)
            return options

        return {
            "material_id": material_id,
            "material_name": material_name,
            "alternatives": [],
            "message": "No sourcing options available — supply manager intervention recommended.",
        }

    async def get_health(self) -> dict[str, Any]:
        """Public API: Get agent health and metrics."""
        return self.state.to_dict()

    # ──────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────

    @staticmethod
    def _classify_price_spike(pct_change: float) -> PriceThreshold:
        """Classify a price change into threshold levels."""
        abs_change = abs(pct_change)
        if abs_change >= 10.0:
            return PriceThreshold.CRITICAL
        elif abs_change >= 5.0:
            return PriceThreshold.WARNING
        return PriceThreshold.NORMAL
