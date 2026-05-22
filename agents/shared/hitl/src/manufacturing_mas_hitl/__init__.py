"""Manufacturing MAS — Shared Human-in-the-Loop (HITL) Gate.

All 9 agents use this shared gate for:
- HITL ticket creation with SLA and priority
- Human decision resolution (approve/reject/modify/escalate/defer/request-info)
- SLA enforcement and escalation on timeout
- Deduplication of pending tickets for the same context
- Full immutable audit trail
"""

from __future__ import annotations

from .gate import (
    HITLDecision,
    HITLGate,
    HITLPriority,
    HITLStatus,
    HITLTicket,
)

__all__ = [
    "HITLDecision",
    "HITLGate",
    "HITLPriority",
    "HITLStatus",
    "HITLTicket",
]
