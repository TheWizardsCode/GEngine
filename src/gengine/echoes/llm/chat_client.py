"""HTTP client for LLM service chat interface."""

from __future__ import annotations

from typing import Any

import httpx


class LLMChatClient:
    """HTTP client for interacting with the Echoes LLM service.
    
    Wraps httpx.AsyncClient and provides methods to hit /parse_intent
    and /narrate endpoints.
    """

    def __init__(
        self,
        base_url: str,
        timeout: float = 30.0,
        headers: dict[str, str] | None = None,
    ) -> None:
        """Initialize the LLM chat client.
        
        Parameters
        ----------
        base_url
            Base URL of the LLM service (e.g., "http://localhost:8001")
        timeout
            Request timeout in seconds
        headers
            Optional HTTP headers (e.g., for API keys)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.headers = headers or {}
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> LLMChatClient:
        """Enter async context manager."""
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers=self.headers,
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context manager."""
        if self._client is not None:
            await self._client.aclose()

    async def parse_intent(
        self,
        user_input: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Call /parse_intent endpoint.
        
        Parameters
        ----------
        user_input
            Natural language input from user
        context
            Game state context (history, metadata, etc.)
            
        Returns
        -------
        dict
            Response JSON from the service
            
        Raises
        ------
        httpx.HTTPStatusError
            If the request fails
        """
        if self._client is None:
            raise RuntimeError("Client not initialized. Use 'async with' context.")
        
        payload = {
            "user_input": user_input,
            "context": context or {},
        }
        
        response = await self._client.post("/parse_intent", json=payload)
        response.raise_for_status()
        return response.json()

    async def narrate(
        self,
        events: list[dict[str, Any]],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Call /narrate endpoint.
        
        Parameters
        ----------
        events
            Game events to narrate
        context
            Game state context (history, metadata, etc.)
            
        Returns
        -------
        dict
            Response JSON from the service
            
        Raises
        ------
        httpx.HTTPStatusError
            If the request fails
        """
        if self._client is None:
            raise RuntimeError("Client not initialized. Use 'async with' context.")
        
        payload = {
            "events": events,
            "context": context or {},
        }
        
        response = await self._client.post("/narrate", json=payload)
        response.raise_for_status()
        return response.json()

    async def health_check(self) -> dict[str, Any]:
        """Call /healthz endpoint.
        
        Returns
        -------
        dict
            Health check response
            
        Raises
        ------
        httpx.HTTPStatusError
            If the request fails
        """
        if self._client is None:
            raise RuntimeError("Client not initialized. Use 'async with' context.")
        
        response = await self._client.get("/healthz")
        response.raise_for_status()
        return response.json()
