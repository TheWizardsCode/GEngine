"""HTTP client for the LLM service."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from ..llm import GameIntent, parse_intent

LOGGER = logging.getLogger("gengine.echoes.gateway.llm")


import os
import subprocess

class LLMClient:
    """HTTP client for the LLM service.

    Provides intent parsing and narration with retry logic and fallback handling.
    """

    def __init__(
        self,
        base_url: str | None = None,
        *,
        timeout: float = 30.0,
        max_retries: int = 2,
    ) -> None:
        """Initialize LLM client.

        Args:
            base_url: Base URL of the LLM service (e.g., "http://localhost:8001")
            timeout: Request timeout in seconds
            max_retries: Number of retry attempts for failed requests
        """
        if not base_url or base_url in ("http://windows-host:8001", "http://localhost:8001"):
            # Try environment variable first
            base_url = os.environ.get("LLM_SERVICE_URL")
        if not base_url or base_url in ("http://windows-host:8001", "http://localhost:8001"):
            # Auto-discover Windows host IP from WSL
            try:
                result = subprocess.run(["ip", "route"], capture_output=True, text=True)
                for line in result.stdout.splitlines():
                    if line.startswith("default"):
                        win_host_ip = line.split()[2]
                        base_url = f"http://{win_host_ip}:8001"
                        print(f"Auto-discovered Windows host: {base_url}")
                        break
            except Exception as e:
                LOGGER.warning(f"Failed to auto-discover Windows host IP: {e}")
        if not base_url:
            raise RuntimeError("Could not determine LLM service URL. Set LLM_SERVICE_URL or provide base_url.")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = httpx.Client(timeout=timeout)

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> "LLMClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    def parse_intent(
        self,
        text: str,
        *,
        context: dict[str, Any] | None = None,
    ) -> GameIntent | None:
        """Parse natural language text into a structured game intent.

        Args:
            text: Natural language command from user
            context: Optional context (district, tick, recent_events, etc.)

        Returns:
            Parsed GameIntent or None if parsing fails
        """
        payload = {"text": text}
        if context:
            payload["context"] = context

        for attempt in range(self.max_retries + 1):
            try:
                response = self._client.post(
                    f"{self.base_url}/parse_intent",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

                # The LLM response should contain intent data directly
                # or wrapped in an "intent" field
                intent_data = data.get("intent", data)

                if not isinstance(intent_data, dict):
                    LOGGER.warning(
                        "LLM response intent is not a dict: %s", type(intent_data)
                    )
                    return None

                return parse_intent(intent_data)

            except httpx.HTTPStatusError as exc:
                LOGGER.warning(
                    "LLM parse_intent failed (attempt %d/%d): HTTP %d",
                    attempt + 1,
                    self.max_retries + 1,
                    exc.response.status_code,
                )
                if attempt == self.max_retries:
                    LOGGER.error("LLM parse_intent exhausted retries")
                    return None

            except (httpx.RequestError, ValueError) as exc:
                LOGGER.warning(
                    "LLM parse_intent error (attempt %d/%d): %s",
                    attempt + 1,
                    self.max_retries + 1,
                    exc,
                )
                if attempt == self.max_retries:
                    LOGGER.error("LLM parse_intent exhausted retries")
                    return None

        return None

    def narrate(
        self,
        events: list[str],
        *,
        context: dict[str, Any] | None = None,
    ) -> str | None:
        """Generate narrative text from simulation events.

        Args:
            events: List of event strings from simulation
            context: Optional context (district, tick, etc.)

        Returns:
            Generated narration or None if generation fails
        """
        payload = {"events": events}
        if context:
            payload["context"] = context

        for attempt in range(self.max_retries + 1):
            try:
                response = self._client.post(
                    f"{self.base_url}/narrate",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

                narration = data.get("narration")
                if not narration:
                    LOGGER.warning("LLM response missing 'narration' field: %s", data)
                    return None

                return str(narration)

            except httpx.HTTPStatusError as exc:
                LOGGER.warning(
                    "LLM narrate failed (attempt %d/%d): HTTP %d",
                    attempt + 1,
                    self.max_retries + 1,
                    exc.response.status_code,
                )
                if attempt == self.max_retries:
                    LOGGER.error("LLM narrate exhausted retries")
                    return None

            except (httpx.RequestError, ValueError) as exc:
                LOGGER.warning(
                    "LLM narrate error (attempt %d/%d): %s",
                    attempt + 1,
                    self.max_retries + 1,
                    exc,
                )
                if attempt == self.max_retries:
                    LOGGER.error("LLM narrate exhausted retries")
                    return None

        return None

    def healthcheck(self) -> bool:
        """Check if LLM service is healthy.

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            response = self._client.get(f"{self.base_url}/healthz", timeout=5.0)
            response.raise_for_status()
            return True
        except (httpx.HTTPError, ValueError):
            return False
