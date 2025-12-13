import os
import pytest
import asyncio
from gengine.echoes.llm.foundry_local_provider import FoundryLocalProvider
from gengine.echoes.llm.settings import LLMSettings

pytestmark = pytest.mark.windows_only

FOUNDRY_BASE_URL = os.environ.get("ECHOES_LLM_BASE_URL", "http://localhost:5272")
FOUNDRY_MODEL = os.environ.get("ECHOES_LLM_MODEL", "qwen2.5-0.5b-instruct-generic-cpu")

@pytest.mark.integration
@pytest.mark.skipif(
    not FOUNDRY_BASE_URL or not FOUNDRY_MODEL,
    reason="Foundry Local base URL and model must be set via env vars."
)
@pytest.mark.skipif(
    not os.environ.get("FOUNDRY_LOCAL_TESTS"),
    reason="Set FOUNDRY_LOCAL_TESTS=1 to enable real Foundry Local integration tests."
)
@pytest.mark.anyio

@pytest.mark.integration
@pytest.mark.skipif(
    not FOUNDRY_BASE_URL or not FOUNDRY_MODEL,
    reason="Foundry Local base URL and model must be set via env vars."
)
@pytest.mark.skipif(
    not os.environ.get("FOUNDRY_LOCAL_TESTS"),
    reason="Set FOUNDRY_LOCAL_TESTS=1 to enable real Foundry Local integration tests."
)
@pytest.mark.anyio
async def test_foundry_parse_intent_real():
    settings = LLMSettings(
        provider="foundry_local",
        base_url=FOUNDRY_BASE_URL,
        model=FOUNDRY_MODEL,
    )
    provider = FoundryLocalProvider(settings)
    result = await provider.parse_intent("Inspect the industrial tier", {})
    assert result.intents, f"No intents returned: {result.raw_response}"
    assert result.confidence > 0

@pytest.mark.integration
@pytest.mark.skipif(
    not FOUNDRY_BASE_URL or not FOUNDRY_MODEL,
    reason="Foundry Local base URL and model must be set via env vars."
)
@pytest.mark.skipif(
    not os.environ.get("FOUNDRY_LOCAL_TESTS"),
    reason="Set FOUNDRY_LOCAL_TESTS=1 to enable real Foundry Local integration tests."
)
@pytest.mark.anyio
@pytest.mark.integration
@pytest.mark.skipif(
    not FOUNDRY_BASE_URL or not FOUNDRY_MODEL,
    reason="Foundry Local base URL and model must be set via env vars."
)
@pytest.mark.skipif(
    not os.environ.get("FOUNDRY_LOCAL_TESTS"),
    reason="Set FOUNDRY_LOCAL_TESTS=1 to enable real Foundry Local integration tests."
)
@pytest.mark.anyio
async def test_foundry_narrate_real():
    settings = LLMSettings(
        provider="foundry_local",
        base_url=FOUNDRY_BASE_URL,
        model=FOUNDRY_MODEL,
    )
    provider = FoundryLocalProvider(settings)
    events = [{"description": "Agent recruited in Industrial Tier"}]
    result = await provider.narrate(events, {})
    assert result.narrative, f"No narrative returned: {result.raw_response}"


