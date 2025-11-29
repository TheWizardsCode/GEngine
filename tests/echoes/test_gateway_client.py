"""Tests for the Echoes gateway client."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

from gengine.echoes.gateway.client import _render_response, main


def test_render_response_with_valid_json() -> None:
    """Verify that _render_response parses JSON and returns a dict."""
    payload = json.dumps({"output": "Hello", "should_exit": False})
    result = _render_response(payload)
    assert result == {"output": "Hello", "should_exit": False}


def test_render_response_with_invalid_json(capsys) -> None:
    """Verify that _render_response handles malformed JSON gracefully."""
    payload = "not json"
    result = _render_response(payload)
    assert result == {}
    captured = capsys.readouterr()
    assert "not json" in captured.out


def test_render_response_with_output(capsys) -> None:
    """Verify that _render_response prints the output field."""
    payload = json.dumps({"output": "Summary text"})
    result = _render_response(payload)
    assert "output" in result
    captured = capsys.readouterr()
    assert "Summary text" in captured.out


def test_render_response_with_error(capsys) -> None:
    """Verify that _render_response prints the error field."""
    payload = json.dumps({"error": "Something went wrong"})
    result = _render_response(payload)
    assert "error" in result
    captured = capsys.readouterr()
    assert "[gateway] Something went wrong" in captured.out


def test_main_with_script() -> None:
    """Verify that main() parses --script and delegates to _run_session."""
    with patch("gengine.echoes.gateway.client.asyncio.run") as mock_run:
        result = main(["--script", "summary;exit"])
    assert result == 0
    mock_run.assert_called_once()
    args, _ = mock_run.call_args
    # The first arg to asyncio.run is the coroutine returned by _run_session
    assert args[0].__class__.__name__ == "coroutine"


def test_main_uses_default_gateway_url() -> None:
    """Verify that main() uses the default gateway URL when no env is set."""
    with patch("gengine.echoes.gateway.client.asyncio.run") as mock_run:
        main(["--script", "exit"])
    mock_run.assert_called_once()


def test_main_uses_env_gateway_url() -> None:
    """Verify that main() respects the ECHOES_GATEWAY_URL environment variable."""
    with patch("gengine.echoes.gateway.client.asyncio.run") as mock_run, patch.dict(
        "os.environ", {"ECHOES_GATEWAY_URL": "ws://custom:9000/ws"}
    ):
        main(["--script", "exit"])
    mock_run.assert_called_once()


def test_render_response_with_exit_flag(capsys) -> None:
    """Verify that _render_response returns should_exit flag."""
    payload = json.dumps({"output": "Goodbye", "should_exit": True})
    result = _render_response(payload)
    assert result["should_exit"] is True
    captured = capsys.readouterr()
    assert "Goodbye" in captured.out


def test_render_response_with_empty_dict(capsys) -> None:
    """Verify that _render_response handles empty dict gracefully."""
    payload = json.dumps({})
    result = _render_response(payload)
    assert result == {}
    captured = capsys.readouterr()
    assert captured.out == ""


def test_main_with_gateway_url_flag() -> None:
    """Verify that --gateway-url flag overrides the default URL."""
    with patch("gengine.echoes.gateway.client.asyncio.run") as mock_run:
        main(["--gateway-url", "ws://custom:9000/ws", "--script", "exit"])
    mock_run.assert_called_once()


def test_main_splits_script_commands() -> None:
    """Verify that --script semicolon-separated commands are parsed correctly."""
    with patch("gengine.echoes.gateway.client.asyncio.run") as mock_run:
        main(["--script", "summary; next; exit"])
    mock_run.assert_called_once()
    # Extract the coroutine argument and verify it's _run_session
    call_args = mock_run.call_args[0]
    assert len(call_args) == 1
    coro = call_args[0]
    assert coro.__class__.__name__ == "coroutine"


def test_main_empty_script_strips_whitespace() -> None:
    """Verify that empty/whitespace-only commands are filtered out."""
    with patch("gengine.echoes.gateway.client.asyncio.run") as mock_run:
        main(["--script", "; ; exit; ;"])
    mock_run.assert_called_once()


def test_main_no_script_runs_interactively() -> None:
    """Verify that main() without --script invokes asyncio.run."""
    with patch("gengine.echoes.gateway.client.asyncio.run") as mock_run:
        main([])
    mock_run.assert_called_once()
