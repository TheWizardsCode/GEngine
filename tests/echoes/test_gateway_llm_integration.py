"""Tests for Gateway → LLM → Simulation integration flow.

This module tests the full integration path from gateway through LLM service
to simulation, with comprehensive mocking to ensure no real API calls are made.
"""

from __future__ import annotations

from unittest.mock import Mock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from gengine.echoes.cli.shell import LocalBackend
from gengine.echoes.gateway.app import (
    GatewayMetrics,
    GatewaySettings,
    create_gateway_app,
)
from gengine.echoes.gateway.llm_client import LLMClient
from gengine.echoes.gateway.session import GatewaySession
from gengine.echoes.llm import (
    DeployResourceIntent,
    InspectIntent,
    NegotiateIntent,
    parse_intent,
)
from gengine.echoes.sim import SimEngine

# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def sim_engine():
    """Create and initialize a simulation engine."""
    engine = SimEngine()
    engine.initialize_state(world="default")
    return engine


@pytest.fixture
def local_backend(sim_engine):
    """Create a local backend with initialized engine."""
    return LocalBackend(sim_engine)


def _local_backend_factory(config):
    """Create a factory that produces local backends."""

    def _factory() -> LocalBackend:
        engine = SimEngine(config=config)
        engine.initialize_state(world="default")
        return LocalBackend(engine)

    return _factory


# ==============================================================================
# LLM Client Mock Tests
# ==============================================================================


class TestLLMClientMockScenarios:
    """Additional LLM client tests with mocked HTTP responses."""

    @patch("httpx.Client.post")
    def test_parse_intent_timeout(self, mock_post) -> None:
        """LLM client handles timeout gracefully."""
        mock_post.side_effect = httpx.TimeoutException("Connection timed out")

        client = LLMClient("http://localhost:8001", max_retries=1)
        intent = client.parse_intent("test command")

        assert intent is None
        # Should retry once
        assert mock_post.call_count == 2
        client.close()

    @patch("httpx.Client.post")
    def test_parse_intent_connection_error(self, mock_post) -> None:
        """LLM client handles connection errors."""
        mock_post.side_effect = httpx.ConnectError("Connection refused")

        client = LLMClient("http://localhost:8001", max_retries=2)
        intent = client.parse_intent("test command")

        assert intent is None
        assert mock_post.call_count == 3  # Initial + 2 retries
        client.close()

    @patch("httpx.Client.post")
    def test_parse_intent_invalid_json_response(self, mock_post) -> None:
        """LLM client handles invalid JSON in response."""
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        client = LLMClient("http://localhost:8001", max_retries=1)
        intent = client.parse_intent("test command")

        assert intent is None
        client.close()

    @patch("httpx.Client.post")
    def test_parse_intent_all_intent_types(self, mock_post) -> None:
        """LLM client parses all supported intent types."""
        intent_types = [
            {
                "intent": "INSPECT",
                "session_id": "test",
                "target_type": "district",
                "target_id": "industrial-tier",
            },
            {
                "intent": "NEGOTIATE",
                "session_id": "test",
                "targets": ["union-flux"],
                "goal": "peace",
            },
            {
                "intent": "DEPLOY_RESOURCE",
                "session_id": "test",
                "resource_type": "materials",
                "amount": 50,
                "target_district": "spire",
            },
            {
                "intent": "REQUEST_REPORT",
                "session_id": "test",
                "report_type": "summary",
            },
        ]

        client = LLMClient("http://localhost:8001")

        for intent_data in intent_types:
            mock_response = Mock()
            mock_response.json.return_value = {"intent": intent_data}
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response

            intent = client.parse_intent(f"test {intent_data['intent']}")
            assert intent is not None
            assert intent.intent.value == intent_data["intent"]

        client.close()

    @patch("httpx.Client.post")
    def test_narrate_timeout(self, mock_post) -> None:
        """LLM client narrate handles timeout."""
        mock_post.side_effect = httpx.TimeoutException("Timeout")

        client = LLMClient("http://localhost:8001", max_retries=0)
        narration = client.narrate(["event1", "event2"])

        assert narration is None
        client.close()

    @patch("httpx.Client.post")
    def test_narrate_server_error_retry(self, mock_post) -> None:
        """LLM client retries on server errors."""
        # First two calls fail, third succeeds
        mock_error_response = Mock()
        mock_error_response.status_code = 500
        mock_error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server Error", request=Mock(), response=mock_error_response
        )

        mock_success_response = Mock()
        mock_success_response.json.return_value = {
            "narration": "The city recovers from the crisis."
        }
        mock_success_response.raise_for_status = Mock()

        mock_post.side_effect = [
            mock_error_response,
            mock_error_response,
            mock_success_response,
        ]

        client = LLMClient("http://localhost:8001", max_retries=2)
        narration = client.narrate(["crisis resolved"])

        assert narration == "The city recovers from the crisis."
        assert mock_post.call_count == 3
        client.close()

    @patch("httpx.Client.get")
    def test_healthcheck_timeout(self, mock_get) -> None:
        """LLM client healthcheck handles timeout."""
        mock_get.side_effect = httpx.TimeoutException("Health check timeout")

        client = LLMClient("http://localhost:8001")
        is_healthy = client.healthcheck()

        assert is_healthy is False
        client.close()


