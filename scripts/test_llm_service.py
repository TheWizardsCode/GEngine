
import httpx
import json
import pytest

import sys

pytestmark = pytest.mark.asyncio

@pytest.mark.asyncio
async def test_llm_service():
    url = "http://localhost:8001"
    print(f"Testing LLM Service at {url}...")
    async with httpx.AsyncClient(base_url=url, timeout=30.0) as client:
        # 1. Health Check
        try:
            response = await client.get("/healthz")
            response.raise_for_status()
            print("✅ Health Check Passed:", response.json())
        except Exception as e:
            print(f"❌ Health Check Failed: {e}")
            return

        # 2. Parse Intent
        print("\nTesting /parse_intent...")
        payload = {
            "user_input": "inspect the industrial district",
            "context": {"current_tick": 10}
        }
        try:
            response = await client.post("/parse_intent", json=payload)
            response.raise_for_status()
            print("✅ Parse Intent Passed:")
            print(json.dumps(response.json(), indent=2))
        except Exception as e:
            print(f"❌ Parse Intent Failed: {e}")

        # 3. Narrate
        print("\nTesting /narrate...")
        payload = {
            "events": [
                {"type": "pollution_increase", "district": "industrial-tier", "amount": 5},
                {"type": "agent_action", "agent": "Aria", "action": "investigate"}
            ],
            "context": {"current_tick": 10}
        }
        try:
            response = await client.post("/narrate", json=payload)
            response.raise_for_status()
            print("✅ Narrate Passed:")
            print(json.dumps(response.json(), indent=2))
        except Exception as e:
            print(f"❌ Narrate Failed: {e}")
