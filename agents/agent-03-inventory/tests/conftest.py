"""Test fixtures for Agent-03 Inventory."""

from __future__ import annotations

import asyncio
import pytest


@pytest.fixture(scope="session")
def event_loop() -> asyncio.AbstractEventLoop:
    """Create a session-scoped event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
