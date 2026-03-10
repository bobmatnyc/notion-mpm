"""Notion Search API — search across pages and databases."""

from __future__ import annotations

from typing import Any

from notion_mpm.api._client import notion_post


async def search(
    token: str,
    query: str = "",
    *,
    filter: dict[str, Any] | None = None,  # noqa: A002
    sort: dict[str, Any] | None = None,
    start_cursor: str | None = None,
    page_size: int = 100,
) -> dict[str, Any]:
    """Search pages and databases in the workspace.

    The integration must have access to the content for it to appear in results.

    Args:
        token: Notion integration token.
        query: Text to search for. Empty string returns all accessible content.
        filter: Filter by object type. E.g.:
                {"property": "object", "value": "database"}
                {"property": "object", "value": "page"}
        sort: Sort order. E.g.:
              {"direction": "descending", "timestamp": "last_edited_time"}
        start_cursor: Pagination cursor from a previous response.
        page_size: Max results per page (max 100).

    Returns:
        Paginated list of page and database objects matching the query.
    """
    body: dict[str, Any] = {"page_size": page_size}
    if query:
        body["query"] = query
    if filter:
        body["filter"] = filter
    if sort:
        body["sort"] = sort
    if start_cursor:
        body["start_cursor"] = start_cursor
    return await notion_post(token, "search", json_data=body)


async def search_pages(
    token: str,
    query: str = "",
    *,
    sort_direction: str = "descending",
    page_size: int = 20,
) -> dict[str, Any]:
    """Convenience: search for pages only.

    Args:
        token: Notion integration token.
        query: Text to search for.
        sort_direction: "ascending" or "descending" by last_edited_time.
        page_size: Max results to return.

    Returns:
        Paginated list of page objects.
    """
    return await search(
        token,
        query,
        filter={"property": "object", "value": "page"},
        sort={"direction": sort_direction, "timestamp": "last_edited_time"},
        page_size=page_size,
    )


async def search_databases(
    token: str,
    query: str = "",
    *,
    page_size: int = 20,
) -> dict[str, Any]:
    """Convenience: search for databases only.

    Args:
        token: Notion integration token.
        query: Text to search for.
        page_size: Max results to return.

    Returns:
        Paginated list of database objects.
    """
    return await search(
        token,
        query,
        filter={"property": "object", "value": "database"},
        page_size=page_size,
    )
