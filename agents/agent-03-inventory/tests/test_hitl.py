"""Tests for Agent-03 HITL integration — verifies the shared gate works via the shim."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the shared package is on the path (same logic as the shim)
_shared_path = str(Path(__file__).resolve().parents[2] / ".." / "shared" / "hitl" / "src")
if _shared_path not in sys.path:
    sys.path.insert(0, _shared_path)

import pytest
from src.hitl.gate import HITLGate, HITLPriority, HITLStatus, HITLDecision, HITLTicket


class TestAgent03HITL:
    """Test HITL integration specific to Agent-03 (Inventory)."""

    @pytest.mark.asyncio
    async def test_stockout_alert_ticket(self) -> None:
        """Stock-out alert creates a P1 ticket via the shared gate."""
        gate = HITLGate()
        ticket = await gate.create_ticket(
            title="Stock-out risk: Steel Coil (85% probability)",
            description="SKU STEEL-001 has 85% stock-out probability.",
            priority=HITLPriority.P1_HIGH,
            source_agent="agent-03",
            context={"sku": "STEEL-001", "stockout_probability": 0.85},
            sla_minutes=60,
        )

        assert ticket.source_agent == "agent-03"
        assert ticket.priority == HITLPriority.P1_HIGH
        assert ticket.status == HITLStatus.PENDING
        assert ticket.ticket_id.startswith("H-")

    @pytest.mark.asyncio
    async def test_dead_stock_alert_ticket(self) -> None:
        """Dead stock alert creates a P2 ticket."""
        gate = HITLGate()
        ticket = await gate.create_ticket(
            title="Dead stock alert: Rubber Gasket (7.2% of inventory value)",
            description="Rubber Gasket has no movement for 95 days.",
            priority=HITLPriority.P2_MEDIUM,
            source_agent="agent-03",
            context={"sku": "RUB-045", "dead_stock_value": 15000.0},
            sla_minutes=240,
        )

        assert ticket.priority == HITLPriority.P2_MEDIUM
        assert ticket.sla_minutes == 240

    @pytest.mark.asyncio
    async def test_resolve_via_status_and_decision(self) -> None:
        """Both resolve interfaces work with the shared gate."""
        gate = HITLGate()

        # Create a ticket
        ticket = await gate.create_ticket(
            title="Space utilization critical",
            description="Zone A at 95%",
            priority=HITLPriority.P2_MEDIUM,
            source_agent="agent-03",
        )

        # Agent-01 style resolve
        result_01 = await gate.resolve_ticket(
            ticket_id=ticket.ticket_id,
            status=HITLStatus.APPROVED,
            resolved_by="warehouse_manager",
            decision="Approved — expanding storage",
        )
        assert result_01 is not None
        assert result_01.status == HITLStatus.APPROVED
        assert result_01.resolved_by == "warehouse_manager"

        # Re-create for Agent-02 style test
        ticket2 = await gate.create_ticket(
            title="Test 2",
            description="Test decision-based resolve",
            source_agent="agent-03",
        )

        result_02 = await gate.resolve_ticket(
            ticket_id=ticket2.ticket_id,
            hitl_decision=HITLDecision.REJECT,
            resolved_by="supply_chain_director",
            reason="Not critical — defer to next review",
        )
        assert isinstance(result_02, dict)
        assert result_02["status"] == "ok"
        assert result_02["ticket"]["status"] == "rejected"

    @pytest.mark.asyncio
    async def test_dedup_suppression(self) -> None:
        """Deduplication suppresses duplicate tickets for the same context."""
        gate = HITLGate(dedup_window_minutes=60)

        ticket1 = await gate.create_ticket(
            title="Stock-out risk: Steel Coil",
            description="Same SKU repeated alert",
            priority=HITLPriority.P1_HIGH,
            source_agent="agent-03",
            context={"sku": "STEEL-001", "stockout_probability": 0.85},
            dedup_key="stockout/STEEL-001",
        )

        ticket2 = await gate.create_ticket(
            title="Stock-out risk: Steel Coil",
            description="Duplicate should be suppressed",
            priority=HITLPriority.P1_HIGH,
            source_agent="agent-03",
            context={"sku": "STEEL-001", "stockout_probability": 0.85},
            dedup_key="stockout/STEEL-001",
        )

        assert ticket1.ticket_id == ticket2.ticket_id

    @pytest.mark.asyncio
    async def test_ticket_audit_trail(self) -> None:
        """Ticket lifecycle entries are recorded."""
        gate = HITLGate()
        ticket = await gate.create_ticket(
            title="Audit test",
            description="Verify audit trail",
            source_agent="agent-03",
        )

        assert len(ticket.audit_log) == 1  # creation entry
        assert ticket.audit_log[0]["actor"] == "system"
        assert "agent-03" in ticket.audit_log[0]["detail"]

    @pytest.mark.asyncio
    async def test_get_pending_and_cancel(self) -> None:
        """Pending list and cancellation work."""
        gate = HITLGate()
        await gate.create_ticket(title="A", description="1", source_agent="agent-03")
        await gate.create_ticket(title="B", description="2", source_agent="agent-03")

        pending = await gate.get_pending_tickets()
        assert len(pending) == 2

        cancelled = await gate.cancel_ticket(pending[0].ticket_id, "Test cleanup")
        assert cancelled

        pending_after = await gate.get_pending_tickets()
        assert len(pending_after) == 1
