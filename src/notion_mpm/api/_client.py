"""Shared Notion HTTP client — connection-pooled, lifespan-managed."""

from __future__ import annotations

from typing import Any

import anyio
import httpx

NOTION_API_BASE = "https://api.notion.com/v1/"
NOTION_VERSION = "2022-06-28"


class NotionAPIError(Exception):
    """Raised when the Notion API returns an error response."""

    def __init__(self, endpoint: str, status: int, code: str, message: str) -> None:
        self.endpoint = endpoint
        self.status = status
        self.code = code
        self.message = message
        super().__init__(f"Notion API error on {endpoint} [{status}] {code}: {message}")


def _raise_for_notion_error(endpoint: str, data: dict[str, Any], status_code: int) -> None:
    """Raise NotionAPIError if the response indicates failure."""
    if data.get("object") == "error":
        raise NotionAPIError(
            endpoint=endpoint,
            status=status_code,
            code=data.get("code", "unknown_error"),
            message=data.get("message", "Unknown error"),
        )


class NotionClient:
    """Connection-pooled Notion HTTP client. One instance per application lifecycle.

    Use as an async context manager for proper resource cleanup, or call
    ``close()`` explicitly when done.

    Example::

        async with NotionClient(token) as client:
            page = await client.get("pages/abc123")

    Args:
        token: Notion integration token (``secret_...`` or ``ntn_...``).
        timeout: Request timeout in seconds (default 30).
        max_connections: Maximum total connections in the pool (default 10).
    """

    def __init__(
        self,
        token: str,
        *,
        timeout: float = 30.0,
        max_connections: int = 10,
    ) -> None:
        self._token = token
        self._client = httpx.AsyncClient(
            base_url=NOTION_API_BASE,
            headers={
                "Authorization": f"Bearer {token}",
                "Notion-Version": NOTION_VERSION,
                "Content-Type": "application/json",
            },
            timeout=timeout,
            limits=httpx.Limits(
                max_connections=max_connections,
                max_keepalive_connections=5,
            ),
        )

    # ------------------------------------------------------------------
    # Public HTTP verbs
    # ------------------------------------------------------------------

    async def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make a GET request to the Notion API."""
        return await self._request("GET", endpoint, params=params or {})

    async def post(self, endpoint: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make a POST request to the Notion API."""
        return await self._request("POST", endpoint, json=json or {})

    async def patch(self, endpoint: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        """Make a PATCH request to the Notion API."""
        return await self._request("PATCH", endpoint, json=json or {})

    async def delete(self, endpoint: str) -> dict[str, Any]:
        """Make a DELETE request to the Notion API."""
        return await self._request("DELETE", endpoint)

    async def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        await self._client.aclose()

    # ------------------------------------------------------------------
    # Async context manager support
    # ------------------------------------------------------------------

    async def __aenter__(self) -> NotionClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()

    # ------------------------------------------------------------------
    # Core request with 429 retry
    # ------------------------------------------------------------------

    async def _request(self, method: str, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        """Execute an HTTP request with automatic 429 retry.

        On HTTP 429 the response ``Retry-After`` header is honoured; the
        request is retried once.  All other non-error HTTP responses are
        parsed as JSON and checked for a Notion error envelope.
        """
        response = await self._client.request(method, endpoint, **kwargs)

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", "1"))
            await anyio.sleep(retry_after)
            response = await self._client.request(method, endpoint, **kwargs)

        data: dict[str, Any] = response.json()
        _raise_for_notion_error(endpoint, data, response.status_code)
        return data


# ---------------------------------------------------------------------------
# Legacy module-level helpers — kept for backwards compatibility.
# New code should use NotionClient directly.
# ---------------------------------------------------------------------------


async def notion_get(
    token: str,
    endpoint: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Make GET request to Notion API (backwards-compat wrapper)."""
    async with NotionClient(token) as client:
        return await client.get(endpoint, params=params)


async def notion_post(
    token: str,
    endpoint: str,
    json_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Make POST request to Notion API (backwards-compat wrapper)."""
    async with NotionClient(token) as client:
        return await client.post(endpoint, json=json_data)


async def notion_patch(
    token: str,
    endpoint: str,
    json_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Make PATCH request to Notion API (backwards-compat wrapper)."""
    async with NotionClient(token) as client:
        return await client.patch(endpoint, json=json_data)


async def notion_delete(
    token: str,
    endpoint: str,
) -> dict[str, Any]:
    """Make DELETE request to Notion API (backwards-compat wrapper)."""
    async with NotionClient(token) as client:
        return await client.delete(endpoint)
