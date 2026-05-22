"""Shared pytest fixtures for the manufacturing-mas-hitl shared gate tests."""

from __future__ import annotations

import asyncio
import sys
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest

# Ensure the shared package is importable when tests are run from the
# shared/hitl/ directory (without requiring `pip install -e .`)
_src = str(Path(__file__).resolve().parent.parent / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

from manufacturing_mas_hitl.gate import HITLGate, HITLPriority


@pytest.fixture(scope="session")
def event_loop() -> asyncio.AbstractEventLoop:
    """Single event loop for the session (required by pytest-asyncio)."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
async def gate() -> AsyncGenerator[HITLGate, None]:
    """A HITLGate with standard poll settings suitable for non-timing tests."""
    g = HITLGate(poll_interval_seconds=1, default_timeout_seconds=3600)
    yield g
    # No background task to clean up — gate is stateless after fixture scope


@pytest.fixture
def fast_gate() -> HITLGate:
    """A HITLGate with fast polling for SLA/escalation/timing tests.

    Use this when you need the poll loop to trigger within milliseconds.
    """
    return HITLGate(poll_interval_seconds=0.05, default_timeout_seconds=1)


# ── Common P0 test data ──────────────────────────────────────────────────────

P0_TITLE = "Safety interlock triggered: Line-A temperature sensor"
P0_DESCRIPTION = (
    "MES safety system alert on Line-A. "
    "Temp sensor T-004 reading 312.5°C (threshold: 290°C). "
    "Immediate halt required per safety protocol H-013."
)
P0_CONTEXT = {
    "line": "Line-A",
    "sensor_id": "T-004",
    "reading": 312.5,
    "threshold": 290.0,
    "protocol": "H-013",
    "halt_action": "immediate",
}

P0_ESCALATION_PATH = ["on_call_engineer", "shift_manager", "cto", "ciso", "ceo"]
