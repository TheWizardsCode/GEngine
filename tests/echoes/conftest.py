"""Pytest configuration for echoes tests."""

import pytest

from gengine.echoes.gateway.app import GatewaySettings
from gengine.echoes.settings import load_simulation_config


@pytest.fixture
def anyio_backend():
    """Force anyio to use asyncio backend only."""
    return "asyncio"


@pytest.fixture
def sim_config():
    """Load the simulation configuration."""
    return load_simulation_config()


@pytest.fixture
def gateway_settings():
    """Return default gateway settings."""
    return GatewaySettings(service_url="local")
