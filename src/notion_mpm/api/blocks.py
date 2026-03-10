"""Notion Blocks API — get, append, update, and delete blocks."""

from __future__ import annotations

from typing import Any

from notion_mpm.api._client import notion_delete, notion_get, notion_patch


async def get_block(token: str, block_id: str) -> dict[str, Any]:
    """Retrieve a specific block by ID.

    Args:
        token: Notion integration token.
        block_id: The block UUID.

    Returns:
        Block object from Notion API.
    """
    return await notion_get(token, f"blocks/{block_id}")


async def get_block_children(
    token: str,
    block_id: str,
    *,
    page_size: int = 100,
    start_cursor: str | None = None,
) -> dict[str, Any]:
    """List all children of a block (or page).

    Args:
        token: Notion integration token.
        block_id: The block or page UUID whose children to retrieve.
        page_size: Maximum number of blocks to return (max 100).
        start_cursor: Pagination cursor from a previous response.

    Returns:
        Paginated list of block objects.
    """
    params: dict[str, Any] = {"page_size": page_size}
    if start_cursor:
        params["start_cursor"] = start_cursor
    return await notion_get(token, f"blocks/{block_id}/children", params=params)


async def get_all_block_children(token: str, block_id: str) -> list[dict[str, Any]]:
    """Retrieve ALL children of a block, auto-paginating.

    Args:
        token: Notion integration token.
        block_id: The block or page UUID.

    Returns:
        Complete list of all child block objects.
    """
    results: list[dict[str, Any]] = []
    start_cursor: str | None = None

    while True:
        page = await get_block_children(token, block_id, page_size=100, start_cursor=start_cursor)
        results.extend(page.get("results", []))
        if not page.get("has_more"):
            break
        start_cursor = page.get("next_cursor")

    return results


async def append_block_children(
    token: str,
    block_id: str,
    children: list[dict[str, Any]],
    *,
    after: str | None = None,
) -> dict[str, Any]:
    """Append new children blocks to a block or page.

    Args:
        token: Notion integration token.
        block_id: The block or page UUID to append to.
        children: List of block objects to append.
        after: Optional block ID — append after this block instead of at the end.

    Returns:
        Object containing the list of newly created blocks.
    """
    body: dict[str, Any] = {"children": children}
    if after:
        body["after"] = after
    return await notion_patch(token, f"blocks/{block_id}/children", json_data=body)


async def update_block(
    token: str,
    block_id: str,
    block_data: dict[str, Any],
) -> dict[str, Any]:
    """Update a block's content.

    Args:
        token: Notion integration token.
        block_id: The block UUID to update.
        block_data: Dict with block type key and updated content.
                    E.g., ``{"paragraph": {"rich_text": [...]}}``

    Returns:
        Updated block object.
    """
    return await notion_patch(token, f"blocks/{block_id}", json_data=block_data)


async def delete_block(token: str, block_id: str) -> dict[str, Any]:
    """Delete (archive) a block.

    Args:
        token: Notion integration token.
        block_id: The block UUID to delete.

    Returns:
        Deleted block object.
    """
    return await notion_delete(token, f"blocks/{block_id}")


def make_paragraph(text: str, *, bold: bool = False, color: str = "default") -> dict[str, Any]:
    """Helper: create a paragraph block dict.

    Args:
        text: Plain text content.
        bold: Whether to bold the text.
        color: Text color name (Notion color tokens).

    Returns:
        Paragraph block object ready for append_block_children.
    """
    annotations: dict[str, Any] = {"bold": bold, "color": color}
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{"type": "text", "text": {"content": text}, "annotations": annotations}]
        },
    }


def make_heading(text: str, level: int = 1) -> dict[str, Any]:
    """Helper: create a heading block dict.

    Args:
        text: Heading text.
        level: Heading level 1, 2, or 3.

    Returns:
        Heading block object.
    """
    if level not in (1, 2, 3):
        raise ValueError("Heading level must be 1, 2, or 3")
    block_type = f"heading_{level}"
    return {
        "object": "block",
        "type": block_type,
        block_type: {"rich_text": [{"type": "text", "text": {"content": text}}]},
    }


def make_bulleted_item(text: str) -> dict[str, Any]:
    """Helper: create a bulleted list item block dict."""
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": text}}]},
    }


def make_numbered_item(text: str) -> dict[str, Any]:
    """Helper: create a numbered list item block dict."""
    return {
        "object": "block",
        "type": "numbered_list_item",
        "numbered_list_item": {"rich_text": [{"type": "text", "text": {"content": text}}]},
    }


def make_todo(text: str, *, checked: bool = False) -> dict[str, Any]:
    """Helper: create a to-do block dict."""
    return {
        "object": "block",
        "type": "to_do",
        "to_do": {
            "rich_text": [{"type": "text", "text": {"content": text}}],
            "checked": checked,
        },
    }


def make_code(code: str, language: str = "plain text") -> dict[str, Any]:
    """Helper: create a code block dict."""
    return {
        "object": "block",
        "type": "code",
        "code": {
            "rich_text": [{"type": "text", "text": {"content": code}}],
            "language": language,
        },
    }


async def get_block_tree(token: str, block_id: str, *, max_depth: int = 3) -> dict[str, Any]:
    """Recursively fetch a block and all its nested children up to max_depth.

    Args:
        token: Notion integration token.
        block_id: Root block UUID.
        max_depth: Maximum recursion depth (default 3 to avoid rate limits).

    Returns:
        Block object with nested "children" lists populated.
    """
    root = await notion_get(token, f"blocks/{block_id}")
    if max_depth > 0 and root.get("has_children"):
        children = await get_all_block_children(token, block_id)
        for child in children:
            if child.get("has_children"):
                child["children"] = (
                    await get_block_tree(token, child["id"], max_depth=max_depth - 1)
                ).get("children", [])
        root["children"] = children
    return root
