"""Workspace summary agent — prints bot user info and top-level pages.

Usage::

    uv run python agents/workspace_summary.py

Requires ``NOTION_API_KEY`` in ``.env.local`` (or environment).
"""

from __future__ import annotations

import asyncio
from typing import Any

from notion_mpm.container import create_container


def _title_from_page(page: dict[str, Any]) -> str:
    """Extract the plain-text title from a page object."""
    props = page.get("properties", {})
    # Database pages: look for a property with type "title"
    for prop in props.values():
        if isinstance(prop, dict) and prop.get("type") == "title":
            rich_text = prop.get("title", [])
            if rich_text:
                return "".join(rt.get("plain_text", "") for rt in rich_text)
    # Top-level pages without a database parent use a "title" key directly
    title_prop = props.get("title", {})
    if isinstance(title_prop, dict):
        rich_text = title_prop.get("title", [])
        if rich_text:
            return "".join(rt.get("plain_text", "") for rt in rich_text)
    return "(untitled)"


async def main() -> None:
    container = create_container()
    try:
        svc = container.service

        # Bot user / workspace info
        bot = await svc.get_bot_user()
        bot_data = bot.get("bot", {})
        workspace = bot_data.get("workspace_info", {}) if isinstance(bot_data, dict) else {}
        print("Workspace Summary")
        print("=" * 50)
        print(f"Bot name    : {bot.get('name', 'unknown')}")
        print(f"Bot ID      : {bot.get('id', 'unknown')}")
        print(f"Workspace   : {workspace.get('name', 'unknown')}")
        print(f"Workspace ID: {workspace.get('id', 'unknown')}")
        print()

        # Top-level pages accessible to the integration
        result = await svc.search(
            "",
            filter={"property": "object", "value": "page"},
            sort={"direction": "descending", "timestamp": "last_edited_time"},
            page_size=20,
        )
        pages = result.get("results", [])
        print(f"Accessible pages ({len(pages)} shown):")
        for page in pages:
            page_id = page.get("id", "")
            title = _title_from_page(page)
            last_edited = page.get("last_edited_time", "")[:10]
            print(f"  [{last_edited}] {title}  ({page_id})")

        if result.get("has_more"):
            print("  ... (more pages available, use start_cursor to paginate)")

    finally:
        await container.aclose()


if __name__ == "__main__":
    asyncio.run(main())
