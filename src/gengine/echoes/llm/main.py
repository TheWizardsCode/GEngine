"""Main entry point for LLM service."""

from __future__ import annotations

import argparse
import json
import logging
from typing import Sequence

import uvicorn

from .app import create_llm_app
from .settings import LLMSettings

logger = logging.getLogger(__name__)


def _configure_logging(level: int = logging.INFO) -> None:
    """Initialize logging if the process has no handlers yet."""
    root_logger = logging.getLogger()
    if root_logger.handlers:
        root_logger.setLevel(level)
        return
    logging.basicConfig(level=level)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for the LLM service runner."""
    parser = argparse.ArgumentParser(description="Run the Echoes LLM service")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8001, help="Port to bind (default: 8001)")
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Log JSON payloads sent to and received from the LLM provider",
    )
    parser.add_argument(
        "--no-streaming",
        action="store_true",
        help="Disable streaming responses (forces buffered mode)",
    )
    return parser.parse_args(argv)


def main() -> None:
    """Run the LLM service."""
    args = _parse_args()

    # Determine log level/verbosity before instantiating providers
    verbose_requested = args.verbose
    # Logging level only depends on explicit CLI request to avoid surprising noise
    _configure_logging(logging.DEBUG if verbose_requested else logging.INFO)
    settings = LLMSettings.from_env()
    effective_verbose = settings.verbose_logging or verbose_requested
    settings.verbose_logging = effective_verbose
    
    # Apply --no-streaming CLI flag (overrides environment variable)
    if args.no_streaming:
        settings.enable_streaming = False

    try:
        settings.validate()
    except ValueError as e:
        logger.error(f"Invalid LLM settings: {e}")
        raise

    config_snapshot = json.dumps(settings.loggable_dict(), indent=2, sort_keys=True)
    logger.info("LLM service configuration:\n%s", config_snapshot)
    if settings.verbose_logging:
        logger.info(
            "Verbose mode enabled; JSON requests/responses will be logged for provider calls."
        )

    app = create_llm_app(settings=settings)

    host = args.host
    port = args.port

    logger.info(f"Starting LLM service with provider '{settings.provider}'")
    if settings.model:
        logger.info(f"Using model: {settings.model}")

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    main()
