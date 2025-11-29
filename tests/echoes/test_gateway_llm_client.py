"""Tests for gateway LLM client."""

import pytest
import httpx
from unittest.mock import Mock, patch

from gengine.echoes.gateway.llm_client import LLMClient
from gengine.echoes.llm import InspectIntent, IntentType


class TestLLMClient:
    """Test LLM client functionality."""

    def test_initialization(self):
        """Test client initialization."""
        client = LLMClient("http://localhost:8001", timeout=10.0, max_retries=3)
        assert client.base_url == "http://localhost:8001"
        assert client.timeout == 10.0
        assert client.max_retries == 3
        client.close()

    def test_context_manager(self):
        """Test client works as context manager."""
        with LLMClient("http://localhost:8001") as client:
            assert client.base_url == "http://localhost:8001"

    @patch("httpx.Client.post")
    def test_parse_intent_success(self, mock_post):
        """Test successful intent parsing."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "intent": {
                "intent": "INSPECT",
                "session_id": "test-session",
                "target_type": "district",
                "target_id": "industrial-tier",
            }
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = LLMClient("http://localhost:8001")
        intent = client.parse_intent("inspect the industrial tier")

        assert intent is not None
        assert isinstance(intent, InspectIntent)
        assert intent.target_type == "district"
        assert intent.target_id == "industrial-tier"
        client.close()

    @patch("httpx.Client.post")
    def test_parse_intent_with_context(self, mock_post):
        """Test intent parsing with context."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "intent": {
                "intent": "INSPECT",
                "session_id": "test-session",
                "target_type": "district",
                "target_id": "test",
            }
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = LLMClient("http://localhost:8001")
        context = {"district": "industrial-tier", "tick": 42}
        intent = client.parse_intent("look around", context=context)

        assert intent is not None
        # Verify context was passed
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["context"] == context
        client.close()

    @patch("httpx.Client.post")
    def test_parse_intent_missing_intent_field(self, mock_post):
        """Test parsing fails gracefully when intent field missing."""
        mock_response = Mock()
        mock_response.json.return_value = {"error": "Invalid request"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = LLMClient("http://localhost:8001")
        intent = client.parse_intent("test")

        assert intent is None
        client.close()

    @patch("httpx.Client.post")
    def test_parse_intent_http_error_with_retry(self, mock_post):
        """Test parsing retries on HTTP errors."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server error", request=Mock(), response=mock_response
        )
        mock_post.return_value = mock_response

        client = LLMClient("http://localhost:8001", max_retries=2)
        intent = client.parse_intent("test")

        assert intent is None
        assert mock_post.call_count == 3  # initial + 2 retries
        client.close()

    @patch("httpx.Client.post")
    def test_parse_intent_request_error(self, mock_post):
        """Test parsing handles request errors."""
        mock_post.side_effect = httpx.RequestError("Connection failed")

        client = LLMClient("http://localhost:8001", max_retries=1)
        intent = client.parse_intent("test")

        assert intent is None
        assert mock_post.call_count == 2  # initial + 1 retry
        client.close()

    @patch("httpx.Client.post")
    def test_narrate_success(self, mock_post):
        """Test successful narration."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "narration": "The city bustles with activity."
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = LLMClient("http://localhost:8001")
        narration = client.narrate(["Agent recruited", "Pollution increased"])

        assert narration == "The city bustles with activity."
        client.close()

    @patch("httpx.Client.post")
    def test_narrate_with_context(self, mock_post):
        """Test narration with context."""
        mock_response = Mock()
        mock_response.json.return_value = {"narration": "Test narration"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = LLMClient("http://localhost:8001")
        context = {"district": "perimeter-hollow", "tick": 10}
        narration = client.narrate(["Event 1"], context=context)

        assert narration == "Test narration"
        # Verify context was passed
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json"]["context"] == context
        client.close()

    @patch("httpx.Client.post")
    def test_narrate_missing_narration_field(self, mock_post):
        """Test narration fails gracefully when narration field missing."""
        mock_response = Mock()
        mock_response.json.return_value = {"error": "Invalid request"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = LLMClient("http://localhost:8001")
        narration = client.narrate(["Test event"])

        assert narration is None
        client.close()

    @patch("httpx.Client.post")
    def test_narrate_http_error(self, mock_post):
        """Test narration handles HTTP errors."""
        mock_response = Mock()
        mock_response.status_code = 503
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Service unavailable", request=Mock(), response=mock_response
        )
        mock_post.return_value = mock_response

        client = LLMClient("http://localhost:8001", max_retries=1)
        narration = client.narrate(["Test"])

        assert narration is None
        assert mock_post.call_count == 2  # initial + 1 retry
        client.close()

    @patch("httpx.Client.get")
    def test_healthcheck_healthy(self, mock_get):
        """Test healthcheck when service is healthy."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        client = LLMClient("http://localhost:8001")
        is_healthy = client.healthcheck()

        assert is_healthy is True
        client.close()

    @patch("httpx.Client.get")
    def test_healthcheck_unhealthy(self, mock_get):
        """Test healthcheck when service is unhealthy."""
        mock_get.side_effect = httpx.RequestError("Connection refused")

        client = LLMClient("http://localhost:8001")
        is_healthy = client.healthcheck()

        assert is_healthy is False
        client.close()
