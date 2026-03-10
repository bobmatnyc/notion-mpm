"""Notion Comments API — create and retrieve page/block comments."""

from __future__ import annotations

from typing import Any

from notion_mpm.api._client import notion_get, notion_post


async def get_comments(
    token: str,
    block_id: str,
    *,
    page_size: int = 100,
    start_cursor: str | None = None,
) -> dict[str, Any]:
    """Retrieve comments on a page or block.

    The integration must have "read comments" capability enabled.

    Args:
        token: Notion integration token.
        block_id: The page or block UUID to retrieve comments for.
        page_size: Max number of comments to return.
        start_cursor: Pagination cursor from a previous response.

    Returns:
        Paginated list of comment objects.
    """
    params: dict[str, Any] = {"block_id": block_id, "page_size": page_size}
    if start_cursor:
        params["start_cursor"] = start_cursor
    return await notion_get(token, "comments", params=params)


async def create_comment(
    token: str,
    rich_text: list[dict[str, Any]],
    *,
    page_id: str | None = None,
    discussion_id: str | None = None,
) -> dict[str, Any]:
    """Create a comment on a page or in an existing discussion thread.

    The integration must have "insert comments" capability enabled.
    Provide either page_id (to start a new discussion) or discussion_id
    (to reply to an existing thread).

    Args:
        token: Notion integration token.
        rich_text: Rich text array for the comment body.
        page_id: The page UUID to add a top-level comment to.
        discussion_id: Existing discussion ID to reply within.

    Returns:
        Created comment object.

    Raises:
        ValueError: If neither page_id nor discussion_id is provided.
    """
    if not page_id and not discussion_id:
        raise ValueError("Either page_id or discussion_id must be provided.")

    body: dict[str, Any] = {"rich_text": rich_text}
    if page_id:
        body["parent"] = {"type": "page_id", "page_id": page_id}
    if discussion_id:
        body["discussion_id"] = discussion_id

    return await notion_post(token, "comments", json_data=body)


def make_rich_text(text: str, *, bold: bool = False, italic: bool = False) -> list[dict[str, Any]]:
    """Helper: create a simple rich text array from a plain string.

    Args:
        text: Plain text content.
        bold: Apply bold annotation.
        italic: Apply italic annotation.

    Returns:
        Rich text array suitable for comment bodies and property values.
    """
    return [
        {
            "type": "text",
            "text": {"content": text},
            "annotations": {"bold": bold, "italic": italic},
        }
    ]
