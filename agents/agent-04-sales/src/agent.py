"""Core Sales & Distribution Agent — manages order routing, fulfillment, pricing, and HITL escalation.

Architecture follows the shared Agent-01/Agent-02 pattern:
- EventConsumer / EventProducer: Kafka pub/sub with CloudEvents
- OrderFulfillment: Order routing, allocation, and fulfillment optimization
- HITLGate: Human-in-the-Loop integration (shared package)
- SalesRepository / CacheManager: PostgreSQL + Redis persistence
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
    """Runtime state tracking for the sales agent."""

    def __init__(self) -> None:
        self.started_at: datetime | None = None
        self.total_messages_consumed: int = 0
        self.total_published: int = 0
        self.total_orders_processed: int = 0
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
            "total_orders_processed": self.total_orders_processed,
            "total_errors": self.total_errors,
            "fallback_mode": self.fallback_mode,
            "paused": self.orchestrator_paused,
            "active_hitl_tickets": self.active_hitl_tickets,
        }


class SalesAgent:
    """Main sales & distribution agent — coordinates order processing and HITL escalation.

    Architecture:
        Consumer ← Kafka (inventory, market, production, orchestrator events)
        Producer → Kafka (sales events, dead-letter)
        HITL → HITLGate (shared — pricing, allocation, bulk orders)
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
        """Start the sales agent."""
        self.state.started_at = datetime.now(timezone.utc)
        logger.info(
            "Starting Sales & Distribution Agent",
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
        logger.info("Shutting down Sales Agent")

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

    async def raise_pricing_alert(
        self,
        product_id: str,
        product_name: str,
        current_price: float,
        proposed_price: float,
        pct_change: float,
        customer_tier: int,
    ) -> dict[str, Any]:
        """Raise a HITL alert for pricing change >5%.

        Corresponds to HITL policy scenario H-017 (Agent-04).
        """
        ticket = await self.hitl.create_ticket(
            title=f"Pricing change alert: {product_name} ({pct_change:+.1f}%)",
            description=(
                f"Price change proposed for {product_name} ({product_id}):\n"
                f"Current: ${current_price:.2f} → Proposed: ${proposed_price:.2f} "
                f"({pct_change:+.1f}%)\n"
                f"Customer tier: {customer_tier}\n\n"
                f"Threshold: {settings.sales.pricing_change_hitl_pct:.0f}%\n"
                f"Recommendation: Review competitive positioning and margin impact."
            ),
            priority=HITLPriority.P1_HIGH,
            source_agent="agent-04",
            context={
                "product_id": product_id,
                "product_name": product_name,
                "current_price": current_price,
                "proposed_price": proposed_price,
                "pct_change": pct_change,
                "customer_tier": customer_tier,
            },
            sla_minutes=60,
        )
        self.state.active_hitl_tickets.append(ticket.ticket_id)
        return ticket.to_dict()

    async def raise_allocation_alert(
        self,
        customer_id: str,
        customer_name: str,
        product_id: str,
        allocated_qty: float,
        requested_qty: float,
        allocation_pct_change: float,
    ) -> dict[str, Any]:
        """Raise a HITL alert for customer allocation change >10%.

        Corresponds to HITL policy scenario H-019 (Agent-04).
        """
        ticket = await self.hitl.create_ticket(
            title=f"Allocation change alert: {customer_name} ({allocation_pct_change:+.1f}%)",
            description=(
                f"Customer {customer_name} ({customer_id}) allocation change:\n"
                f"Requested: {requested_qty:.0f} units\n"
                f"Allocated: {allocated_qty:.0f} units\n"
                f"Change: {allocation_pct_change:+.1f}%\n\n"
                f"Recommendation: Review customer tier priority and inventory availability."
            ),
            priority=HITLPriority.P1_HIGH,
            source_agent="agent-04",
            context={
                "customer_id": customer_id,
                "customer_name": customer_name,
                "product_id": product_id,
                "allocated_qty": allocated_qty,
                "requested_qty": requested_qty,
                "allocation_pct_change": allocation_pct_change,
            },
            sla_minutes=60,
        )
        self.state.active_hitl_tickets.append(ticket.ticket_id)
        return ticket.to_dict()

    async def raise_bulk_order_alert(
        self,
        order_id: str,
        customer_id: str,
        customer_name: str,
        total_value: float,
        product_count: int,
    ) -> dict[str, Any]:
        """Raise a HITL alert for bulk order value exceeding threshold.

        Corresponds to HITL policy scenario H-044 (Agent-04).
        """
        ticket = await self.hitl.create_ticket(
            title=f"Bulk order approval: {customer_name} (${total_value:,.2f})",
            description=(
                f"Order {order_id} from {customer_name} ({customer_id}) "
                f"for ${total_value:,.2f} across {product_count} products "
                f"exceeds the bulk order threshold.\n\n"
                f"Recommendation: Review credit terms and fulfillment capacity."
            ),
            priority=HITLPriority.P2_MEDIUM,
            source_agent="agent-04",
            context={
                "order_id": order_id,
                "customer_id": customer_id,
                "customer_name": customer_name,
                "total_value": total_value,
                "product_count": product_count,
            },
            sla_minutes=240,
        )
        self.state.active_hitl_tickets.append(ticket.ticket_id)
        return ticket.to_dict()

    async def get_health(self) -> dict[str, Any]:
        """Public API: Get agent health and metrics."""
        return self.state.to_dict()
