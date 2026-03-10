"""Notion Pages API — create, retrieve, update, and archive pages."""

from __future__ import annotations

from typing import Any

from notion_mpm.api._client import notion_get, notion_patch, notion_post


async def get_page(token: str, page_id: str) -> dict[str, Any]:
    """Retrieve a Notion page by ID.

    Args:
        token: Notion integration token.
        page_id: The page UUID (with or without dashes).

    Returns:
        Page object from Notion API.
    """
    return await notion_get(token, f"pages/{page_id}")


async def get_page_property(
    token: str,
    page_id: str,
    property_id: str,
    *,
    page_size: int | None = None,
) -> dict[str, Any]:
    """Retrieve a specific property from a page.

    Args:
        token: Notion integration token.
        page_id: The page UUID.
        property_id: The property ID or name.
        page_size: Number of results for paginated properties.

    Returns:
        Property item or paginated list of property items.
    """
    params: dict[str, Any] = {}
    if page_size is not None:
        params["page_size"] = page_size
    return await notion_get(token, f"pages/{page_id}/properties/{property_id}", params=params)


async def create_page(
    token: str,
    parent: dict[str, Any],
    properties: dict[str, Any],
    *,
    children: list[dict[str, Any]] | None = None,
    icon: dict[str, Any] | None = None,
    cover: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a new Notion page.

    Args:
        token: Notion integration token.
        parent: Parent reference. For a database: {"database_id": "..."},
                for a page: {"page_id": "..."}.
        properties: Page properties matching the parent database schema.
                    For a plain page parent, typically {"title": {...}}.
        children: Optional list of block objects to add as page body.
        icon: Optional icon object ({"type": "emoji", "emoji": "..."} or external).
        cover: Optional cover image ({"type": "external", "external": {"url": "..."}}).

    Returns:
        Created page object.
    """
    body: dict[str, Any] = {"parent": parent, "properties": properties}
    if children:
        body["children"] = children
    if icon:
        body["icon"] = icon
    if cover:
        body["cover"] = cover
    return await notion_post(token, "pages", json_data=body)


async def update_page(
    token: str,
    page_id: str,
    *,
    properties: dict[str, Any] | None = None,
    icon: dict[str, Any] | None = None,
    cover: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Update a Notion page's properties, icon, or cover.

    Args:
        token: Notion integration token.
        page_id: The page UUID.
        properties: Properties to update (partial update is supported).
        icon: New icon to set, or None to remove.
        cover: New cover to set, or None to remove.

    Returns:
        Updated page object.
    """
    body: dict[str, Any] = {}
    if properties is not None:
        body["properties"] = properties
    if icon is not None:
        body["icon"] = icon
    if cover is not None:
        body["cover"] = cover
    return await notion_patch(token, f"pages/{page_id}", json_data=body)


async def archive_page(token: str, page_id: str) -> dict[str, Any]:
    """Archive (soft-delete) a Notion page.

    Args:
        token: Notion integration token.
        page_id: The page UUID.

    Returns:
        Archived page object with archived=True.
    """
    return await notion_patch(token, f"pages/{page_id}", json_data={"archived": True})


async def restore_page(token: str, page_id: str) -> dict[str, Any]:
    """Restore an archived Notion page.

    Args:
        token: Notion integration token.
        page_id: The page UUID.

    Returns:
        Restored page object with archived=False.
    """
    return await notion_patch(token, f"pages/{page_id}", json_data={"archived": False})
