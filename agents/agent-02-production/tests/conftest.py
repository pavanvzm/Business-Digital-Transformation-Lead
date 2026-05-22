"""Shared pytest fixtures for Agent-02 tests."""

from __future__ import annotations

import asyncio

import pytest


@pytest.fixture(scope="session")
def event_loop() -> asyncio.AbstractEventLoop:
    """Create a single event loop for the test session.

    Required for async tests using pytest-asyncio.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
def sample_machine_ids() -> list[str]:
    """Sample machine IDs for testing."""
    return ["M-001", "M-002", "M-003"]


@pytest.fixture
def sample_production_lines() -> list[str]:
    """Sample production lines for testing."""
    return ["Line-A", "Line-B", "Line-C"]


@pytest.fixture
def line_dependency_graph() -> dict[str, list[str]]:
    """Sample production line dependency graph."""
    return {
        "Line-A": ["Line-B"],
        "Line-B": ["Line-C"],
        "Line-C": [],
    }
