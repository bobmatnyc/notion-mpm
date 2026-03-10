"""Notion MCP Server — thin MCP adapter over NotionService."""

from __future__ import annotations

import json
from typing import Any

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from notion_mpm.api._client import NotionAPIError
from notion_mpm.api.comments import make_rich_text
from notion_mpm.services.notion_service import NotionService


def _pick(args: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    """Return a subset of dict containing only the specified keys that are present."""
    return {k: v for k, v in args.items() if k in keys}


NOTION_TOOLS: list[types.Tool] = [
    # -------------------------------------------------------------------------
    # Page tools
    # -------------------------------------------------------------------------
    types.Tool(
        name="get_page",
        description="Retrieve a Notion page by its ID, including all properties.",
        inputSchema={
            "type": "object",
            "properties": {
                "page_id": {
                    "type": "string",
                    "description": "Page UUID (with or without dashes)",
                },
            },
            "required": ["page_id"],
        },
    ),
    types.Tool(
        name="get_page_property",
        description="Retrieve a specific property value from a Notion page.",
        inputSchema={
            "type": "object",
            "properties": {
                "page_id": {
                    "type": "string",
                    "description": "Page UUID",
                },
                "property_id": {
                    "type": "string",
                    "description": "Property ID or name to retrieve",
                },
                "page_size": {
                    "type": "integer",
                    "description": "Number of results for paginated properties",
                },
            },
            "required": ["page_id", "property_id"],
        },
    ),
    types.Tool(
        name="create_page",
        description=(
            "Create a new Notion page inside a database or as a sub-page of another page. "
            "For database pages, properties must match the database schema."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "parent": {
                    "type": "object",
                    "description": (
                        'Parent reference. Database: {"database_id": "..."}. '
                        'Page: {"page_id": "..."}'
                    ),
                },
                "properties": {
                    "type": "object",
                    "description": (
                        "Page properties matching the parent schema. "
                        "For a plain page: "
                        '{"title": {"title": [{"text": {"content": "My Title"}}]}}'
                    ),
                },
                "children": {
                    "type": "array",
                    "description": "Optional list of block objects to add as the page body",
                },
                "icon": {
                    "type": "object",
                    "description": 'Optional icon. E.g., {"type": "emoji", "emoji": "📄"}',
                },
                "cover": {
                    "type": "object",
                    "description": (
                        'Optional cover. E.g., {"type": "external", "external": {"url": "..."}}'
                    ),
                },
            },
            "required": ["parent", "properties"],
        },
    ),
    types.Tool(
        name="update_page",
        description="Update a Notion page's properties, icon, or cover image.",
        inputSchema={
            "type": "object",
            "properties": {
                "page_id": {
                    "type": "string",
                    "description": "Page UUID to update",
                },
                "properties": {
                    "type": "object",
                    "description": "Properties to update (partial update supported)",
                },
                "icon": {
                    "type": "object",
                    "description": "New icon object to set",
                },
                "cover": {
                    "type": "object",
                    "description": "New cover image object to set",
                },
            },
            "required": ["page_id"],
        },
    ),
    types.Tool(
        name="archive_page",
        description="Archive (soft-delete) a Notion page. The page can be restored later.",
        inputSchema={
            "type": "object",
            "properties": {
                "page_id": {
                    "type": "string",
                    "description": "Page UUID to archive",
                },
            },
            "required": ["page_id"],
        },
    ),
    types.Tool(
        name="restore_page",
        description="Restore a previously archived Notion page.",
        inputSchema={
            "type": "object",
            "properties": {
                "page_id": {
                    "type": "string",
                    "description": "Page UUID to restore",
                },
            },
            "required": ["page_id"],
        },
    ),
    # -------------------------------------------------------------------------
    # Block tools
    # -------------------------------------------------------------------------
    types.Tool(
        name="get_block",
        description="Retrieve a specific block by its ID.",
        inputSchema={
            "type": "object",
            "properties": {
                "block_id": {
                    "type": "string",
                    "description": "Block UUID",
                },
            },
            "required": ["block_id"],
        },
    ),
    types.Tool(
        name="get_block_children",
        description=(
            "List the direct children of a block or page. "
            "Use this to read the content of a Notion page."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "block_id": {
                    "type": "string",
                    "description": "Block or page UUID whose children to retrieve",
                },
                "page_size": {
                    "type": "integer",
                    "description": "Maximum number of blocks to return (max 100)",
                    "default": 100,
                },
                "start_cursor": {
                    "type": "string",
                    "description": "Pagination cursor from a previous response",
                },
            },
            "required": ["block_id"],
        },
    ),
    types.Tool(
        name="append_block_children",
        description=(
            "Append new content blocks to a page or block. "
            "Use this to add paragraphs, headings, lists, code blocks, and more."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "block_id": {
                    "type": "string",
                    "description": "Block or page UUID to append content to",
                },
                "children": {
                    "type": "array",
                    "description": "List of block objects to append",
                },
                "after": {
                    "type": "string",
                    "description": "Optional block ID — insert after this block instead of at end",
                },
            },
            "required": ["block_id", "children"],
        },
    ),
    types.Tool(
        name="update_block",
        description="Update the content of an existing block.",
        inputSchema={
            "type": "object",
            "properties": {
                "block_id": {
                    "type": "string",
                    "description": "Block UUID to update",
                },
                "block_data": {
                    "type": "object",
                    "description": (
                        "Dict with block type key and updated content. "
                        'E.g., {"paragraph": {"rich_text": [{"type": "text", '
                        '"text": {"content": "New text"}}]}}'
                    ),
                },
            },
            "required": ["block_id", "block_data"],
        },
    ),
    types.Tool(
        name="delete_block",
        description="Delete a block from a Notion page.",
        inputSchema={
            "type": "object",
            "properties": {
                "block_id": {
                    "type": "string",
                    "description": "Block UUID to delete",
                },
            },
            "required": ["block_id"],
        },
    ),
    # -------------------------------------------------------------------------
    # Database tools
    # -------------------------------------------------------------------------
    types.Tool(
        name="get_database",
        description="Retrieve a Notion database schema and metadata by its ID.",
        inputSchema={
            "type": "object",
            "properties": {
                "database_id": {
                    "type": "string",
                    "description": "Database UUID",
                },
            },
            "required": ["database_id"],
        },
    ),
    types.Tool(
        name="create_database",
        description=(
            "Create a new Notion database as a child of an existing page. "
            "Define the property schema (columns) at creation time."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "parent_page_id": {
                    "type": "string",
                    "description": "Page UUID to create the database under",
                },
                "title": {
                    "type": "string",
                    "description": "Database title text",
                },
                "properties": {
                    "type": "object",
                    "description": (
                        "Property schema. Must include a Name/title property. "
                        'E.g., {"Name": {"title": {}}, '
                        '"Status": {"select": {"options": [{"name": "Todo"}]}}}'
                    ),
                },
                "is_inline": {
                    "type": "boolean",
                    "description": "Create as an inline database inside the page",
                    "default": False,
                },
            },
            "required": ["parent_page_id", "title", "properties"],
        },
    ),
    types.Tool(
        name="update_database",
        description="Update a Notion database title, description, or property schema.",
        inputSchema={
            "type": "object",
            "properties": {
                "database_id": {
                    "type": "string",
                    "description": "Database UUID to update",
                },
                "title": {
                    "type": "string",
                    "description": "New title text",
                },
                "description": {
                    "type": "string",
                    "description": "New description text",
                },
                "properties": {
                    "type": "object",
                    "description": "Property schema updates (partial update supported)",
                },
            },
            "required": ["database_id"],
        },
    ),
    types.Tool(
        name="query_database",
        description=(
            "Query a Notion database to retrieve pages matching filter criteria. "
            "Supports filtering, sorting, and pagination."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "database_id": {
                    "type": "string",
                    "description": "Database UUID to query",
                },
                "filter": {
                    "type": "object",
                    "description": (
                        "Notion filter object. "
                        'E.g., {"property": "Status", "select": {"equals": "Done"}}'
                    ),
                },
                "sorts": {
                    "type": "array",
                    "description": (
                        "List of sort objects. "
                        'E.g., [{"property": "Name", "direction": "ascending"}]'
                    ),
                },
                "start_cursor": {
                    "type": "string",
                    "description": "Pagination cursor from a previous response",
                },
                "page_size": {
                    "type": "integer",
                    "description": "Maximum results to return (1-100)",
                    "default": 100,
                },
            },
            "required": ["database_id"],
        },
    ),
    # -------------------------------------------------------------------------
    # User tools
    # -------------------------------------------------------------------------
    types.Tool(
        name="list_users",
        description="List all users in the Notion workspace.",
        inputSchema={
            "type": "object",
            "properties": {
                "page_size": {
                    "type": "integer",
                    "description": "Maximum number of users to return (max 100)",
                    "default": 100,
                },
                "start_cursor": {
                    "type": "string",
                    "description": "Pagination cursor from a previous response",
                },
            },
        },
    ),
    types.Tool(
        name="get_user",
        description="Retrieve information about a specific Notion user.",
        inputSchema={
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "User UUID",
                },
            },
            "required": ["user_id"],
        },
    ),
    types.Tool(
        name="get_bot_user",
        description=(
            "Retrieve information about the bot user associated with this integration, "
            "including workspace name and owner details."
        ),
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
    # -------------------------------------------------------------------------
    # Search tools
    # -------------------------------------------------------------------------
    types.Tool(
        name="search",
        description=(
            "Search for pages and databases in the Notion workspace. "
            "Only returns content the integration has access to."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Text to search for. Empty string returns all accessible content."
                    ),
                    "default": "",
                },
                "filter_type": {
                    "type": "string",
                    "enum": ["page", "database"],
                    "description": "Filter results to only pages or only databases",
                },
                "sort_direction": {
                    "type": "string",
                    "enum": ["ascending", "descending"],
                    "description": "Sort by last_edited_time",
                    "default": "descending",
                },
                "page_size": {
                    "type": "integer",
                    "description": "Maximum results to return (max 100)",
                    "default": 20,
                },
                "start_cursor": {
                    "type": "string",
                    "description": "Pagination cursor from a previous response",
                },
            },
        },
    ),
    # -------------------------------------------------------------------------
    # Comment tools
    # -------------------------------------------------------------------------
    types.Tool(
        name="get_comments",
        description="Retrieve all comments on a Notion page or block.",
        inputSchema={
            "type": "object",
            "properties": {
                "block_id": {
                    "type": "string",
                    "description": "Page or block UUID to retrieve comments for",
                },
                "page_size": {
                    "type": "integer",
                    "description": "Maximum number of comments to return",
                    "default": 100,
                },
                "start_cursor": {
                    "type": "string",
                    "description": "Pagination cursor from a previous response",
                },
            },
            "required": ["block_id"],
        },
    ),
    types.Tool(
        name="create_comment",
        description=(
            "Add a comment to a Notion page. "
            "Requires 'insert comments' capability on the integration."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Comment text content",
                },
                "page_id": {
                    "type": "string",
                    "description": "Page UUID to add a top-level comment to",
                },
                "discussion_id": {
                    "type": "string",
                    "description": "Existing discussion ID to reply within",
                },
            },
            "required": ["text"],
        },
    ),
]


