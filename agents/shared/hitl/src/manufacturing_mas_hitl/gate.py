"""Unified Human-in-the-Loop (HITL) Gate — shared across all 9 MAS agents.

Combines the best of the Agent-01 and Agent-02 implementations:

- HITLStatus: PENDING, APPROVED, REJECTED, OVERRIDE, ESCALATED, TIMEOUT, CANCELLED
- HITLPriority: P0-Critical (15min), P1-High (60min), P2-Medium (240min), P3-Low (1440min)
- HITLDecision: approve, reject, modify, defer, escalate, request_info
- Ticket lifecycle: created -> pending -> (approved|rejected|override|escalated|timeout|cancelled) -> closed
- SLA enforcement with automatic escalation on timeout
- Deduplication with configurable window and threshold
- Full immutable audit trail per ticket
- resolve_ticket() supports both status-based (Agent-01 compat) and decision-based (Agent-02 compat) interfaces
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Coroutine
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


# ─── Enums ───────────────────────────────────────────────────────────────────


class HITLStatus(str, Enum):
    """Ticket lifecycle statuses — covers all states from creation through closure."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    OVERRIDE = "override"  # Human approves with modifications
    ESCALATED = "escalated"
    TIMEOUT = "timeout"    # SLA expired without response
    CANCELLED = "cancelled"


class HITLPriority(str, Enum):
    """Priority levels with corresponding default SLA targets.

    P0-Critical  →  15 minutes  (safety, cybersecurity, circuit breaker)
    P1-High      →  60 minutes  (OEE drop, price spikes, quality critical)
    P2-Medium    → 240 minutes  (PO approvals, schedule variance)
    P3-Low       → 1440 minutes (model deployments, info requests)
    """

    P0_CRITICAL = "P0-Critical"
    P1_HIGH = "P1-High"
    P2_MEDIUM = "P2-Medium"
    P3_LOW = "P3-Low"


class HITLDecision(str, Enum):
    """Human decision types available for resolving a ticket."""

    APPROVE = "approve"
    REJECT = "reject"
    MODIFY = "modify"
    DEFER = "defer"
    ESCALATE = "escalate"
    REQUEST_INFO = "request_info"


# ─── Default SLA Map ─────────────────────────────────────────────────────────

_DEFAULT_SLA_MINUTES: dict[HITLPriority, int] = {
    HITLPriority.P0_CRITICAL: 15,
    HITLPriority.P1_HIGH: 60,
    HITLPriority.P2_MEDIUM: 240,
    HITLPriority.P3_LOW: 1440,
}

_DEFAULT_ESCALATION = {
    HITLPriority.P0_CRITICAL: ["shift_manager", "coo", "cto", "ceo"],
    HITLPriority.P1_HIGH: ["operations_manager", "director", "vp"],
    HITLPriority.P2_MEDIUM: ["supervisor", "manager"],
    HITLPriority.P3_LOW: ["team_lead"],
}


# ─── Ticket Class ────────────────────────────────────────────────────────────


