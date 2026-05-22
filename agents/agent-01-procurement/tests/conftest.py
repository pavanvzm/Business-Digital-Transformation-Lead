"""Pytest configuration for Agent-01 Procurement tests.

All tests use asyncio mode with the built-in event loop.
Fixtures are defined in their respective test files.
"""

from __future__ import annotations

import pytest


# Register custom markers
def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
