"""Shared Notion HTTP client."""

from __future__ import annotations

from typing import Any

import anyio
import httpx

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


class NotionAPIError(Exception):
    """Raised when the Notion API returns an error response."""

    def __init__(self, endpoint: str, status: int, code: str, message: str) -> None:
        self.endpoint = endpoint
        self.status = status
        self.code = code
        self.message = message
        super().__init__(f"Notion API error on {endpoint} [{status}] {code}: {message}")


def _headers(token: str) -> dict[str, str]:
    """Return standard Notion API headers."""
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def _raise_for_notion_error(endpoint: str, data: dict[str, Any], status_code: int) -> None:
    """Raise NotionAPIError if the response indicates failure."""
    if data.get("object") == "error":
        raise NotionAPIError(
            endpoint=endpoint,
            status=status_code,
            code=data.get("code", "unknown_error"),
            message=data.get("message", "Unknown error"),
        )


async def notion_get(
    token: str,
    endpoint: str,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Make GET request to Notion API.

    Args:
        token: Notion integration token (secret_...).
        endpoint: Notion API endpoint path (e.g., 'pages/abc123').
        params: Optional query parameters.

    Returns:
        Parsed JSON response from Notion.

    Raises:
        NotionAPIError: If Notion returns an error response.
    """
    url = f"{NOTION_API_BASE}/{endpoint}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=_headers(token), params=params or {})

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", "1"))
            await anyio.sleep(retry_after)
            response = await client.get(url, headers=_headers(token), params=params or {})

        data: dict[str, Any] = response.json()
        _raise_for_notion_error(endpoint, data, response.status_code)
        return data


async def notion_post(
    token: str,
    endpoint: str,
    json_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Make POST request to Notion API.

    Args:
        token: Notion integration token.
        endpoint: Notion API endpoint path.
        json_data: JSON body to send.

    Returns:
        Parsed JSON response from Notion.

    Raises:
        NotionAPIError: If Notion returns an error response.
    """
    url = f"{NOTION_API_BASE}/{endpoint}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, headers=_headers(token), json=json_data or {})

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", "1"))
            await anyio.sleep(retry_after)
            response = await client.post(url, headers=_headers(token), json=json_data or {})

        data: dict[str, Any] = response.json()
        _raise_for_notion_error(endpoint, data, response.status_code)
        return data


async def notion_patch(
    token: str,
    endpoint: str,
    json_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Make PATCH request to Notion API.

    Args:
        token: Notion integration token.
        endpoint: Notion API endpoint path.
        json_data: JSON body to send.

    Returns:
        Parsed JSON response from Notion.

    Raises:
        NotionAPIError: If Notion returns an error response.
    """
    url = f"{NOTION_API_BASE}/{endpoint}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.patch(url, headers=_headers(token), json=json_data or {})

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", "1"))
            await anyio.sleep(retry_after)
            response = await client.patch(url, headers=_headers(token), json=json_data or {})

        data: dict[str, Any] = response.json()
        _raise_for_notion_error(endpoint, data, response.status_code)
        return data


async def notion_delete(
    token: str,
    endpoint: str,
) -> dict[str, Any]:
    """Make DELETE request to Notion API.

    Args:
        token: Notion integration token.
        endpoint: Notion API endpoint path.

    Returns:
        Parsed JSON response from Notion.

    Raises:
        NotionAPIError: If Notion returns an error response.
    """
    url = f"{NOTION_API_BASE}/{endpoint}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.delete(url, headers=_headers(token))

        data: dict[str, Any] = response.json()
        _raise_for_notion_error(endpoint, data, response.status_code)
        return data
