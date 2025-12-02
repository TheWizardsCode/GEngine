# LLM Service Usage Guide

## Overview

The LLM service (`echoes-llm-service`) provides natural language processing

for the Echoes of Emergence game.

It converts player text into structured game intents and generates

narrative text from simulation events.

## Quick Start

### 1. Start the Service

```bash
# Default configuration (stub provider, no API key needed)
uv run echoes-llm-service

# Service runs on http://localhost:8001
```

### 2. Test the Health Endpoint

```bash
curl http://localhost:8001/healthz
# {"status": "ok", "provider": "stub"}
```

### 3. Parse Natural Language

```bash
curl -X POST http://localhost:8001/parse_intent \
  -H "Content-Type: application/json" \
  -d '{"text": "stabilize the industrial tier district"}'

# Response:
# {
#   "intent": "stabilize",
#   "confidence": 0.9,
#   "parameters": {
#     "district": "industrial tier"
#   }
# }
```

### 4. Generate Narrative

```bash
curl -X POST http://localhost:8001/narrate \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      "Agent recruited in Industrial Tier",
      "Pollution increased by 15%"
    ],
    "context": {
      "district": "Industrial Tier",
      "tick": 42
    }
  }'

# Response:
# {
#   "narration": "Recent events unfolded in the Industrial Tier...",
#   "tone": "neutral"
# }
```

## Configuration

Configure the service via environment variables:

### Provider Selection

```bash
# Stub provider (default, deterministic keyword matching)
export ECHOES_LLM_PROVIDER=stub

# OpenAI provider (requires API key)
export ECHOES_LLM_PROVIDER=openai
export ECHOES_LLM_API_KEY=sk-...
export ECHOES_LLM_MODEL=gpt-4

# Anthropic provider (requires API key)
export ECHOES_LLM_PROVIDER=anthropic
export ECHOES_LLM_API_KEY=sk-ant-...
export ECHOES_LLM_MODEL=claude-3-opus-20240229
```

### Model Parameters

```bash
# Temperature (0.0-1.0, controls randomness)
export ECHOES_LLM_TEMPERATURE=0.7

# Max tokens in response
export ECHOES_LLM_MAX_TOKENS=500

# Request timeout in seconds
export ECHOES_LLM_TIMEOUT_SECONDS=30
```

## Stub Provider

The stub provider is perfect for testing and development:

- **No API costs**: Works completely offline
- **Deterministic**: Same input always produces same output
- **Fast**: No network latency
- **Keyword-based**: Uses simple pattern matching

### Intent Detection

The stub provider recognizes these keywords:

- `inspect`, `investigate`, `examine` → `inspect` intent
- `stabilize`, `calm`, `pacify` → `stabilize` intent
- `negotiate`, `bargain`, `deal` → `negotiate` intent
- `recruit`, `hire`, `enlist` → `recruit` intent
- Default → `observe` intent

### Narration

The stub provider generates simple narrative templates based on event count and context.

## API Reference

### GET /healthz

Health check endpoint.

**Response:**

```json
{
  "status": "ok",
  "provider": "stub"
}
```

### POST /parse_intent

Convert natural language to structured game intent.

**Request:**

```json
{
  "text": "string" // Natural language command
}
```

**Response:**

```json
{
  "intent": "string",      // Detected intent (inspect, stabilize, etc.)
  "confidence": 0.0-1.0,   // Confidence score
  "parameters": {          // Extracted parameters (optional)
    "district": "string",
    "faction": "string",
    "agent": "string"
  }
}
```

### POST /narrate

Generate story text from simulation events.

**Request:**

```json
{
  "events": ["string"], // List of event descriptions
  "context": {
    // Additional context (optional)
    "district": "string",
    "tick": 42,
    "sentiment": "positive"
  }
}
```

**Response:**

```json
{
  "narration": "string", // Generated story text
  "tone": "string" // Tone/sentiment of narration
}
```

## Python Client Example

```python
import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        # Parse intent
        response = await client.post(
            "http://localhost:8001/parse_intent",
            json={"text": "recruit agents in the perimeter hollow"}
        )
        intent_result = response.json()
        print(f"Intent: {intent_result['intent']}")
        print(f"Confidence: {intent_result['confidence']}")
        print(f"Parameters: {intent_result['parameters']}")

        # Generate narration
        response = await client.post(
            "http://localhost:8001/narrate",
            json={
                "events": [
                    "Faction legitimacy increased",
                    "New agent recruited",
                    "Pollution levels stable"
                ],
                "context": {
                    "district": "Perimeter Hollow",
                    "faction": "Reform Coalition"
                }
            }
        )
        narration_result = response.json()
        print(f"\nNarration: {narration_result['narration']}")
        print(f"Tone: {narration_result['tone']}")

asyncio.run(main())
```

## Integration with Gateway

The LLM service is designed to work with the gateway service (`echoes-gateway-service`)

for natural language command routing.

See the Phase 6 implementation plan for details on M6.4 (Intent routing)

and M6.5 (Gateway-LLM integration).

## Adding New Providers

To add a new LLM provider:

1. Create a new class inheriting from `LLMProvider` in `src/gengine/echoes/llm/providers.py`
2. Implement `async def parse_intent()` and `async def narrate()` methods
3. Add the provider to the factory function `create_provider()`
4. Update `LLMSettings` validation to accept the new provider name
5. Add tests in `tests/echoes/test_llm_providers.py`

Example:

```python
class MyCustomProvider(LLMProvider):
    """Custom LLM provider implementation."""

    def __init__(self, api_key: str, model: str, **kwargs):
        self.api_key = api_key
        self.model = model

    async def parse_intent(self, text: str) -> IntentParseResult:
        # Your implementation here
        pass

    async def narrate(self, events: list[str], context: dict) -> NarrateResult:
        # Your implementation here
        pass
```

## Troubleshooting

### Service won't start

- Check that port 8001 is not already in use
- Verify environment variables are set correctly
- Check logs for configuration errors

### Provider validation errors

- Ensure `ECHOES_LLM_PROVIDER` is one of: stub, openai, anthropic
- For openai/anthropic, ensure `ECHOES_LLM_API_KEY` is set
- For openai/anthropic, ensure `ECHOES_LLM_MODEL` is set

### Connection timeout

- Increase `ECHOES_LLM_TIMEOUT_SECONDS`
- Check network connectivity for remote providers
- Consider using stub provider for development

## Next Steps

- See `docs/simul/emergent_story_game_implementation_plan.md` for M6.4-M6.5 roadmap
- See `README.md` for overall project status
- See `tests/echoes/test_llm_*.py` for usage examples
