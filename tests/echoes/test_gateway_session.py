"""Tests for GatewaySession."""

from unittest.mock import Mock

import pytest

from gengine.echoes.cli.shell import CommandResult, ShellBackend
from gengine.echoes.gateway.llm_client import LLMClient
from gengine.echoes.gateway.session import GatewaySession
from gengine.echoes.llm.intents import GameIntent, IntentType


class MockIntent(GameIntent):
    pass

@pytest.fixture
def mock_backend():
    backend = Mock(spec=ShellBackend)
    backend.summary.return_value = {
        "tick": 100,
        "city": "Test City",
        "districts": [],
        "factions": [],
        "agents": [],
        "stability": 0.8,
        "focus": {"district_id": "d1"},
        "focus_digest": {"events": ["event1", "event2"]},
        "focus_history": [],
        "director_history": []
    }
    backend.focus_history.return_value = []
    return backend

@pytest.fixture
def mock_llm_client():
    client = Mock(spec=LLMClient)
    return client

@pytest.fixture
def session(mock_backend, mock_llm_client):
    limits = Mock()
    return GatewaySession(
        backend=mock_backend,
        limits=limits,
        llm_client=mock_llm_client
    )

def test_welcome(session, mock_backend):
    result = session.welcome()
    assert isinstance(result, str)
    mock_backend.summary.assert_called()

def test_execute_standard_command(session, mock_backend):
    # Mock the shell inside session to avoid real execution logic if needed,
    # but GatewaySession creates its own EchoesShell.
    # We can mock the backend's methods that EchoesShell calls.
    
    # For 'summary', EchoesShell calls backend.summary()
    result = session.execute("summary")
    assert isinstance(result, CommandResult)
    mock_backend.summary.assert_called()

def test_execute_natural_language_no_llm(mock_backend):
    limits = Mock()
    session = GatewaySession(backend=mock_backend, limits=limits, llm_client=None)
    result = session.execute_natural_language("do something")
    assert "require LLM service" in result.output

def test_execute_natural_language_success(session, mock_llm_client):
    # Mock intent parsing
    intent = MockIntent(intent=IntentType.INSPECT, session_id="test")
    mock_llm_client.parse_intent.return_value = intent
    
    # Mock intent mapping
    session.intent_mapper = Mock()
    session.intent_mapper.map_intent_to_command.return_value = "summary"
    
    # Mock narration
    mock_llm_client.narrate.return_value = "Narrated output"
    
    # Mock shell execution (we can't easily mock the internal shell,
    # so we rely on backend mocks)
    # "summary" command will call backend.summary()
    
    result = session.execute_natural_language("check status")
    
    assert "Narrated output" in result.output
    mock_llm_client.parse_intent.assert_called()
    session.intent_mapper.map_intent_to_command.assert_called_with(intent)
    mock_llm_client.narrate.assert_called()

def test_execute_natural_language_parse_fail_fallback(session, mock_llm_client):
    mock_llm_client.parse_intent.return_value = None
    
    # "status" should fallback to "summary"
    result = session.execute_natural_language(
        "status"
    )
    
    # Should execute summary
    assert result.output  # Summary output
    assert session.conversation_history[-1]["result"] == "fallback"

def test_execute_natural_language_parse_fail_no_fallback(session, mock_llm_client):
    mock_llm_client.parse_intent.return_value = None
    
    result = session.execute_natural_language("gibberish")
    
    assert "couldn't understand" in result.output
    assert session.conversation_history[-1]["result"] == "fallback"

def test_execute_natural_language_map_fail(session, mock_llm_client):
    intent = MockIntent(intent=IntentType.INSPECT, session_id="test")
    mock_llm_client.parse_intent.return_value = intent
    
    session.intent_mapper = Mock()
    session.intent_mapper.map_intent_to_command.side_effect = ValueError(
        "Mapping error"
    )
    
    result = session.execute_natural_language("do something")
    
    assert "Intent mapping failed" in result.output
    assert session.conversation_history[-1]["result"] == "error"

def test_close(session, mock_backend, mock_llm_client):
    session.close()
    mock_backend.close.assert_called_once()
    mock_llm_client.close.assert_called_once()

def test_build_intent_context(session):
    summary = {
        "tick": 123,
        "focus": {"district_id": "d1"},
        "focus_digest": {"events": ["e1", "e2", "e3", "e4"]}
    }
    context = session._build_intent_context(summary)
    assert context["tick"] == 123
    assert context["district"] == "d1"
    assert len(context["recent_events"]) == 3
    assert context["recent_events"] == ["e1", "e2", "e3"]

def test_fallback_command(session):
    assert session._fallback_command("show summary") == "summary"
    assert session._fallback_command("show map") == "map"
    assert session._fallback_command("next turn") == "next"
    assert session._fallback_command("history") == "history"
    assert session._fallback_command("director") == "director"
    assert session._fallback_command("unknown") is None

def test_try_narrate_no_events(session, mock_llm_client):
    context = {}
    output = "\n  \n" # Empty output
    assert session._try_narrate(output, context) is None
    mock_llm_client.narrate.assert_not_called()

def test_log_focus(session, mock_backend):
    # This method is called internally, but we can test it via execute
    # execute("summary") calls _log_focus
    session.execute("summary")
    # We can't easily assert logging happened without capturing logs, 
    # but we can ensure it doesn't crash.