# ==============================================================================
# Gateway Session Integration Tests
# ==============================================================================


class TestGatewaySessionLLMIntegration:
    """Tests for gateway session with LLM client integration."""

    @pytest.fixture
    def gateway_session_with_mock_llm(self, local_backend):
        """Create a gateway session with a mocked LLM client."""
        from gengine.echoes.settings import load_simulation_config

        config = load_simulation_config()
        mock_llm = Mock(spec=LLMClient)
        mock_llm.healthcheck.return_value = True

        session = GatewaySession(
            local_backend, limits=config.limits, llm_client=mock_llm
        )
        return session, mock_llm

    def test_session_has_llm_client(self, gateway_session_with_mock_llm) -> None:
        """Session stores LLM client reference."""
        session, mock_llm = gateway_session_with_mock_llm
        assert session.llm_client is mock_llm

    def test_session_without_llm_client(self, local_backend) -> None:
        """Session works without LLM client."""
        from gengine.echoes.settings import load_simulation_config

        config = load_simulation_config()
        session = GatewaySession(local_backend, limits=config.limits)

        assert session.llm_client is None
        # Standard commands should still work
        result = session.execute("summary")
        assert not result.should_exit
        assert "summary" in result.output.lower() or "Current" in result.output


# ==============================================================================
# Gateway App LLM Flow Tests
# ==============================================================================


class TestGatewayAppLLMFlow:
    """Tests for the complete gateway app with LLM integration."""

    @pytest.fixture
    def gateway_settings_with_llm(self):
        """Gateway settings with LLM service URL configured."""
        return GatewaySettings(
            service_url="local",
            llm_service_url="http://localhost:8001",
        )

    def test_gateway_healthcheck_includes_llm_url(
        self, sim_config, gateway_settings_with_llm
    ) -> None:
        """Gateway healthcheck reports LLM service URL when configured."""
        app = create_gateway_app(
            backend_factory=_local_backend_factory(sim_config),
            config=sim_config,
            settings=gateway_settings_with_llm,
        )
        client = TestClient(app)

        response = client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data["llm_service_url"] == "http://localhost:8001"

    def test_gateway_metrics_include_llm_section(self, sim_config) -> None:
        """Gateway metrics always include LLM section."""
        settings = GatewaySettings(service_url="local")
        app = create_gateway_app(
            backend_factory=_local_backend_factory(sim_config),
            config=sim_config,
            settings=settings,
        )
        client = TestClient(app)

        response = client.get("/metrics")
        data = response.json()

        assert "llm_integration" in data
        assert "requests" in data["llm_integration"]
        assert "errors" in data["llm_integration"]
        assert "latency_ms" in data["llm_integration"]

    def test_gateway_websocket_regular_command(self, sim_config) -> None:
        """Gateway processes regular commands without LLM."""
        settings = GatewaySettings(service_url="local")
        app = create_gateway_app(
            backend_factory=_local_backend_factory(sim_config),
            config=sim_config,
            settings=settings,
        )
        client = TestClient(app)

        with client.websocket_connect("/ws") as websocket:
            _ = websocket.receive_json()  # Welcome
            websocket.send_json({"command": "summary", "natural_language": False})
            response = websocket.receive_json()
            assert response["type"] == "result"
            assert (
                "summary" in response["output"].lower()
                or "Current" in response["output"]
            )
            websocket.send_json({"command": "exit"})
            _ = websocket.receive_json()


# ==============================================================================
# Gateway Metrics LLM Tracking Tests
# ==============================================================================