class NotionMCPServer:
    """Thin MCP adapter that exposes NotionService methods as MCP tools.

    Takes a ``NotionService`` instance via constructor injection — the server
    itself has no knowledge of tokens or HTTP clients.

    Args:
        service: A fully-configured ``NotionService`` instance.
    """

    def __init__(self, service: NotionService) -> None:
        self._service = service
        self.server: Server[Any, Any] = Server("notion-mpm")
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Register MCP tool handlers on the server."""

        @self.server.list_tools()  # type: ignore[no-untyped-call]
        async def list_tools() -> list[types.Tool]:
            return NOTION_TOOLS

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
            try:
                result = await self._dispatch_tool(name, arguments)
                return [types.TextContent(type="text", text=json.dumps(result, indent=2))]
            except NotionAPIError as e:
                return [
                    types.TextContent(type="text", text=f"Notion API error: {e.code} — {e.message}")
                ]
            except ValueError as e:
                return [types.TextContent(type="text", text=str(e))]

    async def _dispatch_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Route tool calls to the appropriate NotionService method.

        Args:
            name: Tool name to invoke.
            arguments: Arguments passed by the MCP client.

        Returns:
            Response from the Notion API.

        Raises:
            ValueError: If the tool name is not recognised.
            NotionAPIError: If the Notion API returns an error.
        """
        svc = self._service

        handlers: dict[str, Any] = {
            # Pages
            "get_page": lambda a: svc.get_page(a["page_id"]),
            "get_page_property": lambda a: svc.get_page_property(
                a["page_id"], a["property_id"], **_pick(a, ["page_size"])
            ),
            "create_page": lambda a: svc.create_page(
                a["parent"],
                a["properties"],
                **_pick(a, ["children", "icon", "cover"]),
            ),
            "update_page": lambda a: svc.update_page(
                a["page_id"], **_pick(a, ["properties", "icon", "cover"])
            ),
            "archive_page": lambda a: svc.archive_page(a["page_id"]),
            "restore_page": lambda a: svc.restore_page(a["page_id"]),
            # Blocks
            "get_block": lambda a: svc.get_block(a["block_id"]),
            "get_block_children": lambda a: svc.get_block_children(
                a["block_id"], **_pick(a, ["page_size", "start_cursor"])
            ),
            "append_block_children": lambda a: svc.append_block_children(
                a["block_id"], a["children"], **_pick(a, ["after"])
            ),
            "update_block": lambda a: svc.update_block(a["block_id"], a["block_data"]),
            "delete_block": lambda a: svc.delete_block(a["block_id"]),
            # Databases
            "get_database": lambda a: svc.get_database(a["database_id"]),
            "create_database": lambda a: svc.create_database(
                {"type": "page_id", "page_id": a["parent_page_id"]},
                [{"type": "text", "text": {"content": a["title"]}}],
                a["properties"],
                is_inline=a.get("is_inline", False),
            ),
            "update_database": lambda a: self._update_database(a),
            "query_database": lambda a: svc.query_database(
                a["database_id"],
                filter=a.get("filter"),
                sorts=a.get("sorts"),
                **_pick(a, ["start_cursor", "page_size"]),
            ),
            # Users
            "list_users": lambda a: svc.list_users(**_pick(a, ["page_size", "start_cursor"])),
            "get_user": lambda a: svc.get_user(a["user_id"]),
            "get_bot_user": lambda a: svc.get_bot_user(),
            # Search
            "search": lambda a: self._search(a),
            # Comments
            "get_comments": lambda a: svc.get_comments(
                a["block_id"], **_pick(a, ["page_size", "start_cursor"])
            ),
            "create_comment": lambda a: svc.create_comment(
                make_rich_text(a["text"]),
                page_id=a.get("page_id"),
                discussion_id=a.get("discussion_id"),
            ),
        }

        if name not in handlers:
            raise ValueError(f"Unknown tool: {name}")

        return await handlers[name](arguments)

    async def _search(self, args: dict[str, Any]) -> dict[str, Any]:
        """Build search call with optional type filter and sort."""
        filter_obj: dict[str, Any] | None = None
        if "filter_type" in args:
            filter_obj = {"property": "object", "value": args["filter_type"]}

        sort_obj: dict[str, Any] | None = None
        if "sort_direction" in args:
            sort_obj = {"direction": args["sort_direction"], "timestamp": "last_edited_time"}

        return await self._service.search(
            args.get("query", ""),
            filter=filter_obj,
            sort=sort_obj,
            start_cursor=args.get("start_cursor"),
            page_size=args.get("page_size", 20),
        )

    async def _update_database(self, args: dict[str, Any]) -> dict[str, Any]:
        """Build update_database call with optional rich text title/description."""
        kwargs: dict[str, Any] = {}
        if "title" in args:
            kwargs["title"] = [{"type": "text", "text": {"content": args["title"]}}]
        if "description" in args:
            kwargs["description"] = [{"type": "text", "text": {"content": args["description"]}}]
        if "properties" in args:
            kwargs["properties"] = args["properties"]
        return await self._service.update_database(args["database_id"], **kwargs)

    async def run(self, container: Any | None = None) -> None:
        """Run the MCP server over stdio.

        Args:
            container: Optional ``Container`` instance — if provided, its
                ``aclose()`` method is called when the server exits so that
                HTTP connections are released cleanly.
        """
        async with stdio_server() as (read_stream, write_stream):
            try:
                await self.server.run(
                    read_stream,
                    write_stream,
                    self.server.create_initialization_options(),
                )
            finally:
                if container is not None:
                    await container.aclose()
