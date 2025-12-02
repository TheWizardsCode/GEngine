"""Lightweight CLI client for the Echoes gateway service."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from typing import Sequence

import websockets

from ..cli.shell import PROMPT


async def _run_session(url: str, script: list[str]) -> None:
    commands = list(script)
    async with websockets.connect(url) as websocket:
        welcome_raw = await websocket.recv()
        _render_response(welcome_raw)
        while True:
            if commands:
                command = commands.pop(0)
                print(f"{PROMPT}{command}")
            else:  # pragma: no cover - interactive input
                try:
                    command = input(PROMPT)
                except (EOFError, KeyboardInterrupt):
                    command = "exit"
            await websocket.send(json.dumps({"command": command}))
            response_raw = await websocket.recv()
            data = _render_response(response_raw)
            if data.get("should_exit"):
                break


def _render_response(payload: str) -> dict[str, object]:
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        print(payload)
        return {}
    output = data.get("output")
    if output:
        print(output)
    error = data.get("error")
    if error:
        print(f"[gateway] {error}")
    return data


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Echoes gateway shell client")
    parser.add_argument(
        "--gateway-url",
        default=os.environ.get("ECHOES_GATEWAY_URL", "ws://localhost:8100/ws"),
        help="WebSocket URL for the gateway service",
    )
    parser.add_argument(
        "--script",
        help="Semicolon-separated list of commands to run and then exit",
    )
    args = parser.parse_args(argv)
    script: list[str] = []
    if args.script:
        script = [cmd.strip() for cmd in args.script.split(";") if cmd.strip()]
    try:
        asyncio.run(_run_session(args.gateway_url, script))
    except KeyboardInterrupt:  # pragma: no cover - interactive cancel
        return 0
    except (
        websockets.exceptions.ConnectionClosedError
    ) as exc:  # pragma: no cover - passthrough
        print(f"Gateway connection closed: {exc}")
        return 1
    except OSError as exc:  # pragma: no cover - networking failure
        print(f"Failed to connect to gateway: {exc}")
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
