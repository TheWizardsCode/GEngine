"""CLI entry point for running the Echoes gateway service."""

from __future__ import annotations

import uvicorn  # pragma: no cover

from ..settings import load_simulation_config  # pragma: no cover
from .app import GatewaySettings, create_gateway_app  # pragma: no cover


def main() -> None:  # pragma: no cover - uvicorn runner
    settings = GatewaySettings.from_env()  # pragma: no cover
    config = load_simulation_config()  # pragma: no cover
    app = create_gateway_app(config=config, settings=settings)  # pragma: no cover
    uvicorn.run(app, host=settings.host, port=settings.port)  # pragma: no cover


if __name__ == "__main__":  # pragma: no cover
    main()  # pragma: no cover
