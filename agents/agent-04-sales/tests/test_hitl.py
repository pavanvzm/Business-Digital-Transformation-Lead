"""Tests for Agent-04 HITL integration — verifies the shared gate works via the shim."""

from __future__ import annotations

import sys
from pathlib import Path

_shared_path = str(Path(__file__).resolve().parents[2] / ".." / "shared" / "hitl" / "src")
if _shared_path not in sys.path:
    sys.path.insert(0, _shared_path)

import pytest
from src.hitl.gate import HITLGate, HITLPriority, HITLStatus, HITLDecision, HITLTicket


class TestAgent04HITL:
    """Test HITL integration specific to Agent-04 (Sales & Distribution)."""

    @pytest.mark.asyncio
    async def test_pricing_alert_ticket(self) -> None:
        """Pricing change >5% creates a P1 ticket via the shared gate."""
        gate = HITLGate()
        ticket = await gate.create_ticket(
            title="Pricing change alert: Widget-A (+8.5%)",
            description="Price change of +8.5% exceeds 5% threshold.",
            priority=HITLPriority.P1_HIGH,
            source_agent="agent-04",
            context={
                "product_id": "WIDGET-A",
                "current_price": 100.0,
                "proposed_price": 108.5,
                "pct_change": 8.5,
            },
            sla_minutes=60,
        )

        assert ticket.source_agent == "agent-04"
        assert ticket.priority == HITLPriority.P1_HIGH
        assert ticket.status == HITLStatus.PENDING
        assert ticket.ticket_id.startswith("H-")

    @pytest.mark.asyncio
    async def test_bulk_order_ticket(self) -> None:
        """Bulk order creates a P2 ticket."""
        gate = HITLGate()
        ticket = await gate.create_ticket(
            title="Bulk order approval: Acme Corp ($150,000.00)",
            description="Order exceeds $100K threshold.",
            priority=HITLPriority.P2_MEDIUM,
            source_agent="agent-04",
            context={"order_id": "ORD-123", "total_value": 150000.0},
            sla_minutes=240,
        )

        assert ticket.priority == HITLPriority.P2_MEDIUM
        assert ticket.sla_minutes == 240

    @pytest.mark.asyncio
    async def test_resolve_both_interfaces(self) -> None:
        """Both resolve interfaces work with the shared gate."""
        gate = HITLGate()

        # Agent-01 style
        t1 = await gate.create_ticket(
            title="Pricing alert", description="Test",
            source_agent="agent-04",
        )
        r1 = await gate.resolve_ticket(
            ticket_id=t1.ticket_id,
            status=HITLStatus.APPROVED,
            resolved_by="cso@company.com",
            decision="Approved",
        )
        assert r1 is not None
        assert r1.status == HITLStatus.APPROVED

        # Agent-02 style
        t2 = await gate.create_ticket(
            title="Allocation alert", description="Test",
            source_agent="agent-04",
        )
        r2 = await gate.resolve_ticket(
            ticket_id=t2.ticket_id,
            hitl_decision=HITLDecision.ESCALATE,
            resolved_by="sales_manager",
            reason="coo",
        )
        assert r2["status"] == "ok"
        assert r2["ticket"]["status"] == "escalated"

    @pytest.mark.asyncio
    async def test_request_info_action(self) -> None:
        """Request Info pauses SLA and logs the request."""
        gate = HITLGate()
        ticket = await gate.create_ticket(
            title="Pricing review", description="Request additional context",
            source_agent="agent-04",
        )

        result = await gate.resolve_ticket(
            ticket_id=ticket.ticket_id,
            hitl_decision=HITLDecision.REQUEST_INFO,
            resolved_by="cso",
            reason="Need competitor pricing data",
        )
        assert result["info_requested"] is True
        assert len(ticket.audit_log) == 2

    @pytest.mark.asyncio
    async def test_ticket_serialization(self) -> None:
        """to_dict() produces all expected fields."""
        gate = HITLGate()
        ticket = await gate.create_ticket(
            title="Test ticket", description="Testing serialization",
            source_agent="agent-04",
            context={"test": True},
        )
        d = ticket.to_dict()

        assert d["ticket_id"].startswith("H-")
        assert d["source_agent"] == "agent-04"
        assert d["status"] == "pending"
        assert d["context"] == {"test": True}
        assert "audit_log" in d
        assert "created_at" in d
        assert "sla_deadline" in d