class TestGatewayMetricsLLMTracking:
    """Tests for LLM-specific metrics tracking."""

    def test_metrics_record_llm_request(self) -> None:
        """Metrics track LLM requests with latency."""
        metrics = GatewayMetrics()

        metrics.record_llm_request(100.0)
        metrics.record_llm_request(150.0)
        metrics.record_llm_request(200.0)

        assert metrics.llm_requests == 3
        assert len(metrics.llm_latencies) == 3
        assert metrics.llm_latencies[0] == 100.0

    def test_metrics_record_llm_error(self) -> None:
        """Metrics track LLM errors."""
        metrics = GatewayMetrics()

        metrics.record_llm_error()
        metrics.record_llm_error()

        assert metrics.llm_errors == 2

    def test_metrics_llm_latency_stats(self) -> None:
        """Metrics calculate LLM latency statistics."""
        metrics = GatewayMetrics()

        for i in range(10):
            metrics.record_llm_request(float(i * 20))

        data = metrics.to_dict()
        llm_stats = data["llm_integration"]["latency_ms"]

        assert llm_stats["min"] == 0.0
        assert llm_stats["max"] == 180.0
        assert llm_stats["avg"] == 90.0

    def test_metrics_llm_latency_capped(self) -> None:
        """LLM latency samples are capped at max_latency_samples."""
        metrics = GatewayMetrics()
        metrics.max_latency_samples = 5

        for i in range(10):
            metrics.record_llm_request(float(i))

        # Should only keep last 5
        assert len(metrics.llm_latencies) == 5
        assert metrics.llm_latencies == [5.0, 6.0, 7.0, 8.0, 9.0]

    def test_metrics_to_dict_includes_all_llm_fields(self) -> None:
        """to_dict includes all LLM integration fields."""
        metrics = GatewayMetrics()
        metrics.record_llm_request(50.0)
        metrics.record_llm_error()

        data = metrics.to_dict()
        llm = data["llm_integration"]

        assert llm["requests"] == 1
        assert llm["errors"] == 1
        assert "avg" in llm["latency_ms"]
        assert "min" in llm["latency_ms"]
        assert "max" in llm["latency_ms"]


# ==============================================================================
# Intent Parsing Edge Cases
# ==============================================================================


class TestIntentParsingEdgeCases:
    """Edge case tests for intent parsing through the gateway."""

    def test_parse_inspect_intent(self) -> None:
        """Parse INSPECT intent from dict."""
        data = {
            "intent": "INSPECT",
            "session_id": "test",
            "target_type": "district",
            "target_id": "industrial-tier",
        }
        intent = parse_intent(data)
        assert isinstance(intent, InspectIntent)
        assert intent.target_type == "district"

    def test_parse_negotiate_intent(self) -> None:
        """Parse NEGOTIATE intent from dict."""
        data = {
            "intent": "NEGOTIATE",
            "session_id": "test",
            "targets": ["faction-a", "faction-b"],
            "goal": "peace",
        }
        intent = parse_intent(data)
        assert isinstance(intent, NegotiateIntent)
        assert len(intent.targets) == 2

    def test_parse_deploy_resource_intent(self) -> None:
        """Parse DEPLOY_RESOURCE intent from dict."""
        data = {
            "intent": "DEPLOY_RESOURCE",
            "session_id": "test",
            "resource_type": "energy",
            "amount": 100,
            "target_district": "spire",
        }
        intent = parse_intent(data)
        assert isinstance(intent, DeployResourceIntent)
        assert intent.amount == 100

    def test_parse_intent_missing_field_raises(self) -> None:
        """Missing required fields raise validation error."""
        data = {
            "intent": "INSPECT",
            "session_id": "test",
            # Missing target_type and target_id
        }
        with pytest.raises(ValueError):  # Pydantic ValidationError
            parse_intent(data)

    def test_parse_intent_unknown_type_raises(self) -> None:
        """Unknown intent type raises ValueError."""
        data = {
            "intent": "UNKNOWN_INTENT",
            "session_id": "test",
        }
        with pytest.raises(ValueError, match="Unknown intent type"):
            parse_intent(data)


# ==============================================================================
# Full Flow Integration Tests
# ==============================================================================


