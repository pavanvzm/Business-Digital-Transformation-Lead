"""Tests for the HITL gate module."""

from __future__ import annotations

import pytest

from src.hitl.gate import HITLDecision, HITLGate, HITLPriority, HITLStatus, HITLTicket


class TestHITLTicket:
    """Test individual HITL ticket lifecycle."""

    def test_create_ticket(self) -> None:
        """Ticket creation sets required fields."""
        ticket = HITLTicket(
            title="OEE below threshold",
            description="Line-A OEE dropped to 65%",
            priority=HITLPriority.P1_HIGH,
            source_agent="agent-02",
            context={"production_line": "Line-A", "oee": 65.0},
            sla_minutes=60,
        )

        assert ticket.ticket_id.startswith("H-")
        assert ticket.priority == HITLPriority.P1_HIGH
        assert ticket.status == HITLStatus.PENDING
        assert ticket.sla_minutes == 60
        assert len(ticket.audit_log) == 1

    def test_default_sla_by_priority(self) -> None:
        """SLA is set based on priority when not explicitly provided."""
        ticket = HITLTicket(
            title="Test",
            description="Test ticket",
            priority=HITLPriority.P0_CRITICAL,
            source_agent="agent-02",
        )
        assert ticket.sla_minutes == 15  # P0 = 15 min default

    def test_approve_ticket(self) -> None:
        """Approving a ticket updates status and records resolver."""
        ticket = HITLTicket(
            title="Test",
            description="Test ticket",
            priority=HITLPriority.P2_MEDIUM,
            source_agent="agent-02",
        )
        ticket.approve(by="production_manager", reason="Approved — safe to proceed")

        assert ticket.status == HITLStatus.APPROVED
        assert ticket.resolved_by == "production_manager"
        assert ticket.resolved_at is not None
        assert len(ticket.audit_log) == 2

    def test_reject_ticket(self) -> None:
        """Rejecting a ticket records the rejection reason."""
        ticket = HITLTicket(
            title="Test",
            description="Test ticket",
            priority=HITLPriority.P2_MEDIUM,
            source_agent="agent-02",
        )
        ticket.reject(by="qa_director", reason="Quality check failed — do not proceed")

        assert ticket.status == HITLStatus.REJECTED
        assert ticket.resolved_by == "qa_director"
        assert ticket.decision == "Quality check failed — do not proceed"

    def test_override_ticket(self) -> None:
        """Overriding a ticket sets override params."""
        ticket = HITLTicket(
            title="Test",
            description="Test ticket",
            priority=HITLPriority.P1_HIGH,
            source_agent="agent-02",
        )
        ticket.override(
            by="operations_manager",
            params={"speed": 90, "temperature": 195},
            reason="Manual adjustment needed",
        )

        assert ticket.status == HITLStatus.APPROVED
        assert ticket.context.get("override_params") == {"speed": 90, "temperature": 195}
        assert "Manual adjustment" in ticket.decision or "Override" in ticket.decision

    def test_escalate_ticket(self) -> None:
        """Escalating routes to higher authority."""
        ticket = HITLTicket(
            title="Test",
            description="Test ticket",
            priority=HITLPriority.P1_HIGH,
            source_agent="agent-02",
            escalation_path=["production_manager", "coo", "ceo"],
        )
        ticket.escalate(escalated_to="coo", by="production_manager")

        assert ticket.status == HITLStatus.ESCALATED
        assert len(ticket.escalation_history) == 1
        assert ticket.escalation_history[0]["to"] == "coo"

    def test_to_dict_serialization(self) -> None:
        """Ticket serialization includes all fields."""
        ticket = HITLTicket(
            title="Test OEE Alert",
            description="OEE dropped below 70%",
            priority=HITLPriority.P1_HIGH,
            source_agent="agent-02",
            context={"oee": 65.0},
        )
        d = ticket.to_dict()

        assert d["title"] == "Test OEE Alert"
        assert d["priority"] == "P1-High"
        assert d["status"] == "pending"
        assert d["source_agent"] == "agent-02"
        assert "ticket_id" in d
        assert "created_at" in d
        assert "sla_deadline" in d
        assert "audit_log" in d
        assert d["context"]["oee"] == 65.0


class TestHITLGate:
    """Test HITL gate orchestration."""

    @pytest.mark.asyncio
    async def test_create_and_resolve_ticket(self) -> None:
        """Full lifecycle: create, resolve with approval."""
        gate = HITLGate()

        ticket = await gate.create_ticket(
            title="OEE Critical Drop",
            description="Line-A OEE at 65%",
            priority=HITLPriority.P1_HIGH,
            source_agent="agent-02",
            sla_minutes=60,
        )

        result = await gate.resolve_ticket(
            ticket_id=ticket.ticket_id,
            decision=HITLDecision.APPROVE,
            resolved_by="production_manager",
            reason="Approved",
        )

        assert result["status"] == "ok"
        assert result["ticket"]["status"] == "approved"

    @pytest.mark.asyncio
    async def test_resolve_nonexistent_ticket(self) -> None:
        """Resolving a non-existent ticket returns error."""
        gate = HITLGate()
        result = await gate.resolve_ticket(
            ticket_id="NONEXISTENT",
            decision=HITLDecision.APPROVE,
            resolved_by="test",
        )

        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_get_ticket(self) -> None:
        """Getting a ticket by ID."""
        gate = HITLGate()
        ticket = await gate.create_ticket(
            title="Test",
            description="Test",
            priority=HITLPriority.P2_MEDIUM,
            source_agent="agent-02",
        )

        retrieved = await gate.get_ticket(ticket.ticket_id)
        assert retrieved is not None
        assert retrieved.ticket_id == ticket.ticket_id

    @pytest.mark.asyncio
    async def test_poll_loop_sla_breach(self) -> None:
        """SLA breach triggers escalation and timeout."""
        import asyncio

        gate = HITLGate(poll_interval_seconds=0.05)  # fast poll for test
        resolved_tickets: list[str] = []

        async def callback(ticket: HITLTicket) -> None:
            resolved_tickets.append(ticket.ticket_id)

        ticket = await gate.create_ticket(
            title="Test SLA",
            description="SLA test",
            priority=HITLPriority.P1_HIGH,
            source_agent="agent-02",
            sla_minutes=0,  # immediately expired
        )

        # Run poll loop briefly
        poll_task = asyncio.create_task(gate.poll_pending_decisions(callback))
        await asyncio.sleep(0.3)
        poll_task.cancel()

        # Check that the ticket was escalated or timed out
        updated = await gate.get_ticket(ticket.ticket_id)
        assert updated is not None
        assert updated.status in (HITLStatus.ESCALATED, HITLStatus.TIMEOUT)
