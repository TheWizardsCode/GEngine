"""Typed HTTP client for the Echoes simulation service."""

from __future__ import annotations

from typing import Any

import httpx


class SimServiceClient:
    """Minimal synchronous client for interacting with the simulation API."""

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 10.0,
        client: Any = None,
    ) -> None:
        self._client = client or httpx.Client(base_url=base_url, timeout=timeout)

    # Context manager helpers -----------------------------------------
    def __enter__(self) -> "SimServiceClient":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    # Public API -------------------------------------------------------
    def tick(self, ticks: int) -> dict[str, Any]:
        response = self._client.post("/tick", json={"ticks": ticks})
        response.raise_for_status()
        return response.json()

    def state(
        self, detail: str = "summary", district_id: str | None = None
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"detail": detail}
        if district_id is not None:
            params["district_id"] = district_id
        response = self._client.get("/state", params=params)
        response.raise_for_status()
        return response.json()

    def metrics(self) -> dict[str, Any]:
        response = self._client.get("/metrics")
        response.raise_for_status()
        return response.json()

    def submit_actions(self, actions: list[dict[str, Any]]) -> dict[str, Any]:
        response = self._client.post("/actions", json={"actions": actions})
        response.raise_for_status()
        return response.json()

    def focus_state(self) -> dict[str, Any]:
        response = self._client.get("/focus")
        response.raise_for_status()
        return response.json()

    def set_focus(self, district_id: str | None) -> dict[str, Any]:
        response = self._client.post("/focus", json={"district_id": district_id})
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        close = getattr(self._client, "close", None)
        if callable(close):
            close()
