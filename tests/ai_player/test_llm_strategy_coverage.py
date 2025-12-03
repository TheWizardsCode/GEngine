"""Additional tests for LLM strategy coverage."""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch
from gengine.ai_player.llm_strategy import (
    LLMDecisionLayer,
    LLMStrategyConfig,
    LLMDecisionRequest,
    evaluate_complexity,
    create_llm_decision_layer
)
from gengine.echoes.llm.providers import LLMProvider
from gengine.echoes.llm.intents import IntentType

@pytest.fixture
def mock_provider():
    provider = Mock(spec=LLMProvider)
    provider.parse_intent = AsyncMock()
    return provider

@pytest.fixture
def config():
    return LLMStrategyConfig(
        llm_call_budget=5,
        llm_timeout_seconds=0.1,
        fallback_on_error=True
    )

@pytest.fixture
def layer(mock_provider, config):
    return LLMDecisionLayer(provider=mock_provider, config=config)

@pytest.fixture
def request_data():
    return LLMDecisionRequest(
        state={"stability": 0.8},
        tick=100,
        session_id="test_session"
    )

def test_budget_exhausted(layer, request_data):
    layer._budget.calls_used = 5
    assert layer.is_budget_exhausted()
    assert layer.request_decision(request_data) is None

def test_evaluate_complexity_critical_stability():
    config = LLMStrategyConfig(complexity_threshold_stability=0.5)
    state = {"stability": 0.4}
    is_complex, factors = evaluate_complexity(state, config)
    assert is_complex
    assert "critical_stability" in factors

def test_evaluate_complexity_stressed_factions():
    config = LLMStrategyConfig(
        complexity_threshold_factions=2,
        complexity_threshold_legitimacy=0.4
    )
    state = {
        "faction_legitimacy": {"f1": 0.3, "f2": 0.3, "f3": 0.8}
    }
    is_complex, factors = evaluate_complexity(state, config)
    assert is_complex
    assert "multiple_stressed_factions" in factors

def test_evaluate_complexity_story_seeds():
    config = LLMStrategyConfig(complexity_threshold_seeds=2)
    state = {
        "story_seeds": [{"seed_id": "s1"}, {"seed_id": "s2"}]
    }
    is_complex, factors = evaluate_complexity(state, config)
    assert is_complex
    assert "multiple_story_seeds" in factors

def test_evaluate_complexity_legitimacy_spread():
    config = LLMStrategyConfig(complexity_threshold_legitimacy_spread=0.3)
    state = {
        "faction_legitimacy": {"f1": 0.9, "f2": 0.4}
    }
    is_complex, factors = evaluate_complexity(state, config)
    assert is_complex
    assert "faction_legitimacy_spread" in factors

def test_build_command_critical_stability(layer, request_data):
    request_data.state["stability"] = 0.3
    layer._config.complexity_threshold_stability = 0.5
    command = layer._build_command_from_context(request_data)
    assert "stability is critical" in command

def test_build_command_stressed_factions(layer, request_data):
    request_data.complexity_factors = ["multiple_stressed_factions"]
    request_data.state["faction_legitimacy"] = {"f1": 0.2}
    command = layer._build_command_from_context(request_data)
    assert "low legitimacy" in command

def test_build_command_story_seeds(layer, request_data):
    request_data.complexity_factors = ["multiple_story_seeds"]
    request_data.state["story_seeds"] = [{"seed_id": "s1"}]
    command = layer._build_command_from_context(request_data)
    assert "Multiple crises" in command

def test_parse_intent_inspect(layer):
    mock_result = Mock()
    mock_result.intents = [{"type": "inspect", "target": "district", "target_id": "d1"}]
    intent = layer._parse_intent_from_result(mock_result, "sess")
    assert intent.intent == IntentType.INSPECT
    assert intent.target_id == "d1"

def test_parse_intent_negotiate(layer):
    mock_result = Mock()
    mock_result.intents = [{"type": "negotiate", "targets": ["f1"], "goal": "peace"}]
    intent = layer._parse_intent_from_result(mock_result, "sess")
    assert intent.intent == IntentType.NEGOTIATE
    assert intent.targets == ["f1"]

def test_parse_intent_deploy(layer):
    mock_result = Mock()
    mock_result.intents = [{"type": "deploy", "resource_type": "materials", "amount": 100}]
    intent = layer._parse_intent_from_result(mock_result, "sess")
    assert intent.intent == IntentType.DEPLOY_RESOURCE
    assert intent.amount == 100.0

def test_parse_intent_report(layer):
    mock_result = Mock()
    mock_result.intents = [{"type": "report", "report_type": "summary"}]
    intent = layer._parse_intent_from_result(mock_result, "sess")
    assert intent.intent == IntentType.REQUEST_REPORT

def test_parse_intent_unknown(layer):
    mock_result = Mock()
    mock_result.intents = [{"type": "unknown"}]
    intent = layer._parse_intent_from_result(mock_result, "sess")
    assert intent.intent == IntentType.INSPECT  # Default

def test_parse_intent_error(layer):
    # Simulate error by passing invalid data that causes exception during parsing
    mock_result = Mock()
    # Trigger ValueError in float conversion for deploy intent
    mock_result.intents = [{"type": "deploy", "amount": "invalid"}]
    intent = layer._parse_intent_from_result(mock_result, "sess")
    assert intent is None

def test_call_llm_timeout(layer, request_data):
    async def delayed_response(*args, **kwargs):
        await asyncio.sleep(0.2)
        return Mock()
    
    layer._provider.parse_intent.side_effect = delayed_response
    
    result = asyncio.run(layer._call_llm(request_data))
    assert result is None
    assert layer._budget.fallback_count == 1

def test_call_llm_error_fallback(layer, request_data):
    layer._provider.parse_intent.side_effect = Exception("LLM Error")
    
    result = asyncio.run(layer._call_llm(request_data))
    assert result is None
    assert layer._budget.fallback_count == 1

def test_call_llm_error_no_fallback(layer, request_data):
    layer._config.fallback_on_error = False
    layer._provider.parse_intent.side_effect = Exception("LLM Error")
    
    with pytest.raises(Exception):
        asyncio.run(layer._call_llm(request_data))

def test_create_llm_decision_layer_default():
    layer = create_llm_decision_layer()
    assert isinstance(layer, LLMDecisionLayer)
    assert layer._config.llm_call_budget == 10

def test_request_decision_sync(layer, request_data):
    # Mock successful response
    mock_result = Mock()
    mock_result.intents = [{"type": "inspect"}]
    mock_result.confidence = 0.9
    mock_result.raw_response = "raw"
    
    # We need to mock the async call inside request_decision or the provider
    # Since request_decision calls asyncio.run, we can mock _call_llm if we want,
    # but mocking the provider is better integration test.
    
    # However, asyncio.run won't work if we are already in a loop (which pytest-asyncio might do)
    # But this test is synchronous.
    
    # We need to make sure the provider returns a future-like object or coroutine
    async def success_response(*args, **kwargs):
        return mock_result
    
    layer._provider.parse_intent.side_effect = success_response
    
    response = layer.request_decision(request_data)
    assert response is not None
    assert response.intent.intent == IntentType.INSPECT

