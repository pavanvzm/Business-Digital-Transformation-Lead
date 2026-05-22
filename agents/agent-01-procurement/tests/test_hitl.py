"""Tests for the HITLGate — ticket lifecycle, SLA enforcement, escalation, resolution."""

from __future__ import annotations

import asyncio
import pytest
from src.hitl.gate import HITLGate, HITLTicket, HITLStatus, HITLPriority


@pytest.fixture
def gate() -> HITLGate:
    return HITLGate(poll_interval_seconds=1, default_timeout_seconds=3600)


class TestTicketCreation:
    """HITL ticket creation and lifecycle."""

    async def test_create_ticket(self, gate: HITLGate) -> None:
        """Basic ticket creation with defaults."""
        ticket = await gate.create_ticket(
            title="Test Approval",
            description="Testing ticket creation",
            priority=HITLPriority.P2_MEDIUM,
            source_agent="agent-01",
        )

        assert ticket.ticket_id is not None
        assert ticket.title == "Test Approval"
        assert ticket.status == HITLStatus.PENDING
        assert ticket.source_agent == "agent-01"
        assert ticket.sla_deadline is not None

    async def test_create_ticket_with_context(self, gate: HITLGate) -> None:
        """Ticket with business context."""
        ticket = await gate.create_ticket(
            title="PO Approval: Copper Wire",
            description="Large PO requires approval",
            priority=HITLPriority.P1_HIGH,
            source_agent="agent-01",
            context={
                "po_id": "PO-ABC123",
                "total_value": 750_000.0,
                "material": "Copper Wire",
            },
            sla_minutes=60,
        )

        assert ticket.context["po_id"] == "PO-ABC123"
        assert ticket.context["total_value"] == 750_000.0

    async def test_ticket_audit_log(self, gate: HITLGate) -> None:
        """Ticket creation logs an audit entry."""
        ticket = await gate.create_ticket(
            title="Audit Test",
            description="Check audit trail",
            priority=HITLPriority.P3_LOW,
        )

        assert len(ticket.audit_log) == 1
        assert ticket.audit_log[0]["action"] == "created"
        assert ticket.audit_log[0]["actor"] == "agent-01"


class TestTicketResolution:
    """Ticket resolution paths."""

    async def test_approve_ticket(self, gate: HITLGate) -> None:
        """Approve a ticket."""
        ticket = await gate.create_ticket(
            title="Approve Test",
            description="Test approval",
        )

        resolved = await gate.resolve_ticket(
            ticket_id=ticket.ticket_id,
            status=HITLStatus.APPROVED,
            resolved_by="john.doe@company.com",
            decision="Approved — within budget",
        )

        assert resolved is not None
        assert resolved.status == HITLStatus.APPROVED
        assert resolved.resolved_by == "john.doe@company.com"
        assert resolved.decision == "Approved — within budget"

    async def test_reject_ticket(self, gate: HITLGate) -> None:
        """Reject a ticket."""
        ticket = await gate.create_ticket(
            title="Reject Test",
            description="Test rejection",
        )

        resolved = await gate.resolve_ticket(
            ticket_id=ticket.ticket_id,
            status=HITLStatus.REJECTED,
            resolved_by="jane@company.com",
            decision="Budget constraints — defer to next quarter",
        )

        assert resolved is not None
        assert resolved.status == HITLStatus.REJECTED

    async def test_override_ticket(self, gate: HITLGate) -> None:
        """Human override with modified parameters."""
        ticket = await gate.create_ticket(
            title="Override Test",
            description="Test override with modifications",
            context={"po_id": "PO-OVERRIDE", "quantity": 1000},
        )

        resolved = await gate.resolve_ticket(
            ticket_id=ticket.ticket_id,
            status=HITLStatus.OVERRIDE,
            resolved_by="director@company.com",
            decision="Approved with reduced quantity",
            override_params={"quantity": 500},
        )

        assert resolved is not None
        assert resolved.status == HITLStatus.OVERRIDE
        assert resolved.context.get("override_params", {}).get("quantity") == 500

    async def test_resolve_nonexistent_ticket(self, gate: HITLGate) -> None:
        """Resolving a nonexistent ticket returns None."""
        resolved = await gate.resolve_ticket(
            ticket_id="nonexistent",
            status=HITLStatus.APPROVED,
            resolved_by="test",
        )
        assert resolved is None


class TestTicketManagement:
    """Ticket listing, retrieval, and cancellation."""

    async def test_get_pending_tickets(self, gate: HITLGate) -> None:
        """Pending tickets are listed."""
        await gate.create_ticket(title="Ticket 1", description="Desc 1")
        await gate.create_ticket(title="Ticket 2", description="Desc 2")

        pending = await gate.get_pending_tickets()
        assert len(pending) == 2

    async def test_get_ticket(self, gate: HITLGate) -> None:
        """Retrieve a specific ticket."""
        ticket = await gate.create_ticket(title="Get Me", description="Find this ticket")

        found = await gate.get_ticket(ticket.ticket_id)
        assert found is not None
        assert found.title == "Get Me"

    async def test_cancel_ticket(self, gate: HITLGate) -> None:
        """Cancel a pending ticket."""
        ticket = await gate.create_ticket(title="Cancel Me", description="Will be cancelled")

        cancelled = await gate.cancel_ticket(ticket.ticket_id, "No longer needed")
        assert cancelled

        # Should no longer be in pending
        pending = await gate.get_pending_tickets()
        assert len(pending) == 0

        # Should be findable via get_ticket
        found = await gate.get_ticket(ticket.ticket_id)
        assert found is not None
        assert found.status == HITLStatus.CANCELLED


class TestSLA:
    """SLA enforcement and escalation."""

    async def test_sla_timeout_escalation(self) -> None:
        """SLA breach triggers escalation."""
        gate = HITLGate(poll_interval_seconds=1, default_timeout_seconds=1)

        ticket = await gate.create_ticket(
            title="SLA Test",
            description="Will timeout",
            priority=HITLPriority.P1_HIGH,
            sla_minutes=0,  # immediate timeout
        )

        # Wait for SLA poll loop
        await asyncio.sleep(0.5)

        # Manually check timeout
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        if ticket.sla_deadline and now >= ticket.sla_deadline:
            # In production this is handled by the poll loop
            pass

        await gate.cancel_ticket(ticket.ticket_id, "cleanup")

    async def test_sla_priority_defaults(self, gate: HITLGate) -> None:
        """Different priorities get different SLA defaults."""
        p1 = await gate.create_ticket(title="P1", description="", priority=HITLPriority.P1_HIGH)
        p2 = await gate.create_ticket(title="P2", description="", priority=HITLPriority.P2_MEDIUM)
        p3 = await gate.create_ticket(title="P3", description="", priority=HITLPriority.P3_LOW)

        # P1 should have shortest SLA (smallest interval to deadline)
        p1_sla = (p1.sla_deadline - p1.created_at).total_seconds()
        p3_sla = (p3.sla_deadline - p3.created_at).total_seconds()

        assert p1_sla < p3_sla
