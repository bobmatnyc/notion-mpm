"""Notion API submodules.

Each module exposes pure async functions that call the Notion REST API.
Import individual modules for use as a library:

    from notion_mpm.api import pages, databases, blocks
    result = await pages.get_page(token, page_id)
"""

from notion_mpm.api import blocks, comments, databases, pages, search, users

__all__ = ["pages", "blocks", "databases", "users", "search", "comments"]
