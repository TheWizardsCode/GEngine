"""CLI entry point for running the Echoes simulation FastAPI service."""

from __future__ import annotations

import os

import uvicorn

from .app import create_app


def main() -> None:  # pragma: no cover - thin wrapper around uvicorn
    host = os.environ.get("ECHOES_SERVICE_HOST", "0.0.0.0")
    port = int(os.environ.get("ECHOES_SERVICE_PORT", "8000"))
    world = os.environ.get("ECHOES_SERVICE_WORLD", "default")

    app = create_app(auto_world=world)
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":  # pragma: no cover
    main()
