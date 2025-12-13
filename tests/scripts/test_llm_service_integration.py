
import pytest
import httpx
import os
from gengine.echoes.gateway.llm_client import LLMClient

pytestmark = pytest.mark.asyncio

@pytest.mark.integration
@pytest.mark.asyncio
async def test_llm_service_windows_integration():
    """
    Integration test to verify communication with the LLM service running on the Windows side.
    Only runs when the 'integration' marker is set.
    """
    # Use LLMClient to resolve the URL automatically
    client_wrapper = LLMClient()
    llm_url = client_wrapper.base_url
    
    async with httpx.AsyncClient(base_url=llm_url, timeout=30.0) as client:
        # Health Check
        response = await client.get("/healthz")
        response.raise_for_status()
        assert response.json().get("status") == "ok"

        # Parse Intent
        payload = {
            "user_input": "inspect the industrial district",
            "context": {"current_tick": 10}
        }
        response = await client.post("/parse_intent", json=payload)
        response.raise_for_status()
        data = response.json()
        # Check for either 'intent' (single) or 'intents' (list)
        assert "intent" in data or "intents" in data

        # Narrate
        payload = {
            "events": [
                {"type": "pollution_increase", "district": "industrial-tier", "amount": 5},
                {"type": "agent_action", "agent": "Aria", "action": "investigate"}
            ],
            "context": {"current_tick": 10}
        }
        response = await client.post("/narrate", json=payload)
        response.raise_for_status()
        data = response.json()
        # Check for either 'narration' or 'narrative'
        assert "narration" in data or "narrative" in data