class HITLTicket:
    """A HITL approval ticket with full lifecycle tracking and immutable audit trail.

    Compatible with both Agent-01 (status-based) and Agent-02 (decision-based) APIs.
    """

    def __init__(
        self,
        title: str,
        description: str,
        priority: HITLPriority,
        source_agent: str,
        context: dict[str, Any] | None = None,
        sla_minutes: int | None = None,
        escalation_path: list[str] | None = None,
    ) -> None:
        # Ticket ID format: H-YYYYMMDD-NNNNNN (human-readable, traceable)
        self.ticket_id = (
            f"H-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"
        )

        # Map priority to default SLA if not explicitly provided
        if sla_minutes is None:
            sla_minutes = _DEFAULT_SLA_MINUTES.get(priority, 240)

        self.title = title
        self.description = description
        self.priority = priority
        self.source_agent = source_agent
        self.context: dict[str, Any] = context or {}
        self.status: HITLStatus = HITLStatus.PENDING
        self.sla_minutes: int = sla_minutes
        self.created_at: datetime = datetime.now(timezone.utc)
        self.sla_deadline: datetime = self.created_at + timedelta(minutes=sla_minutes)
        self.resolved_at: datetime | None = None
        self.resolved_by: str | None = None
        self.decision: str | None = None

        # Escalation
        self.escalation_path: list[str] = escalation_path or _DEFAULT_ESCALATION.get(priority, [])
        self.escalation_history: list[dict[str, Any]] = []

        # Immutable audit log
        self.audit_log: list[dict[str, Any]] = []
        self._add_audit_entry(
            "system",
            f"Ticket created (priority={priority.value}, SLA={sla_minutes}min, agent={source_agent})",
        )

    # ── Audit ────────────────────────────────────────────────────────────────

    def _add_audit_entry(self, actor: str, detail: str) -> None:
        """Append an entry to the immutable audit trail.

        Args:
            actor: Who performed the action (system, email, role).
            detail: Human-readable description of what happened.
        """
        self.audit_log.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": actor,
            "detail": detail,
        })

    def add_audit_entry(self, action: str, actor: str, detail: str) -> None:
        """Public audit entry (Agent-01 compatible interface).

        Args:
            action: The action performed (e.g., 'approved', 'rejected').
            actor: Who performed the action.
            detail: Human-readable description.
        """
        self._add_audit_entry(actor, f"{action}: {detail}")

    # ── Decision Methods ─────────────────────────────────────────────────────

    def approve(self, by: str, reason: str = "") -> None:
        """Approve this ticket."""
        self.status = HITLStatus.APPROVED
        self.resolved_at = datetime.now(timezone.utc)
        self.resolved_by = by
        self.decision = reason or "Approved"
        self._add_audit_entry(by, f"Approved: {reason}")

    def reject(self, by: str, reason: str) -> None:
        """Reject this ticket with a reason."""
        self.status = HITLStatus.REJECTED
        self.resolved_at = datetime.now(timezone.utc)
        self.resolved_by = by
        self.decision = reason
        self._add_audit_entry(by, f"Rejected: {reason}")

    def override(self, by: str, params: dict[str, Any] | None = None, reason: str = "") -> None:
        """Human override with modified parameters.

        Args:
            by: Who performed the override.
            params: Modified parameter values.
            reason: Rationale for the override.
        """
        self.status = HITLStatus.OVERRIDE
        self.resolved_at = datetime.now(timezone.utc)
        self.resolved_by = by
        self.decision = f"Override: {reason}" if reason else "Overridden"
        if params:
            self.context["override_params"] = params
        self._add_audit_entry(by, f"Override with params {params}: {reason}")

    def escalate(self, escalated_to: str, by: str | None = None) -> None:
        """Escalate this ticket to a higher authority.

        Args:
            escalated_to: Role or individual to escalate to.
            by: Who triggered the escalation (default: system).
        """
        self.status = HITLStatus.ESCALATED
        self.escalation_history.append({
            "from": by or "system",
            "to": escalated_to,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        self._add_audit_entry(by or "system", f"Escalated to {escalated_to}")

    def mark_timeout(self) -> None:
        """Mark ticket as timed out (SLA breached with no response)."""
        self.status = HITLStatus.TIMEOUT
        self.resolved_at = datetime.now(timezone.utc)
        self._add_audit_entry("system", "SLA timeout — no response received within deadline")

    # ── Serialization ───────────────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """Serialize ticket to a JSON-compatible dictionary."""
        return {
            "ticket_id": self.ticket_id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "source_agent": self.source_agent,
            "status": self.status.value,
            "sla_minutes": self.sla_minutes,
            "created_at": self.created_at.isoformat(),
            "sla_deadline": self.sla_deadline.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
            "decision": self.decision,
            "escalation_path": self.escalation_path,
            "escalation_history": self.escalation_history,
            "audit_log": self.audit_log,
            "context": self.context,
        }


# ─── HITL Gate Orchestrator ─────────────────────────────────────────────────


class HITLGate:
    """Manages HITL ticket lifecycle, SLA enforcement, deduplication, and decision polling.

    All 9 agents instantiate this gate, passing their own:
    - poll_interval_seconds: how often to check for SLA breaches
    - default_timeout_seconds: fallback SLA if not specified per-ticket

    The gate connects to an external decision service (REST API, Slack bot, dashboard)
    where human reviewers view and respond to pending tickets.
    """

    def __init__(
        self,
        poll_interval_seconds: int = 10,
        default_timeout_seconds: int = 3600,
        dedup_window_minutes: int = 15,
        dedup_threshold_change_pct: float = 5.0,
    ) -> None:
        self.poll_interval = poll_interval_seconds
        self.default_timeout = default_timeout_seconds
        self.dedup_window_minutes = dedup_window_minutes
        self.dedup_threshold_change_pct = dedup_threshold_change_pct

        self._tickets: dict[str, HITLTicket] = {}
        self._dedup_cache: dict[str, dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    # ── Core Operations ─────────────────────────────────────────────────────

    async def create_ticket(
        self,
        title: str,
        description: str,
        priority: HITLPriority = HITLPriority.P2_MEDIUM,
        source_agent: str = "agent-00",
        context: dict[str, Any] | None = None,
        sla_minutes: int | None = None,
        escalation_path: list[str] | None = None,
        dedup_key: str | None = None,
    ) -> HITLTicket:
        """Create a new HITL ticket with optional deduplication.

        If ``dedup_key`` is provided and a ticket with the same key exists
        within the dedup window, the existing pending ticket is returned
        instead of creating a new one — unless a tracked numeric value has
        changed beyond ``dedup_threshold_change_pct``.

        Args:
            title: Short human-readable title (e.g., "OEE drop on Line-A").
            description: Detailed context including impact and options.
            priority: Priority level (affects default SLA and escalation).
            source_agent: Agent identifier (e.g., "agent-01", "agent-02").
            context: Machine-readable dict for automated processing on resolution.
            sla_minutes: Minutes until SLA deadline. Defaults from priority if None.
            escalation_path: Ordered list of roles to escalate through on timeout.
            dedup_key: Optional deduplication key (e.g., "oee/Line-A").

        Returns:
            The created (or deduplicated) HITLTicket.
        """
        ctx = context or {}

        # Deduplication check
        if dedup_key:
            async with self._lock:
                if await self._is_duplicate(dedup_key, ctx):
                    existing_id = self._dedup_cache[dedup_key]["ticket_id"]
                    existing = self._tickets.get(existing_id)
                    if existing and existing.status == HITLStatus.PENDING:
                        logger.info(
                            "HITL ticket suppressed — duplicate",
                            dedup_key=dedup_key,
                            existing_ticket_id=existing_id,
                        )
                        return existing

        ticket = HITLTicket(
            title=title,
            description=description,
            priority=priority,
            source_agent=source_agent,
            context=ctx,
            sla_minutes=sla_minutes,
            escalation_path=escalation_path,
        )

        async with self._lock:
            self._tickets[ticket.ticket_id] = ticket
            if dedup_key:
                self._dedup_cache[dedup_key] = {
                    "ticket_id": ticket.ticket_id,
                    "context": ctx,
                    "created_at": datetime.now(timezone.utc),
                }

        logger.info(
            "HITL ticket created",
            ticket_id=ticket.ticket_id,
            priority=priority.value,
            sla_minutes=ticket.sla_minutes,
            source_agent=source_agent,
            dedup=bool(dedup_key),
        )

        return ticket

    async def resolve_ticket(
        self,
        ticket_id: str,
        status: HITLStatus | None = None,
        resolved_by: str | None = None,
        decision: str | None = None,
        override_params: dict[str, Any] | None = None,
        # Agent-02 compatible interface
        hitl_decision: HITLDecision | None = None,
        reason: str | None = None,
    ) -> HITLTicket | dict[str, Any]:
        """Resolve a pending HITL ticket.

        Supports two calling conventions:
        - **Agent-01 style**: ``resolve_ticket(ticket_id, status, resolved_by, decision, override_params)``
        - **Agent-02 style**: ``resolve_ticket(ticket_id, hitl_decision, resolved_by, reason, override_params)``

        When ``hitl_decision`` is provided (Agent-02 style), the method returns
        a ``dict`` with ``{"status": "ok"|"error", "ticket": ...}``.
        Otherwise (Agent-01 style), it returns the resolved ``HITLTicket`` or ``None``.

        Args:
            ticket_id: The ticket to resolve.
            status: Resolution status (Agent-01 style).
            resolved_by: Identifier of the human resolver.
            decision: Free-text rationale (Agent-01 style).
            override_params: Modified parameters if status is OVERRIDE.
            hitl_decision: Decision enum (Agent-02 style).
            reason: Rationale for the decision (Agent-02 style).

        Returns:
            Resolved HITLTicket (Agent-01 compat) or dict (Agent-02 compat).
        """
        ticket = self._tickets.get(ticket_id)
        if ticket is None:
            logger.warning("HITL ticket not found", ticket_id=ticket_id)
            if hitl_decision is not None:
                return {"status": "error", "message": f"Ticket {ticket_id} not found"}
            return None

        if ticket.status != HITLStatus.PENDING:
            msg = f"Ticket {ticket_id} is not pending (status: {ticket.status.value})"
            logger.warning(msg)
            if hitl_decision is not None:
                return {"status": "error", "message": msg}
            # Return the ticket as-is for Agent-01 compat; caller should check status
            return ticket

        # Agent-02 style (decision-based)
        if hitl_decision is not None:
            resolved_by_str = resolved_by or "unknown"
            reason_str = reason or ""

            if hitl_decision == HITLDecision.APPROVE:
                ticket.approve(by=resolved_by_str, reason=reason_str)
            elif hitl_decision == HITLDecision.REJECT:
                ticket.reject(by=resolved_by_str, reason=reason_str or "No reason provided")
            elif hitl_decision == HITLDecision.MODIFY:
                ticket.override(by=resolved_by_str, params=override_params or {}, reason=reason_str)
            elif hitl_decision == HITLDecision.ESCALATE:
                ticket.escalate(escalated_to=reason_str, by=resolved_by_str)
            elif hitl_decision == HITLDecision.DEFER:
                ticket._add_audit_entry(resolved_by_str, f"Deferred: {reason_str}")
                # Defer keeps the ticket pending but extends SLA by 1 hour
                ticket.sla_deadline = datetime.now(timezone.utc) + timedelta(hours=1)
                return {"status": "ok", "ticket": ticket.to_dict(), "deferred": True}
            elif hitl_decision == HITLDecision.REQUEST_INFO:
                ticket._add_audit_entry(resolved_by_str, f"Additional info requested: {reason_str}")
                # Request info pauses the SLA timer (extend by 15 min)
                ticket.sla_deadline = datetime.now(timezone.utc) + timedelta(minutes=15)
                return {"status": "ok", "ticket": ticket.to_dict(), "info_requested": True}

            logger.info(
                "HITL ticket resolved",
                ticket_id=ticket_id,
                decision=hitl_decision.value,
                by=resolved_by_str,
            )
            return {"status": "ok", "ticket": ticket.to_dict()}

        # Agent-01 style (status-based)
        if status is None:
            logger.warning("No status or decision provided for ticket resolution")
            return None

        if status == HITLStatus.APPROVED:
            ticket.approve(by=resolved_by or "unknown", reason=decision or "")
        elif status == HITLStatus.REJECTED:
            ticket.reject(by=resolved_by or "unknown", reason=decision or "No reason provided")
        elif status == HITLStatus.OVERRIDE:
            ticket.override(
                by=resolved_by or "unknown",
                params=override_params,
                reason=decision or "Overridden",
            )
        else:
            ticket.status = status
            ticket.resolved_at = datetime.now(timezone.utc)
            ticket.resolved_by = resolved_by
            ticket.decision = decision
            ticket._add_audit_entry(resolved_by or "system", f"{status.value}: {decision or ''}")

        logger.info(
            "HITL ticket resolved",
            ticket_id=ticket_id,
            status=status.value,
            by=resolved_by or "unknown",
        )

        return ticket

    async def poll_pending_decisions(
        self,
        on_resolved: Callable[[HITLTicket], Coroutine[Any, Any, None]],
    ) -> None:
        """Continuously poll pending tickets for SLA breaches and external decisions.

        For each ticket that breaches its SLA deadline:
        1. Escalate to the next role in the escalation path (if path exists).
        2. Reset SLA deadline by the ticket's original SLA duration.
        3. If no escalation path remains, mark as TIMEOUT and invoke callback.

        Args:
            on_resolved: Async callback invoked when a ticket transitions
                         out of PENDING (resolved externally or timed out).
        """
        while True:
            try:
                now = datetime.now(timezone.utc)
                resolved_tickets: list[HITLTicket] = []

                async with self._lock:
                    for ticket_id, ticket in list(self._tickets.items()):
                        if ticket.status != HITLStatus.PENDING:
                            continue

                        # External resolution detected (status changed via resolve_ticket)
                        # Handled by callback on next iteration.

                        # Check SLA breach
                        if now > ticket.sla_deadline:
                            path = ticket.escalation_path
                            if path:
                                next_idx = len(ticket.escalation_history)
                                next_level = path[next_idx % len(path)]
                                ticket.escalate(escalated_to=next_level)
                                ticket.sla_deadline = now + timedelta(minutes=ticket.sla_minutes)
                                logger.warning(
                                    "HITL SLA breached — escalated",
                                    ticket_id=ticket_id,
                                    to=next_level,
                                )
                            else:
                                ticket.mark_timeout()
                                resolved_tickets.append(ticket)
                                logger.warning(
                                    "HITL SLA breached — ticket timed out",
                                    ticket_id=ticket_id,
                                )

                # Invoke callbacks outside lock to prevent deadlock
                for ticket in resolved_tickets:
                    try:
                        await on_resolved(ticket)
                    except Exception:
                        logger.exception(
                            "Error in HITL on_resolved callback",
                            ticket_id=ticket.ticket_id,
                        )

                await asyncio.sleep(self.poll_interval)

            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Error in HITL poll loop")
                await asyncio.sleep(self.poll_interval)

    # ── Query Methods ───────────────────────────────────────────────────────

    async def get_ticket(self, ticket_id: str) -> HITLTicket | None:
        """Get a ticket by ID."""
        return self._tickets.get(ticket_id)

    async def get_pending_tickets(self) -> list[HITLTicket]:
        """Get all currently pending tickets."""
        async with self._lock:
            return [t for t in self._tickets.values() if t.status == HITLStatus.PENDING]

    async def cancel_ticket(self, ticket_id: str, reason: str = "") -> bool:
        """Cancel a pending ticket.

        Args:
            ticket_id: The ticket to cancel.
            reason: Why the ticket was cancelled.

        Returns:
            True if the ticket was found and cancelled, False otherwise.
        """
        ticket = self._tickets.get(ticket_id)
        if ticket is None or ticket.status != HITLStatus.PENDING:
            return False

        ticket.status = HITLStatus.CANCELLED
        ticket.resolved_at = datetime.now(timezone.utc)
        ticket.decision = reason or "Cancelled"
        ticket._add_audit_entry("system", f"Cancelled: {reason}")
        logger.info("HITL ticket cancelled", ticket_id=ticket_id, reason=reason)
        return True

    # ── Internal Helpers ────────────────────────────────────────────────────

    async def _is_duplicate(self, dedup_key: str, context: dict[str, Any]) -> bool:
        """Check if a ticket with the same dedup_key exists within the dedup window."""
        now = datetime.now(timezone.utc)
        existing = self._dedup_cache.get(dedup_key)
        if not existing:
            return False

        # Check if dedup window has expired
        elapsed = (now - existing["created_at"]).total_seconds() / 60.0
        if elapsed > self.dedup_window_minutes:
            return False

        # Check if any tracked numeric value has changed beyond threshold
        for key, new_val in context.items():
            if isinstance(new_val, (int, float)):
                old_val = existing["context"].get(key, new_val)
                if old_val != 0 and abs((new_val - old_val) / old_val * 100) > self.dedup_threshold_change_pct:
                    return False  # Significant change — allow new ticket

        return True
