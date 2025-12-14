"""Tests for LLM chat CLI and client."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from gengine.echoes.llm.chat_client import LLMChatClient

pytestmark = pytest.mark.anyio


def _import_chat_script():
    """Import the echoes_llm_chat script module."""
    script_path = Path(__file__).parent.parent.parent / "scripts" / "echoes_llm_chat.py"
    spec = importlib.util.spec_from_file_location("echoes_llm_chat", script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load script from {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestLLMChatClient:
    """Tests for LLMChatClient."""

    async def test_context_manager(self) -> None:
        """Test that client can be used as async context manager."""
        async with LLMChatClient("http://localhost:8001") as client:
            assert client._client is not None
        # Client should be closed after exiting context
        # (no direct way to check httpx.AsyncClient.is_closed,
        # but we can verify it doesn't raise)

    async def test_parse_intent_request_format(self) -> None:
        """Test that parse_intent formats requests correctly."""
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/parse_intent"
            payload = json.loads(request.content)
            assert payload["user_input"] == "test input"
            assert payload["context"] == {
                "history": [{"role": "user", "content": "hi"}]
            }
            
            return httpx.Response(
                200,
                json={
                    "intents": [{"type": "test"}],
                    "raw_response": "test",
                    "confidence": 0.9,
                },
            )
        
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(
            base_url="http://localhost:8001",
            transport=transport,
        ) as mock_client:
            client = LLMChatClient("http://localhost:8001")
            client._client = mock_client
            
            result = await client.parse_intent(
                "test input",
                {"history": [{"role": "user", "content": "hi"}]},
            )
            
            assert result["intents"] == [{"type": "test"}]
            assert result["confidence"] == 0.9

    async def test_narrate_request_format(self) -> None:
        """Test that narrate formats requests correctly."""
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/narrate"
            payload = json.loads(request.content)
            assert payload["events"] == [{"type": "test_event"}]
            assert payload["context"] == {"tick": 10}
            
            return httpx.Response(
                200,
                json={
                    "narrative": "Test narrative",
                    "raw_response": "test",
                    "metadata": {"input_tokens": 10, "output_tokens": 20},
                },
            )
        
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(
            base_url="http://localhost:8001",
            transport=transport,
        ) as mock_client:
            client = LLMChatClient("http://localhost:8001")
            client._client = mock_client
            
            result = await client.narrate(
                [{"type": "test_event"}],
                {"tick": 10},
            )
            
            assert result["narrative"] == "Test narrative"
            assert result["metadata"]["input_tokens"] == 10

    async def test_health_check(self) -> None:
        """Test health check endpoint."""
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == "/healthz"
            return httpx.Response(
                200,
                json={
                    "status": "ok",
                    "provider": "stub",
                    "model": "N/A",
                },
            )
        
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(
            base_url="http://localhost:8001",
            transport=transport,
        ) as mock_client:
            client = LLMChatClient("http://localhost:8001")
            client._client = mock_client
            
            result = await client.health_check()
            assert result["status"] == "ok"
            assert result["provider"] == "stub"

    async def test_http_error_handling(self) -> None:
        """Test that HTTP errors are raised properly."""
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                500,
                json={"detail": "Internal server error"},
            )
        
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(
            base_url="http://localhost:8001",
            transport=transport,
        ) as mock_client:
            client = LLMChatClient("http://localhost:8001")
            client._client = mock_client
            
            with pytest.raises(httpx.HTTPStatusError):
                await client.parse_intent("test")

    async def test_client_not_initialized(self) -> None:
        """Test that calling methods without context manager raises error."""
        client = LLMChatClient("http://localhost:8001")
        
        with pytest.raises(RuntimeError, match="Client not initialized"):
            await client.parse_intent("test")
        
        with pytest.raises(RuntimeError, match="Client not initialized"):
            await client.narrate([{"type": "test"}])
        
        with pytest.raises(RuntimeError, match="Client not initialized"):
            await client.health_check()

    async def test_custom_headers(self) -> None:
        """Test that custom headers are passed through."""
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.headers.get("X-API-Key") == "test-key"
            return httpx.Response(200, json={"status": "ok"})
        
        transport = httpx.MockTransport(handler)
        client = LLMChatClient(
            "http://localhost:8001",
            headers={"X-API-Key": "test-key"},
        )
        
        async with httpx.AsyncClient(
            base_url="http://localhost:8001",
            transport=transport,
            headers={"X-API-Key": "test-key"},
        ) as mock_client:
            client._client = mock_client
            result = await client.health_check()
            assert result["status"] == "ok"


class TestAutoDetection:
    """Tests for service URL auto-detection."""

    def test_detect_service_url_success(self) -> None:
        """Test successful service detection."""
        chat_module = _import_chat_script()
        detect_service_url = chat_module.detect_service_url
        
        # Mock httpx.get to simulate successful connection
        with patch("httpx.get") as mock_get:
            mock_get.return_value.status_code = 200
            result = detect_service_url()
            assert result is not None
            assert "8001" in result

    def test_detect_service_url_failure(self) -> None:
        """Test when no service is found."""
        chat_module = _import_chat_script()
        detect_service_url = chat_module.detect_service_url
        
        # Mock httpx.get to simulate connection failure
        with patch("httpx.get") as mock_get:
            mock_get.side_effect = httpx.ConnectError("Connection refused")
            result = detect_service_url()
            assert result is None


class TestChatSession:
    """Tests for ChatSession (imported from scripts)."""

    def test_history_management(self) -> None:
        """Test history add and clear operations."""
        chat_module = _import_chat_script()
        ChatSession = chat_module.ChatSession
        
        session = ChatSession("http://localhost:8001", history_limit=2)
        
        # Add entries
        session.add_to_history("user", "hello")
        session.add_to_history("assistant", "hi")
        assert len(session.history) == 2
        
        # Add more entries to trigger limit
        session.add_to_history("user", "message 2")
        session.add_to_history("assistant", "response 2")
        session.add_to_history("user", "message 3")
        session.add_to_history("assistant", "response 3")
        
        # Should only keep last 2*2 entries (user+assistant pairs)
        assert len(session.history) == 4
        assert session.history[0]["content"] == "message 2"
        
        # Clear history
        session.clear_history()
        assert len(session.history) == 0

    def test_context_building(self) -> None:
        """Test context building with history."""
        chat_module = _import_chat_script()
        ChatSession = chat_module.ChatSession
        
        session = ChatSession("http://localhost:8001")
        session.additional_context = {"tick": 10}
        session.add_to_history("user", "hello")
        session.add_to_history("assistant", "hi")
        
        context = session.build_context()
        assert context["tick"] == 10
        assert len(context["history"]) == 2
        assert context["history"][0]["role"] == "user"

    def test_save_transcript(self, tmp_path) -> None:
        """Test saving transcript to file."""
        chat_module = _import_chat_script()
        ChatSession = chat_module.ChatSession
        
        session = ChatSession("http://localhost:8001", mode="parse")
        session.add_to_history("user", "test")
        session.add_to_history("assistant", "response")
        
        transcript_path = tmp_path / "transcript.json"
        session.save_transcript(str(transcript_path))
        
        # Verify file was created and contains expected data
        assert transcript_path.exists()
        with open(transcript_path) as f:
            data = json.load(f)
        
        assert data["mode"] == "parse"
        assert data["service_url"] == "http://localhost:8001"
        assert len(data["history"]) == 2

    def test_context_file_loading(self, tmp_path) -> None:
        """Test loading initial context from file."""
        chat_module = _import_chat_script()
        ChatSession = chat_module.ChatSession
        
        # Create a context file
        context_file = tmp_path / "context.json"
        context_data = {"tick": 5, "district": "industrial"}
        with open(context_file, "w") as f:
            json.dump(context_data, f)
        
        # Create session with context file
        session = ChatSession(
            "http://localhost:8001",
            context_file=str(context_file),
        )
        
        assert session.additional_context["tick"] == 5
        assert session.additional_context["district"] == "industrial"
