"""Notion Databases API — create, retrieve, update, and query databases."""

from __future__ import annotations

from typing import Any

from notion_mpm.api._client import notion_get, notion_patch, notion_post


async def get_database(token: str, database_id: str) -> dict[str, Any]:
    """Retrieve a Notion database by ID.

    Args:
        token: Notion integration token.
        database_id: The database UUID.

    Returns:
        Database object including schema (properties).
    """
    return await notion_get(token, f"databases/{database_id}")


async def create_database(
    token: str,
    parent: dict[str, Any],
    title: list[dict[str, Any]],
    properties: dict[str, Any],
    *,
    icon: dict[str, Any] | None = None,
    cover: dict[str, Any] | None = None,
    is_inline: bool = False,
) -> dict[str, Any]:
    """Create a new Notion database.

    Args:
        token: Notion integration token.
        parent: Parent page reference: {"type": "page_id", "page_id": "..."}.
        title: Rich text array for the database title.
        properties: Property schema dict. Must include a "title" property.
        icon: Optional icon object.
        cover: Optional cover image object.
        is_inline: If True, create as an inline database inside a page.

    Returns:
        Created database object.
    """
    body: dict[str, Any] = {
        "parent": parent,
        "title": title,
        "properties": properties,
        "is_inline": is_inline,
    }
    if icon:
        body["icon"] = icon
    if cover:
        body["cover"] = cover
    return await notion_post(token, "databases", json_data=body)


async def update_database(
    token: str,
    database_id: str,
    *,
    title: list[dict[str, Any]] | None = None,
    description: list[dict[str, Any]] | None = None,
    properties: dict[str, Any] | None = None,
    icon: dict[str, Any] | None = None,
    cover: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Update a Notion database's schema or metadata.

    Args:
        token: Notion integration token.
        database_id: The database UUID.
        title: New rich text title.
        description: New rich text description.
        properties: Property schema updates (partial update supported).
        icon: New icon or None.
        cover: New cover or None.

    Returns:
        Updated database object.
    """
    body: dict[str, Any] = {}
    if title is not None:
        body["title"] = title
    if description is not None:
        body["description"] = description
    if properties is not None:
        body["properties"] = properties
    if icon is not None:
        body["icon"] = icon
    if cover is not None:
        body["cover"] = cover
    return await notion_patch(token, f"databases/{database_id}", json_data=body)


async def query_database(
    token: str,
    database_id: str,
    *,
    filter: dict[str, Any] | None = None,  # noqa: A002
    sorts: list[dict[str, Any]] | None = None,
    start_cursor: str | None = None,
    page_size: int = 100,
) -> dict[str, Any]:
    """Query a Notion database with optional filters and sorts.

    Args:
        token: Notion integration token.
        database_id: The database UUID.
        filter: Notion filter object. E.g.:
                {"property": "Status", "select": {"equals": "Done"}}
        sorts: List of sort objects. E.g.:
               [{"property": "Name", "direction": "ascending"}]
        start_cursor: Pagination cursor from a previous response.
        page_size: Max results to return (1–100, default 100).

    Returns:
        Paginated list of page objects matching the query.
    """
    body: dict[str, Any] = {"page_size": page_size}
    if filter:
        body["filter"] = filter
    if sorts:
        body["sorts"] = sorts
    if start_cursor:
        body["start_cursor"] = start_cursor
    return await notion_post(token, f"databases/{database_id}/query", json_data=body)


async def query_all(
    token: str,
    database_id: str,
    *,
    filter: dict[str, Any] | None = None,  # noqa: A002
    sorts: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Query ALL pages in a database, auto-paginating.

    Args:
        token: Notion integration token.
        database_id: The database UUID.
        filter: Optional Notion filter object.
        sorts: Optional list of sort objects.

    Returns:
        Complete list of all matching page objects.
    """
    results: list[dict[str, Any]] = []
    start_cursor: str | None = None

    while True:
        page = await query_database(
            token,
            database_id,
            filter=filter,
            sorts=sorts,
            start_cursor=start_cursor,
            page_size=100,
        )
        results.extend(page.get("results", []))
        if not page.get("has_more"):
            break
        start_cursor = page.get("next_cursor")

    return results
