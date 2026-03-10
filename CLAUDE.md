# Notion MPM - Project Context

## What This Is
Python MCP server + API library for Notion workspace integration.
Provides:
1. Clean Python API: `from notion_mpm.api import pages; await pages.get_page(token, page_id)`
2. MCP server: wraps the API for Claude Desktop (`uv run notion-mpm mcp`)
3. Agent scripts: standalone Python scripts in `agents/`

## Setup
```bash
cp .env.local.example .env.local
# Add NOTION_API_KEY=secret_...
uv sync
```

Create a Notion integration at: https://www.notion.so/my-integrations
Then share pages/databases with the integration from inside Notion.

## Run
```bash
uv run notion-mpm setup    # verify token + workspace connectivity
uv run notion-mpm doctor   # health check
uv run notion-mpm mcp      # start MCP server (for Claude Desktop)
```

## Test
```bash
uv run pytest
uv run pytest --cov=src --cov-report=html
```

## Architecture
```
src/notion_mpm/
├── api/              # Pure Notion API functions (library layer)
│   ├── _client.py        # Shared httpx client + NotionAPIError
│   ├── pages.py          # 6 page operations
│   ├── blocks.py         # 7 block operations + block builder helpers
│   ├── databases.py      # 5 database operations
│   ├── users.py          # 4 user operations
│   ├── search.py         # 3 search operations
│   └── comments.py       # 2 comment operations + rich_text helper
├── auth/             # Token management from .env/.env.local
├── cli/              # Click CLI commands
└── server/           # Thin MCP adapter over api/

agents/               # Standalone Python agent scripts
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

## Notion API Facts
- **Base URL**: `https://api.notion.com/v1`
- **Auth**: `Authorization: Bearer {token}` (internal integration token: `secret_...`)
- **Version header**: `Notion-Version: 2022-06-28` (ALWAYS required)
- **Rate limits**: 3 req/s per integration; retry on 429 with `Retry-After` header
- **IDs**: UUIDs, usable with or without dashes

## Key APIs Used
- `GET /pages/{id}` — retrieve page
- `POST /pages` — create page (in database or as sub-page)
- `PATCH /pages/{id}` — update page properties / archive
- `GET /blocks/{id}/children` — read page content
- `PATCH /blocks/{id}/children` — append blocks to page
- `PATCH /blocks/{id}` — update block
- `DELETE /blocks/{id}` — delete block
- `GET /databases/{id}` — retrieve database schema
- `POST /databases` — create database
- `POST /databases/{id}/query` — query with filter/sort
- `GET /users` — list workspace users
- `GET /users/me` — get bot user info (used for token validation)
- `POST /search` — search pages and databases
- `GET /comments?block_id={id}` — get page comments
- `POST /comments` — create comment

## Integration Capabilities Required
Set these in your Notion integration settings:
- Read content (required)
- Update content (required for write ops)
- Insert comments (required for create_comment)
- Read comments (required for get_comments)

## Important Patterns

### Token env loading (auto-searches up directory tree)
The `TokenManager` loads `.env.local` searching from CWD upward, then the
project root (inferred from `__file__`), then `~`. Stop on first `NOTION_API_KEY`.

### Error handling
All API calls raise `NotionAPIError` when `response["object"] == "error"`.
The MCP server catches these and returns text content with the error.

### Rate limiting
`_client.py` handles 429 automatically: checks `Retry-After` header, sleeps,
then retries once. Do not add additional retry logic elsewhere.

### Block helpers (blocks.py)
Convenience functions: `make_paragraph()`, `make_heading()`, `make_bulleted_item()`,
`make_numbered_item()`, `make_todo()`, `make_code()`. Use these when building
block lists for `append_block_children`.

### Pagination
All list endpoints return `has_more` + `next_cursor`. Helper functions
`query_all()` (databases) and `list_all_users()` (users) auto-paginate.
`get_all_block_children()` auto-paginates block children.

## Release Workflow
- Always use `make` scripts — never run `uv publish` or edit version files directly
- The Makefile handles: lint → test → version bump → build → publish → tag → GitHub release
- Use `make publish` for patch releases, `make publish-minor` / `make publish-major` as needed
- PYPI_TOKEN must be in `.env.local` or `../gworkspace-mcp/.env.local`

## Development Guidelines
- Python 3.10+ — use `X | Y` union syntax, NOT `Optional[X]` or `Union[X, Y]`
- All API functions are `async` — the MCP server and CLI use `asyncio.run()` / `anyio.run()`
- Type annotations are strict (`mypy --strict`) — run `make type-check` before committing
- Line length: 100 characters (ruff enforced)
- Always `from __future__ import annotations` in API/server modules
- Tests live in `tests/` — run `make test` before committing
- No secrets in code — tokens come from env only

## MPM Notes
- Release workflow: `make publish` (patch), `make publish-minor`, `make publish-major`
- PYPI_TOKEN resolved from `.env.local` then `../gworkspace-mcp/.env.local`
