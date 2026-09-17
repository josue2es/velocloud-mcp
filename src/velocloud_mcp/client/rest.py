"""HTTP client for the VeloCloud Orchestrator REST API (v2)."""

import asyncio
from typing import Any

import httpx

from velocloud_mcp.client.auth import auth_headers
from velocloud_mcp.config import Settings


class VcoApiError(RuntimeError):
    """The Orchestrator answered, but not with success."""

    def __init__(self, status_code: int, path: str, detail: str) -> None:
        super().__init__(f"HTTP {status_code} from {path}: {detail}")
        self.status_code = status_code
        self.path = path


class VcoClient:
    """One per process. The semaphore caps concurrent calls against the Orchestrator,
    which asks clients to keep no more than 2-4 requests in flight at a time."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._limit = asyncio.Semaphore(settings.max_in_flight)
        self._http = httpx.AsyncClient(
            base_url=f"https://{settings.host}",
            headers=auth_headers(settings),
            verify=settings.verify_tls,
            timeout=settings.request_timeout,
        )

    async def enterprises(self) -> list[dict]:
        """Raw customer records. Projection happens in domain, not here."""
        payload = await self.get("/enterprises")
        return payload.get("data", payload) if isinstance(payload, dict) else payload

    async def aclose(self) -> None:
        await self._http.aclose()

    async def get(self, path: str) -> Any:
        """GET a v2 path relative to the API base, e.g. '/enterprises'."""
        return await self._request("GET", f"{self._settings.api_base}{path}")

    async def _request(self, method: str, path: str, json: dict | None = None) -> Any:
        async with self._limit:
            response = await self._http.request(method, path, json=json)
        if response.is_error:
            # Truncate: an Orchestrator error body can be long, and this text
            # may end up in a tool result the model reads.
            raise VcoApiError(response.status_code, path, response.text[:200])
        return response.json()