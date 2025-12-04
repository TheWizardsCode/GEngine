"""Tests for OpenAIProvider coverage."""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from gengine.echoes.llm.openai_provider import OpenAIProvider
from gengine.echoes.llm.settings import LLMSettings


@pytest.fixture
def settings():
    return LLMSettings(
        provider="openai",
        api_key="test-key",
        model="gpt-4-test"
    )

@pytest.fixture
def provider(settings):
    # We need to mock AsyncOpenAI before it's instantiated in __init__
    # or patch it. Since we are testing the class, we can instantiate it
    # and then replace the client.
    with pytest.MonkeyPatch.context() as m:
        m.setattr("gengine.echoes.llm.openai_provider.AsyncOpenAI", Mock())
        provider = OpenAIProvider(settings)
        provider.client = Mock()
        provider.client.chat = Mock()
        provider.client.chat.completions = Mock()
        provider.client.chat.completions.create = AsyncMock()
        return provider

def test_parse_intent_inspect(provider):
    mock_response = Mock()
    mock_response.model_dump_json.return_value = "{}"
    mock_message = Mock()
    mock_message.function_call.name = "inspect_target"
    mock_message.function_call.arguments = (
        '{"target_type": "district", "target_id": "d1", "focus_areas": ["pollution"]}'
    )
    mock_response.choices = [Mock(message=mock_message)]
    
    provider.client.chat.completions.create.return_value = mock_response
    
    result = asyncio.run(
        provider.parse_intent("check district d1", {"session_id": "test"})
    )
    
    assert len(result.intents) == 1
    intent = result.intents[0]
    assert intent["intent"] == "INSPECT"
    assert intent["target_type"] == "district"
    assert intent["target_id"] == "d1"
    assert intent["focus_areas"] == ["pollution"]

def test_parse_intent_negotiate(provider):
    mock_response = Mock()
    mock_response.model_dump_json.return_value = "{}"
    mock_message = Mock()
    mock_message.function_call.name = "negotiate_with_faction"
    mock_message.function_call.arguments = (
        '{"targets": ["f1"], "goal": "peace"}'
    )
    mock_response.choices = [Mock(message=mock_message)]
    
    provider.client.chat.completions.create.return_value = mock_response
    
    result = asyncio.run(provider.parse_intent("talk to f1", {"session_id": "test"}))
    
    assert len(result.intents) == 1
    intent = result.intents[0]
    assert intent["intent"] == "NEGOTIATE"
    assert intent["targets"] == ["f1"]
    assert intent["goal"] == "peace"

def test_parse_intent_deploy(provider):
    mock_response = Mock()
    mock_response.model_dump_json.return_value = "{}"
    mock_message = Mock()
    mock_message.function_call.name = "deploy_resource"
    mock_message.function_call.arguments = (
        '{"resource_type": "money", "amount": 100, "target_district": "d1"}'
    )
    mock_response.choices = [Mock(message=mock_message)]
    
    provider.client.chat.completions.create.return_value = mock_response
    
    result = asyncio.run(provider.parse_intent("send money", {"session_id": "test"}))
    
    assert len(result.intents) == 1
    intent = result.intents[0]
    assert intent["intent"] == "DEPLOY_RESOURCE"
    assert intent["amount"] == 100

def test_parse_intent_pass_policy(provider):
    mock_response = Mock()
    mock_response.model_dump_json.return_value = "{}"
    mock_message = Mock()
    mock_message.function_call.name = "pass_policy"
    mock_message.function_call.arguments = (
        '{"policy_id": "p1", "duration_ticks": 10}'
    )
    mock_response.choices = [Mock(message=mock_message)]
    
    provider.client.chat.completions.create.return_value = mock_response
    
    result = asyncio.run(provider.parse_intent("pass p1", {"session_id": "test"}))
    
    assert len(result.intents) == 1
    intent = result.intents[0]
    assert intent["intent"] == "PASS_POLICY"
    assert intent["policy_id"] == "p1"

def test_parse_intent_covert_action(provider):
    mock_response = Mock()
    mock_response.model_dump_json.return_value = "{}"
    mock_message = Mock()
    mock_message.function_call.name = "covert_action"
    mock_message.function_call.arguments = (
        '{"action_type": "spy", "target_faction": "f1"}'
    )
    mock_response.choices = [Mock(message=mock_message)]
    
    provider.client.chat.completions.create.return_value = mock_response
    
    result = asyncio.run(provider.parse_intent("spy on f1", {"session_id": "test"}))
    
    assert len(result.intents) == 1
    intent = result.intents[0]
    assert intent["intent"] == "COVERT_ACTION"
    assert intent["action_type"] == "spy"

def test_parse_intent_invoke_agent(provider):
    mock_response = Mock()
    mock_response.model_dump_json.return_value = "{}"
    mock_message = Mock()
    mock_message.function_call.name = "invoke_agent"
    mock_message.function_call.arguments = '{"agent_id": "a1", "action": "move"}'
    mock_response.choices = [Mock(message=mock_message)]
    
    provider.client.chat.completions.create.return_value = mock_response
    
    result = asyncio.run(provider.parse_intent("agent a1 move", {"session_id": "test"}))
    
    assert len(result.intents) == 1
    intent = result.intents[0]
    assert intent["intent"] == "INVOKE_AGENT"
    assert intent["agent_id"] == "a1"

def test_parse_intent_request_report(provider):
    mock_response = Mock()
    mock_response.model_dump_json.return_value = "{}"
    mock_message = Mock()
    mock_message.function_call.name = "request_report"
    mock_message.function_call.arguments = '{"report_type": "full"}'
    mock_response.choices = [Mock(message=mock_message)]
    
    provider.client.chat.completions.create.return_value = mock_response
    
    result = asyncio.run(provider.parse_intent("report", {"session_id": "test"}))
    
    assert len(result.intents) == 1
    intent = result.intents[0]
    assert intent["intent"] == "REQUEST_REPORT"
    assert intent["report_type"] == "full"

def test_parse_intent_unknown_function(provider):
    mock_response = Mock()
    mock_response.model_dump_json.return_value = "{}"
    mock_message = Mock()
    mock_message.function_call.name = "unknown_func"
    mock_message.function_call.arguments = '{}'
    mock_response.choices = [Mock(message=mock_message)]
    
    provider.client.chat.completions.create.return_value = mock_response
    
    result = asyncio.run(provider.parse_intent("unknown", {"session_id": "test"}))
    
    assert len(result.intents) == 0
