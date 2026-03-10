"""Search-and-read agent — searches pages matching a query, prints their content.

Usage::

    uv run python agents/search_and_read.py "my search query"
    uv run python agents/search_and_read.py          # lists all accessible pages

Requires ``NOTION_API_KEY`` in ``.env.local`` (or environment).
"""

from __future__ import annotations

import asyncio
import sys
from typing import Any

from notion_mpm.container import create_container


def _plain_text(rich_text_arr: list[dict[str, Any]]) -> str:
    """Flatten a Notion rich_text array to plain text."""
    return "".join(rt.get("plain_text", "") for rt in rich_text_arr)


def _title_from_page(page: dict[str, Any]) -> str:
    """Extract the plain-text title from a page object."""
    props = page.get("properties", {})
    for prop in props.values():
        if isinstance(prop, dict) and prop.get("type") == "title":
            return _plain_text(prop.get("title", []))
    return "(untitled)"


def _block_text(block: dict[str, Any]) -> str:
    """Extract readable text from a block for display."""
    block_type = block.get("type", "")
    content = block.get(block_type, {})
    rich_text = content.get("rich_text", [])
    text = _plain_text(rich_text)

    prefix_map = {
        "heading_1": "# ",
        "heading_2": "## ",
        "heading_3": "### ",
        "bulleted_list_item": "• ",
        "numbered_list_item": "1. ",
        "to_do": "[x] " if content.get("checked") else "[ ] ",
        "code": f"```{content.get('language', '')}\n",
    }
    suffix_map = {"code": "\n```"}

    prefix = prefix_map.get(block_type, "")
    suffix = suffix_map.get(block_type, "")
    return f"{prefix}{text}{suffix}" if text else ""


async def main(query: str) -> None:
    container = create_container()
    try:
        svc = container.service

        print(f"Searching for: {query!r}")
        print("=" * 50)

        result = await svc.search(
            query,
            filter={"property": "object", "value": "page"},
            sort={"direction": "descending", "timestamp": "last_edited_time"},
            page_size=10,
        )
        pages = result.get("results", [])

        if not pages:
            print("No pages found.")
            return

        print(f"Found {len(pages)} page(s):\n")

        for i, page in enumerate(pages, 1):
            page_id = page.get("id", "")
            title = _title_from_page(page)
            last_edited = page.get("last_edited_time", "")[:10]
            print(f"{i}. {title}")
            print(f"   ID: {page_id}  |  last edited: {last_edited}")

            # Read the first page's content as a demo
            if i == 1:
                print("\n   Content preview:")
                try:
                    children = await svc.get_all_block_children(page_id)
                    lines_shown = 0
                    for block in children:
                        line = _block_text(block)
                        if line:
                            print(f"   {line}")
                            lines_shown += 1
                        if lines_shown >= 10:
                            remaining = len(children) - lines_shown
                            if remaining > 0:
                                print(f"   ... ({remaining} more blocks)")
                            break
                    if lines_shown == 0:
                        print("   (no text content)")
                except Exception as exc:  # noqa: BLE001
                    print(f"   (could not read content: {exc})")
            print()

    finally:
        await container.aclose()


if __name__ == "__main__":
    search_query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    asyncio.run(main(search_query))