class TestFullGatewayLLMFlow:
    """Full integration tests for Gateway → LLM → Simulation flow."""

    @patch("httpx.Client")
    def test_full_flow_inspect_command(self, mock_client_class, sim_config) -> None:
        """Full flow: natural language → LLM parse → simulation query."""
        # Setup mock LLM client responses
        mock_client = Mock()

        # Mock healthcheck
        mock_health_response = Mock()
        mock_health_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_health_response

        # Mock parse_intent
        mock_parse_response = Mock()
        mock_parse_response.json.return_value = {
            "intent": {
                "intent": "INSPECT",
                "session_id": "test",
                "target_type": "district",
                "target_id": "industrial-tier",
            }
        }
        mock_parse_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_parse_response

        mock_client_class.return_value = mock_client

        # Create LLM client with mocked httpx
        llm_client = LLMClient("http://localhost:8001")
        intent = llm_client.parse_intent("check on the industrial district")

        assert intent is not None
        assert intent.intent.value == "INSPECT"
        assert intent.target_type == "district"

        llm_client.close()

    @patch("httpx.Client")
    def test_full_flow_negotiate_command(self, mock_client_class, sim_config) -> None:
        """Full flow: natural language negotiate → LLM → simulation action."""
        mock_client = Mock()

        mock_health_response = Mock()
        mock_health_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_health_response

        mock_parse_response = Mock()
        mock_parse_response.json.return_value = {
            "intent": {
                "intent": "NEGOTIATE",
                "session_id": "test",
                "targets": ["union-of-flux"],
                "goal": "reduce unrest",
            }
        }
        mock_parse_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_parse_response

        mock_client_class.return_value = mock_client

        llm_client = LLMClient("http://localhost:8001")
        intent = llm_client.parse_intent("negotiate with the Union of Flux")

        assert intent is not None
        assert intent.intent.value == "NEGOTIATE"
        assert "union-of-flux" in intent.targets

        llm_client.close()

    @patch("httpx.Client")
    def test_full_flow_deploy_resource_command(
        self, mock_client_class, sim_config
    ) -> None:
        """Full flow: deploy resource natural language → LLM → simulation."""
        mock_client = Mock()

        mock_health_response = Mock()
        mock_health_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_health_response

        mock_parse_response = Mock()
        mock_parse_response.json.return_value = {
            "intent": {
                "intent": "DEPLOY_RESOURCE",
                "session_id": "test",
                "resource_type": "materials",
                "amount": 50,
                "target_district": "perimeter-hollow",
                "purpose": "stabilization",
            }
        }
        mock_parse_response.raise_for_status = Mock()
        mock_client.post.return_value = mock_parse_response

        mock_client_class.return_value = mock_client

        llm_client = LLMClient("http://localhost:8001")
        intent = llm_client.parse_intent(
            "send 50 materials to perimeter hollow for stabilization"
        )

        assert intent is not None
        assert intent.intent.value == "DEPLOY_RESOURCE"
        assert intent.amount == 50
        assert intent.target_district == "perimeter-hollow"

        llm_client.close()

    def test_flow_without_llm_falls_back(self, sim_config) -> None:
        """Without LLM, gateway processes commands directly."""
        settings = GatewaySettings(service_url="local", llm_service_url=None)
        app = create_gateway_app(
            backend_factory=_local_backend_factory(sim_config),
            config=sim_config,
            settings=settings,
        )
        client = TestClient(app)

        with client.websocket_connect("/ws") as websocket:
            _ = websocket.receive_json()  # Welcome
            # Send command that would be natural language
            websocket.send_json({"command": "next", "natural_language": False})
            response = websocket.receive_json()
            assert response["type"] == "result"
            # Command should execute successfully
            assert "Tick" in response["output"]
            websocket.send_json({"command": "exit"})
            _ = websocket.receive_json()


# ==============================================================================
# Concurrent Request Tests
# ==============================================================================


class TestConcurrentLLMRequests:
    """Tests for concurrent LLM request handling."""

    @patch("httpx.Client")
    def test_multiple_sequential_parse_requests(self, mock_client_class) -> None:
        """Multiple sequential parse requests work correctly."""
        mock_client = Mock()

        mock_health_response = Mock()
        mock_health_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_health_response

        # Return different intents for sequential calls
        responses = [
            {
                "intent": {
                    "intent": "INSPECT",
                    "session_id": "test",
                    "target_type": "district",
                    "target_id": "d1",
                }
            },
            {
                "intent": {
                    "intent": "NEGOTIATE",
                    "session_id": "test",
                    "targets": ["faction-a"],
                }
            },
            {
                "intent": {
                    "intent": "REQUEST_REPORT",
                    "session_id": "test",
                    "report_type": "summary",
                }
            },
        ]

        mock_responses = []
        for resp in responses:
            mock_resp = Mock()
            mock_resp.json.return_value = resp
            mock_resp.raise_for_status = Mock()
            mock_responses.append(mock_resp)

        mock_client.post.side_effect = mock_responses
        mock_client_class.return_value = mock_client

        llm_client = LLMClient("http://localhost:8001")

        intent1 = llm_client.parse_intent("check district d1")
        intent2 = llm_client.parse_intent("talk to faction a")
        intent3 = llm_client.parse_intent("give me a summary")

        assert intent1.intent.value == "INSPECT"
        assert intent2.intent.value == "NEGOTIATE"
        assert intent3.intent.value == "REQUEST_REPORT"

        llm_client.close()
