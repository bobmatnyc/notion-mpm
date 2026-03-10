# notion-mpm

Python MCP server + API library for Notion workspace integration.

Provides:
1. **Clean Python API**: `from notion_mpm.api import pages; await pages.get_page(token, page_id)`
2. **MCP server**: wraps the API for Claude Desktop (`uv run notion-mpm mcp`)
3. **20+ tools**: pages, blocks, databases, users, search, comments

## Setup

```bash
cp .env.local.example .env.local
# Add NOTION_API_KEY=secret_...
uv sync
```

Create a Notion integration at: https://www.notion.so/my-integrations

Then share your pages/databases with the integration inside Notion.

## Run

```bash
uv run notion-mpm setup    # verify token + workspace
uv run notion-mpm doctor   # health check
uv run notion-mpm mcp      # start MCP server (for Claude Desktop)
```

## Test

```bash
uv run pytest
uv run pytest --cov=src --cov-report=html
```

## Claude Desktop Config

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "notion": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/notion-mpm", "notion-mpm", "mcp"]
    }
  }
}
```

## API Overview

```
src/notion_mpm/
├── api/
│   ├── _client.py      # Shared httpx client + NotionAPIError
│   ├── pages.py        # get, create, update, archive, restore pages
│   ├── blocks.py       # get, append, update, delete blocks + helpers
│   ├── databases.py    # get, create, update, query databases
│   ├── users.py        # list, get, get_bot_user
│   ├── search.py       # search pages and databases
│   └── comments.py     # get and create comments
├── auth/               # Token management from .env/.env.local
├── cli/                # Click CLI commands
└── server/             # Thin MCP adapter over api/
```

## MCP Tools

| Category  | Tools |
|-----------|-------|
| Pages     | `get_page`, `get_page_property`, `create_page`, `update_page`, `archive_page`, `restore_page` |
| Blocks    | `get_block`, `get_block_children`, `append_block_children`, `update_block`, `delete_block` |
| Databases | `get_database`, `create_database`, `update_database`, `query_database` |
| Users     | `list_users`, `get_user`, `get_bot_user` |
| Search    | `search` |
| Comments  | `get_comments`, `create_comment` |

## Token Scopes

Your integration needs these capabilities (set in Notion integration settings):

- **Read content** — required for all read operations
- **Update content** — required for create/update/archive
- **Insert comments** — required for `create_comment`
- **Read comments** — required for `get_comments`

## Release

```bash
make publish        # patch bump + PyPI + GitHub Release
make publish-minor  # minor bump
make publish-major  # major bump
```
