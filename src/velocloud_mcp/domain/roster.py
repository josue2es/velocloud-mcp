"""In-memory roster of customers, with an age the caller can inspect."""

import asyncio
import time
from collections.abc import Awaitable, Callable

from velocloud_mcp.domain.customer import Customer, project_customer

_ONE_DAY = 86_400.0


class CustomerRoster:
    """Caches the projected customer list. Fetching is injected, so tests need no network."""

    def __init__(
        self,
        fetch_raw: Callable[[], Awaitable[list[dict]]],
        ttl_seconds: float = _ONE_DAY,
    ) -> None:
        self._fetch_raw = fetch_raw
        self._ttl_seconds = ttl_seconds
        self._customers: list[Customer] = []
        self._loaded_at: float | None = None
        self._loading: asyncio.Task | None = None

    @property
    def age_seconds(self) -> float | None:
        """Seconds since the last successful load, or None if never loaded."""
        return None if self._loaded_at is None else time.monotonic() - self._loaded_at

    @property
    def is_stale(self) -> bool:
        age = self.age_seconds
        return age is None or age > self._ttl_seconds

    async def customers(self, force_refresh: bool = False) -> list[Customer]:
        """Return the roster. Concurrent callers share one fetch rather than racing."""
        if force_refresh or self.is_stale:
            # Store the task before the first await, so coroutines that arrive
            # while it is running await this same fetch instead of starting another.
            if self._loading is None:
                self._loading = asyncio.create_task(self._load())
            try:
                await self._loading
            finally:
                self._loading = None
        return self._customers

    async def _load(self) -> None:
        """Fetch and project. Personal data never enters the cache."""
        self._customers = [project_customer(raw) for raw in await self._fetch_raw()]
        self._loaded_at = time.monotonic()