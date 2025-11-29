"""Main entry point for LLM service."""

from __future__ import annotations

import logging

import uvicorn

from .app import create_llm_app
from .settings import LLMSettings

logger = logging.getLogger(__name__)


def main() -> None:
    """Run the LLM service."""
    settings = LLMSettings.from_env()
    
    try:
        settings.validate()
    except ValueError as e:
        logger.error(f"Invalid LLM settings: {e}")
        raise

    app = create_llm_app(settings=settings)
    
    host = "0.0.0.0"
    port = 8001  # Different port from simulation service (8000)
    
    logger.info(f"Starting LLM service with provider '{settings.provider}'")
    if settings.model:
        logger.info(f"Using model: {settings.model}")
    
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    main()
