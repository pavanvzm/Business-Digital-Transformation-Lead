"""Core Inventory & Warehousing Agent — manages reorder points, stock rotation, dead stock detection, and HITL escalation.

Architecture follows the shared Agent-01/Agent-02 pattern:
- EventConsumer / EventProducer: Kafka pub/sub with CloudEvents
- InventoryAnalyzer: Dynamic safety stock, EOQ, stock-out probability
- HITLGate: Human-in-the-Loop integration (shared package)
- InventoryRepository / CacheManager: PostgreSQL + Redis persistence
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from config.settings import settings
from src.hitl.gate import HITLGate, HITLPriority, HITLTicket

logger = logging.getLogger(__name__)


class AgentState:
    """Runtime state tracking for the inventory agent."""

    def __init__(self) -> None:
        self.started_at: datetime | None = None
        self.total_messages_consumed: int = 0
        self.total_published: int = 0
        self.total_reorder_recommendations: int = 0
        self.total_dead_stock_alerts: int = 0
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
            "total_reorder_recommendations": self.total_reorder_recommendations,
            "total_dead_stock_alerts": self.total_dead_stock_alerts,
            "total_errors": self.total_errors,
            "fallback_mode": self.fallback_mode,
            "paused": self.orchestrator_paused,
            "active_hitl_tickets": self.active_hitl_tickets,
        }


class InventoryAgent:
    """Main inventory & warehousing agent — coordinates stock management and HITL escalation.

    Architecture:
        Consumer ← Kafka (sales, production, forecast, orchestrator events)
        Producer → Kafka (inventory events, dead-letter)
        HITL → HITLGate (shared — stock-out, dead stock, space utilization)
    """

    def __init__(self) -> None:
        self.state = AgentState()
        self.settings = settings

        # HITL gate — shared implementation
        self.hitl = HITLGate(
            poll_interval_seconds=settings.hitl_poll_interval_seconds,
            default_timeout_seconds=settings.hitl_timeout_seconds,
        )

        # Shutdown event
        self._shutdown_event = asyncio.Event()

    async def start(self) -> None:
        """Start the inventory agent."""
        self.state.started_at = datetime.now(timezone.utc)
        logger.info(
            "Starting Inventory & Warehousing Agent",
            agent_id=settings.agent_id,
            environment=settings.environment,
        )

    async def run(self) -> None:
        """Main run loop."""
        try:
            hitl_task = asyncio.create_task(
                self.hitl.poll_pending_decisions(self._on_hitl_response)
            )
            await asyncio.wait([hitl_task], return_when=asyncio.FIRST_COMPLETED)
        except asyncio.CancelledError:
            logger.info("Run loop cancelled")
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        """Graceful shutdown."""
        logger.info("Shutting down Inventory Agent")

    async def _on_hitl_response(self, ticket: HITLTicket) -> None:
        """Callback when a HITL decision is received."""
        self.state.active_hitl_tickets = [
            t for t in self.state.active_hitl_tickets if t != ticket.ticket_id
        ]
        logger.info(
            "HITL response received",
            ticket_id=ticket.ticket_id,
            status=ticket.status.value,
        )

    # ── Public API — HITL Triggers ──────────────────────────────────────────

    async def raise_stockout_alert(
        self,
        sku: str,
        material_name: str,
        current_stock: float,
        stockout_probability: float,
        lead_time_days: int,
    ) -> dict[str, Any]:
        """Raise a HITL alert for stock-out risk >15% probability.

        Corresponds to HITL policy scenario H-014 (Agent-03).
        """
        ticket = await self.hitl.create_ticket(
            title=f"Stock-out risk: {material_name} ({stockout_probability:.0%} probability)",
            description=(
                f"SKU {sku} ({material_name}) has a {stockout_probability:.0%} "
                f"probability of stock-out within {lead_time_days}-day lead time. "
                f"Current stock: {current_stock:.0f} units.\n\n"
                f"Threshold: {settings.inventory.stock_out_probability_hitl:.0%}\n"
                f"Recommendation: Expedite procurement or adjust safety stock."
            ),
            priority=HITLPriority.P1_HIGH,
            source_agent="agent-03",
            context={
                "sku": sku,
                "material_name": material_name,
                "current_stock": current_stock,
                "stockout_probability": stockout_probability,
                "lead_time_days": lead_time_days,
            },
            sla_minutes=60,
        )
        self.state.active_hitl_tickets.append(ticket.ticket_id)
        return ticket.to_dict()

    async def raise_dead_stock_alert(
        self,
        sku: str,
        material_name: str,
        dead_stock_value: float,
        total_inventory_value: float,
        days_without_movement: int,
    ) -> dict[str, Any]:
        """Raise a HITL alert for dead stock exceeding 5% of total inventory value.

        Corresponds to HITL policy scenario H-032 (Agent-03).
        """
        pct_of_total = (dead_stock_value / total_inventory_value * 100) if total_inventory_value > 0 else 0
        ticket = await self.hitl.create_ticket(
            title=f"Dead stock alert: {material_name} ({pct_of_total:.1f}% of inventory value)",
            description=(
                f"SKU {sku} ({material_name}) has had zero movement for "
                f"{days_without_movement} days. Value at risk: ${dead_stock_value:,.2f} "
                f"({pct_of_total:.1f}% of total inventory).\n\n"
                f"Recommendation: Review for write-off, donation, or discount sale."
            ),
            priority=HITLPriority.P2_MEDIUM,
            source_agent="agent-03",
            context={
                "sku": sku,
                "material_name": material_name,
                "dead_stock_value": dead_stock_value,
                "total_inventory_value": total_inventory_value,
                "pct_of_total": pct_of_total,
                "days_without_movement": days_without_movement,
            },
            sla_minutes=240,
        )
        self.state.active_hitl_tickets.append(ticket.ticket_id)
        return ticket.to_dict()

    async def raise_space_utilization_alert(
        self,
        warehouse_zone: str,
        utilization_pct: float,
    ) -> dict[str, Any]:
        """Raise a HITL alert for warehouse space utilization >92%.

        Corresponds to HITL policy scenario H-042 (Agent-03).
        """
        ticket = await self.hitl.create_ticket(
            title=f"Warehouse space critical: {warehouse_zone} at {utilization_pct:.0f}%",
            description=(
                f"Warehouse zone {warehouse_zone} is at {utilization_pct:.0f}% capacity "
                f"(critical threshold: {settings.inventory.space_utilization_critical_pct:.0f}%).\n\n"
                f"Recommendation: Evaluate cross-docking, off-site storage, or slotting optimization."
            ),
            priority=HITLPriority.P2_MEDIUM,
            source_agent="agent-03",
            context={
                "warehouse_zone": warehouse_zone,
                "utilization_pct": utilization_pct,
                "critical_threshold": settings.inventory.space_utilization_critical_pct,
            },
            sla_minutes=240,
        )
        self.state.active_hitl_tickets.append(ticket.ticket_id)
        return ticket.to_dict()

    async def get_health(self) -> dict[str, Any]:
        """Public API: Get agent health and metrics."""
        return self.state.to_dict()
