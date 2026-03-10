# notion-mpm — Project Goals

## Vision

A production-quality Python MCP server and API library that makes Notion a
first-class tool for AI agents. Clean, well-typed, well-tested — the Notion
equivalent of slack-mpm.

---

## Phase 1: Foundation (scaffold — current)

**Status**: Complete

Goals:
- [x] Project scaffold mirroring slack-mpm conventions
- [x] `pyproject.toml`, `Makefile`, `VERSION`, `.gitignore`
- [x] `CLAUDE.md` with full project context for agentic development
- [x] Auth: `TokenManager` with multi-directory `.env.local` search
- [x] Auth: `NotionToken` / `WorkspaceInfo` Pydantic models
- [x] Client: `_client.py` with `notion_get`, `notion_post`, `notion_patch`, `notion_delete`
- [x] API modules: `pages`, `blocks`, `databases`, `users`, `search`, `comments`
- [x] Block helpers: `make_paragraph`, `make_heading`, `make_bulleted_item`, etc.
- [x] CLI: `setup`, `doctor`, `mcp` commands
- [x] MCP server: 20 tools across all 6 API domains
- [x] Tests: `test_client`, `test_blocks_helpers`, `test_auth_models`, `test_comments_helpers`
- [x] README with setup, API overview, and tool table
- [x] Public GitHub repo + initial commit

---

## Phase 2: Complete API Coverage

**Priority**: High — implement remaining Notion API surface

### Pages
- [ ] `get_page_property` — already scaffolded, add integration test
- [ ] Proper archived page listing (needs search filter)

### Blocks
- [ ] `get_block_tree` — recursive fetch (scaffolded, needs tests)
- [ ] Support all block types: callout, toggle, table, column_list, embed, bookmark, image, video, pdf, divider, equation, link_preview, synced_block, template, link_to_page, child_page, child_database
- [ ] Block type builder helpers for all above

### Databases
- [ ] Full filter spec support with compound filters (`and`, `or`)
- [ ] Rollup and formula property type support in schema
- [ ] `query_all` pagination helper — scaffolded, add tests

### Properties
- [ ] Dedicated `api/properties.py` module
- [ ] Rich property type builders: title, rich_text, number, select, multi_select, date, people, files, checkbox, url, email, phone_number, formula, relation, rollup, created_time, last_edited_time
- [ ] Helper: `make_title_property(text)`, `make_select_property(name)`, etc.

### Search
- [ ] Full-text search with all filter options
- [ ] Pagination helper: `search_all()`

### Users
- [ ] `list_all_users` — scaffolded, add tests

---

## Phase 3: Developer Experience

**Priority**: Medium — make the library pleasant to use

### Type Safety
- [ ] Typed TypedDict definitions for all Notion object types
- [ ] Property value TypedDicts for all property types
- [ ] Block content TypedDicts for all block types

### Rich API Helpers
- [ ] `NotionPage` helper class: `page.get_title()`, `page.get_property(name)`, etc.
- [ ] `NotionDatabase` helper class with schema introspection
- [ ] `RichText` builder: fluent API for constructing rich text arrays
- [ ] `BlockBuilder`: fluent page content construction

### Error Handling
- [ ] Specific exception subclasses: `NotionNotFoundError`, `NotionPermissionError`, `NotionRateLimitError`
- [ ] Better error messages with Notion documentation links

---

## Phase 4: Agent Scripts

**Priority**: Medium — practical automation examples

Scripts in `agents/`:
- [ ] `sync_to_notion.py` — sync markdown files to a Notion page tree
- [ ] `database_export.py` — export a Notion database to CSV/JSON
- [ ] `page_snapshot.py` — snapshot a page (blocks) to markdown
- [ ] `bulk_update.py` — update multiple database entries from a CSV
- [ ] `notion_to_markdown.py` — convert a Notion page to clean markdown

---

## Phase 5: MCP Enhancements

**Priority**: Medium — richer MCP tool surface

- [ ] Resources: expose pages as MCP resources (readable by URI)
- [ ] Resource templates: `notion://page/{page_id}`, `notion://database/{database_id}`
- [ ] Prompts: pre-built prompts for common Notion workflows
- [ ] Tool: `get_page_markdown` — return page content as clean markdown
- [ ] Tool: `create_page_from_markdown` — parse markdown and create blocks
- [ ] Tool: `duplicate_page` — clone a page with its content
- [ ] Tool: `move_page` — reparent a page to a new location

---

## Phase 6: Testing & Quality

**Priority**: Ongoing

- [ ] Integration test suite (with a real Notion test workspace)
- [ ] Mock fixtures for all API responses
- [ ] 90%+ unit test coverage on pure functions
- [ ] Property-based tests for block builders
- [ ] CI: GitHub Actions for lint + test on PRs
- [ ] Type coverage: 100% mypy strict

---

## Phase 7: Distribution

**Priority**: Low — after API is stable

- [ ] Publish to PyPI as `notion-mpm`
- [ ] GitHub Releases with auto-generated release notes
- [ ] Homebrew formula (via `homebrew-tools` tap)
- [ ] PyPI badge in README
- [ ] Auto-update skill for claude-mpm users

---

## Design Principles

1. **Library-first**: every MCP tool is a thin wrapper over a pure `async` API function
2. **Type-safe**: strict mypy, Pydantic models for all auth objects
3. **Conventions mirror slack-mpm**: same file layout, same CLI UX, same error handling
4. **No vendor lock-in**: the `api/` layer works independently of MCP
5. **Friendly errors**: `NotionAPIError` includes endpoint + code + message
6. **Auto-pagination helpers**: `query_all`, `list_all_users`, `get_all_block_children`
7. **Block helpers**: builder functions reduce boilerplate for common content creation

---

## Notion API Reference

- API docs: https://developers.notion.com/reference/intro
- Integrations: https://www.notion.so/my-integrations
- Block types: https://developers.notion.com/reference/block
- Filter reference: https://developers.notion.com/reference/post-database-query-filter
- Changelog: https://developers.notion.com/changelog
