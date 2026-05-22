"""Human-in-the-Loop (HITL) gate — delegates to the shared implementation.

All 9 agents use the same shared HITL gate at ``agents/shared/hitl/``.
This shim ensures that existing imports (``from src.hitl.gate import ...``)
resolve transparently to the shared package.
"""

from __future__ import annotations

import sys
from pathlib import Path

_shared_path = str(Path(__file__).resolve().parents[3] / "shared" / "hitl" / "src")
if _shared_path not in sys.path:
    sys.path.insert(0, _shared_path)

from manufacturing_mas_hitl.gate import (  # noqa: E402
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
