"""High-level Notion service — SOA service layer over NotionClient."""

from __future__ import annotations

from typing import Any

from notion_mpm.api._client import NotionClient


class NotionService:
    """High-level Notion operations.

    All API calls go through the injected ``NotionClient``.  This class is the
    canonical implementation of every Notion operation used by the MCP server
    and CLI.  The module-level functions in ``api/`` are thin backwards-compat
    wrappers that create a short-lived client per call.

    Args:
        client: A shared, connection-pooled ``NotionClient`` instance.
    """

    def __init__(self, client: NotionClient) -> None:
        self._client = client

    # ------------------------------------------------------------------
    # Pages
    # ------------------------------------------------------------------

    async def get_page(self, page_id: str) -> dict[str, Any]:
        """Retrieve a Notion page by ID."""
        return await self._client.get(f"pages/{page_id}")

    async def get_page_property(
        self,
        page_id: str,
        property_id: str,
        *,
        page_size: int | None = None,
    ) -> dict[str, Any]:
        """Retrieve a specific property from a page."""
        params: dict[str, Any] = {}
        if page_size is not None:
            params["page_size"] = page_size
        return await self._client.get(f"pages/{page_id}/properties/{property_id}", params=params)

    async def create_page(
        self,
        parent: dict[str, Any],
        properties: dict[str, Any],
        *,
        children: list[dict[str, Any]] | None = None,
        icon: dict[str, Any] | None = None,
        cover: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new Notion page."""
        body: dict[str, Any] = {"parent": parent, "properties": properties}
        if children:
            body["children"] = children
        if icon:
            body["icon"] = icon
        if cover:
            body["cover"] = cover
        return await self._client.post("pages", json=body)

    async def update_page(
        self,
        page_id: str,
        *,
        properties: dict[str, Any] | None = None,
        icon: dict[str, Any] | None = None,
        cover: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Update a Notion page's properties, icon, or cover."""
        body: dict[str, Any] = {}
        if properties is not None:
            body["properties"] = properties
        if icon is not None:
            body["icon"] = icon
        if cover is not None:
            body["cover"] = cover
        return await self._client.patch(f"pages/{page_id}", json=body)

    async def archive_page(self, page_id: str) -> dict[str, Any]:
        """Archive (soft-delete) a Notion page."""
        return await self._client.patch(f"pages/{page_id}", json={"archived": True})

    async def restore_page(self, page_id: str) -> dict[str, Any]:
        """Restore an archived Notion page."""
        return await self._client.patch(f"pages/{page_id}", json={"archived": False})

    # ------------------------------------------------------------------
    # Blocks
    # ------------------------------------------------------------------

    async def get_block(self, block_id: str) -> dict[str, Any]:
        """Retrieve a specific block by ID."""
        return await self._client.get(f"blocks/{block_id}")

    async def get_block_children(
        self,
        block_id: str,
        *,
        page_size: int = 100,
        start_cursor: str | None = None,
    ) -> dict[str, Any]:
        """List the direct children of a block or page."""
        params: dict[str, Any] = {"page_size": page_size}
        if start_cursor:
            params["start_cursor"] = start_cursor
        return await self._client.get(f"blocks/{block_id}/children", params=params)

    async def get_all_block_children(self, block_id: str) -> list[dict[str, Any]]:
        """Retrieve ALL children of a block, auto-paginating."""
        results: list[dict[str, Any]] = []
        start_cursor: str | None = None

        while True:
            page = await self.get_block_children(block_id, page_size=100, start_cursor=start_cursor)
            results.extend(page.get("results", []))
            if not page.get("has_more"):
                break
            start_cursor = page.get("next_cursor")

        return results

    async def append_block_children(
        self,
        block_id: str,
        children: list[dict[str, Any]],
        *,
        after: str | None = None,
    ) -> dict[str, Any]:
        """Append new children blocks to a block or page."""
        body: dict[str, Any] = {"children": children}
        if after:
            body["after"] = after
        return await self._client.patch(f"blocks/{block_id}/children", json=body)

    async def update_block(self, block_id: str, block_data: dict[str, Any]) -> dict[str, Any]:
        """Update a block's content."""
        return await self._client.patch(f"blocks/{block_id}", json=block_data)

    async def delete_block(self, block_id: str) -> dict[str, Any]:
        """Delete (archive) a block."""
        return await self._client.delete(f"blocks/{block_id}")

    # ------------------------------------------------------------------
    # Databases
    # ------------------------------------------------------------------

    async def get_database(self, database_id: str) -> dict[str, Any]:
        """Retrieve a Notion database by ID."""
        return await self._client.get(f"databases/{database_id}")

    async def create_database(
        self,
        parent: dict[str, Any],
        title: list[dict[str, Any]],
        properties: dict[str, Any],
        *,
        icon: dict[str, Any] | None = None,
        cover: dict[str, Any] | None = None,
        is_inline: bool = False,
    ) -> dict[str, Any]:
        """Create a new Notion database."""
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
        return await self._client.post("databases", json=body)

    async def update_database(
        self,
        database_id: str,
        *,
        title: list[dict[str, Any]] | None = None,
        description: list[dict[str, Any]] | None = None,
        properties: dict[str, Any] | None = None,
        icon: dict[str, Any] | None = None,
        cover: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Update a Notion database's schema or metadata."""
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
        return await self._client.patch(f"databases/{database_id}", json=body)

    async def query_database(
        self,
        database_id: str,
        *,
        filter: dict[str, Any] | None = None,  # noqa: A002
        sorts: list[dict[str, Any]] | None = None,
        start_cursor: str | None = None,
        page_size: int = 100,
    ) -> dict[str, Any]:
        """Query a Notion database with optional filters and sorts."""
        body: dict[str, Any] = {"page_size": page_size}
        if filter:
            body["filter"] = filter
        if sorts:
            body["sorts"] = sorts
        if start_cursor:
            body["start_cursor"] = start_cursor
        return await self._client.post(f"databases/{database_id}/query", json=body)

    async def query_all(
        self,
        database_id: str,
        *,
        filter: dict[str, Any] | None = None,  # noqa: A002
        sorts: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """Query ALL pages in a database, auto-paginating."""
        results: list[dict[str, Any]] = []
        start_cursor: str | None = None

        while True:
            page = await self.query_database(
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

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

    async def list_users(
        self,
        *,
        page_size: int = 100,
        start_cursor: str | None = None,
    ) -> dict[str, Any]:
        """List users in the workspace."""
        params: dict[str, Any] = {"page_size": page_size}
        if start_cursor:
            params["start_cursor"] = start_cursor
        return await self._client.get("users", params=params)

    async def get_user(self, user_id: str) -> dict[str, Any]:
        """Retrieve a specific user by ID."""
        return await self._client.get(f"users/{user_id}")

    async def get_bot_user(self) -> dict[str, Any]:
        """Retrieve information about the bot user for this integration."""
        return await self._client.get("users/me")

    async def list_all_users(self) -> list[dict[str, Any]]:
        """List ALL users in the workspace, auto-paginating."""
        results: list[dict[str, Any]] = []
        start_cursor: str | None = None

        while True:
            page = await self.list_users(page_size=100, start_cursor=start_cursor)
            results.extend(page.get("results", []))
            if not page.get("has_more"):
                break
            start_cursor = page.get("next_cursor")

        return results

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    async def search(
        self,
        query: str = "",
        *,
        filter: dict[str, Any] | None = None,  # noqa: A002
        sort: dict[str, Any] | None = None,
        start_cursor: str | None = None,
        page_size: int = 100,
    ) -> dict[str, Any]:
        """Search pages and databases in the workspace."""
        body: dict[str, Any] = {"page_size": page_size}
        if query:
            body["query"] = query
        if filter:
            body["filter"] = filter
        if sort:
            body["sort"] = sort
        if start_cursor:
            body["start_cursor"] = start_cursor
        return await self._client.post("search", json=body)

    # ------------------------------------------------------------------
    # Comments
    # ------------------------------------------------------------------

    async def get_comments(
        self,
        block_id: str,
        *,
        page_size: int = 100,
        start_cursor: str | None = None,
    ) -> dict[str, Any]:
        """Retrieve comments on a page or block."""
        params: dict[str, Any] = {"block_id": block_id, "page_size": page_size}
        if start_cursor:
            params["start_cursor"] = start_cursor
        return await self._client.get("comments", params=params)

    async def create_comment(
        self,
        rich_text: list[dict[str, Any]],
        *,
        page_id: str | None = None,
        discussion_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a comment on a page or in an existing discussion thread."""
        if not page_id and not discussion_id:
            raise ValueError("Either page_id or discussion_id must be provided.")

        body: dict[str, Any] = {"rich_text": rich_text}
        if page_id:
            body["parent"] = {"type": "page_id", "page_id": page_id}
        if discussion_id:
            body["discussion_id"] = discussion_id

        return await self._client.post("comments", json=body)
