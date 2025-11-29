"""Pytest configuration for echoes tests."""

import pytest


@pytest.fixture
def anyio_backend():
    """Force anyio to use asyncio backend only."""
    return "asyncio"
