"""Notion Users API — list and retrieve workspace users."""

from __future__ import annotations

from typing import Any

from notion_mpm.api._client import notion_get


async def list_users(
    token: str,
    *,
    page_size: int = 100,
    start_cursor: str | None = None,
) -> dict[str, Any]:
    """List users in the workspace.

    Args:
        token: Notion integration token.
        page_size: Maximum number of users to return (max 100).
        start_cursor: Pagination cursor from a previous response.

    Returns:
        Paginated list of user objects.
    """
    params: dict[str, Any] = {"page_size": page_size}
    if start_cursor:
        params["start_cursor"] = start_cursor
    return await notion_get(token, "users", params=params)


async def list_all_users(token: str) -> list[dict[str, Any]]:
    """List ALL users in the workspace, auto-paginating.

    Args:
        token: Notion integration token.

    Returns:
        Complete list of all user objects.
    """
    results: list[dict[str, Any]] = []
    start_cursor: str | None = None

    while True:
        page = await list_users(token, page_size=100, start_cursor=start_cursor)
        results.extend(page.get("results", []))
        if not page.get("has_more"):
            break
        start_cursor = page.get("next_cursor")

    return results


async def get_user(token: str, user_id: str) -> dict[str, Any]:
    """Retrieve a specific user by ID.

    Args:
        token: Notion integration token.
        user_id: The user UUID.

    Returns:
        User object with name, avatar, and type.
    """
    return await notion_get(token, f"users/{user_id}")


async def get_bot_user(token: str) -> dict[str, Any]:
    """Retrieve information about the bot user associated with this integration.

    Args:
        token: Notion integration token.

    Returns:
        Bot user object including workspace info and owner.
    """
    return await notion_get(token, "users/me")
