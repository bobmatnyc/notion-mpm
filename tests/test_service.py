"""Tests for NotionService — all API calls mocked via NotionClient."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from notion_mpm.api._client import NotionClient
from notion_mpm.services.notion_service import NotionService


def _make_service(**overrides: Any) -> tuple[MagicMock, NotionService]:
    """Return a (mock_client, service) pair with all HTTP verbs mocked."""
    client = MagicMock(spec=NotionClient)
    client.get = AsyncMock(return_value=overrides.get("get", {"object": "page", "id": "p1"}))
    client.post = AsyncMock(return_value=overrides.get("post", {"object": "page", "id": "new"}))
    client.patch = AsyncMock(return_value=overrides.get("patch", {"object": "page", "id": "p1"}))
    client.delete = AsyncMock(
        return_value=overrides.get("delete", {"object": "block", "id": "b1", "archived": True})
    )
    return client, NotionService(client)


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_page() -> None:
    client, svc = _make_service(get={"object": "page", "id": "abc"})
    result = await svc.get_page("abc")
    client.get.assert_called_once_with("pages/abc")
    assert result["id"] == "abc"


@pytest.mark.asyncio
async def test_get_page_property_no_page_size() -> None:
    client, svc = _make_service(get={"object": "property_item"})
    await svc.get_page_property("pid", "prop1")
    client.get.assert_called_once_with("pages/pid/properties/prop1", params={})


@pytest.mark.asyncio
async def test_get_page_property_with_page_size() -> None:
    client, svc = _make_service(get={"object": "property_item"})
    await svc.get_page_property("pid", "prop1", page_size=5)
    client.get.assert_called_once_with("pages/pid/properties/prop1", params={"page_size": 5})


@pytest.mark.asyncio
async def test_create_page_minimal() -> None:
    client, svc = _make_service(post={"object": "page", "id": "new"})
    await svc.create_page({"database_id": "db1"}, {"Name": {}})
    client.post.assert_called_once_with(
        "pages",
        json={"parent": {"database_id": "db1"}, "properties": {"Name": {}}},
    )


@pytest.mark.asyncio
async def test_create_page_with_children() -> None:
    client, svc = _make_service(post={"object": "page", "id": "new"})
    children = [{"object": "block", "type": "paragraph"}]
    await svc.create_page({"page_id": "parent"}, {}, children=children)
    call_kwargs = client.post.call_args
    assert call_kwargs[1]["json"]["children"] == children


@pytest.mark.asyncio
async def test_archive_page() -> None:
    client, svc = _make_service(patch={"object": "page", "archived": True})
    await svc.archive_page("p1")
    client.patch.assert_called_once_with("pages/p1", json={"archived": True})


@pytest.mark.asyncio
async def test_restore_page() -> None:
    client, svc = _make_service(patch={"object": "page", "archived": False})
    await svc.restore_page("p1")
    client.patch.assert_called_once_with("pages/p1", json={"archived": False})


# ---------------------------------------------------------------------------
# Blocks
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_block() -> None:
    client, svc = _make_service(get={"object": "block", "id": "b1"})
    result = await svc.get_block("b1")
    client.get.assert_called_once_with("blocks/b1")
    assert result["id"] == "b1"


@pytest.mark.asyncio
async def test_get_block_children_defaults() -> None:
    client, svc = _make_service(get={"results": [], "has_more": False})
    await svc.get_block_children("b1")
    client.get.assert_called_once_with("blocks/b1/children", params={"page_size": 100})


@pytest.mark.asyncio
async def test_get_block_children_with_cursor() -> None:
    client, svc = _make_service(get={"results": [], "has_more": False})
    await svc.get_block_children("b1", start_cursor="cursor123")
    call_params = client.get.call_args[1]["params"]
    assert call_params["start_cursor"] == "cursor123"


@pytest.mark.asyncio
async def test_get_all_block_children_auto_paginates() -> None:
    """Should auto-paginate until has_more is False."""
    block_a = {"object": "block", "id": "a"}
    block_b = {"object": "block", "id": "b"}

    client = MagicMock(spec=NotionClient)
    client.get = AsyncMock(
        side_effect=[
            {"results": [block_a], "has_more": True, "next_cursor": "c1"},
            {"results": [block_b], "has_more": False},
        ]
    )
    svc = NotionService(client)
    results = await svc.get_all_block_children("root")

    assert len(results) == 2
    assert results[0]["id"] == "a"
    assert results[1]["id"] == "b"
    assert client.get.call_count == 2


@pytest.mark.asyncio
async def test_append_block_children() -> None:
    client, svc = _make_service(patch={"results": []})
    children = [{"type": "paragraph"}]
    await svc.append_block_children("b1", children)
    client.patch.assert_called_once_with("blocks/b1/children", json={"children": children})


@pytest.mark.asyncio
async def test_append_block_children_with_after() -> None:
    client, svc = _make_service(patch={"results": []})
    await svc.append_block_children("b1", [], after="prev_block")
    call_json = client.patch.call_args[1]["json"]
    assert call_json["after"] == "prev_block"


@pytest.mark.asyncio
async def test_update_block() -> None:
    client, svc = _make_service(patch={"object": "block"})
    block_data = {"paragraph": {"rich_text": []}}
    await svc.update_block("b1", block_data)
    client.patch.assert_called_once_with("blocks/b1", json=block_data)


@pytest.mark.asyncio
async def test_delete_block() -> None:
    client, svc = _make_service(delete={"object": "block", "archived": True})
    await svc.delete_block("b1")
    client.delete.assert_called_once_with("blocks/b1")


# ---------------------------------------------------------------------------
# Databases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_database() -> None:
    client, svc = _make_service(get={"object": "database", "id": "db1"})
    result = await svc.get_database("db1")
    client.get.assert_called_once_with("databases/db1")
    assert result["id"] == "db1"


@pytest.mark.asyncio
async def test_query_database_minimal() -> None:
    client, svc = _make_service(post={"results": [], "has_more": False})
    await svc.query_database("db1")
    client.post.assert_called_once_with("databases/db1/query", json={"page_size": 100})


@pytest.mark.asyncio
async def test_query_database_with_filter() -> None:
    client, svc = _make_service(post={"results": [], "has_more": False})
    flt = {"property": "Status", "select": {"equals": "Done"}}
    await svc.query_database("db1", filter=flt)
    call_json = client.post.call_args[1]["json"]
    assert call_json["filter"] == flt


@pytest.mark.asyncio
async def test_query_all_auto_paginates() -> None:
    page_a = {"object": "page", "id": "a"}
    page_b = {"object": "page", "id": "b"}

    client = MagicMock(spec=NotionClient)
    client.post = AsyncMock(
        side_effect=[
            {"results": [page_a], "has_more": True, "next_cursor": "c1"},
            {"results": [page_b], "has_more": False},
        ]
    )
    svc = NotionService(client)
    results = await svc.query_all("db1")

    assert len(results) == 2
    assert client.post.call_count == 2


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_users() -> None:
    client, svc = _make_service(get={"results": [], "has_more": False})
    await svc.list_users()
    client.get.assert_called_once_with("users", params={"page_size": 100})


@pytest.mark.asyncio
async def test_get_user() -> None:
    client, svc = _make_service(get={"object": "user", "id": "u1"})
    result = await svc.get_user("u1")
    client.get.assert_called_once_with("users/u1")
    assert result["id"] == "u1"


@pytest.mark.asyncio
async def test_get_bot_user() -> None:
    client, svc = _make_service(get={"object": "user", "id": "bot1"})
    await svc.get_bot_user()
    client.get.assert_called_once_with("users/me")


@pytest.mark.asyncio
async def test_list_all_users_auto_paginates() -> None:
    user_a = {"object": "user", "id": "a"}
    user_b = {"object": "user", "id": "b"}

    client = MagicMock(spec=NotionClient)
    client.get = AsyncMock(
        side_effect=[
            {"results": [user_a], "has_more": True, "next_cursor": "c1"},
            {"results": [user_b], "has_more": False},
        ]
    )
    svc = NotionService(client)
    results = await svc.list_all_users()

    assert len(results) == 2
    assert client.get.call_count == 2


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_search_empty_query() -> None:
    client, svc = _make_service(post={"results": []})
    await svc.search()
    call_json = client.post.call_args[1]["json"]
    # Empty query should not include "query" key
    assert "query" not in call_json


@pytest.mark.asyncio
async def test_search_with_query() -> None:
    client, svc = _make_service(post={"results": []})
    await svc.search("hello")
    call_json = client.post.call_args[1]["json"]
    assert call_json["query"] == "hello"


@pytest.mark.asyncio
async def test_search_with_filter() -> None:
    client, svc = _make_service(post={"results": []})
    flt = {"property": "object", "value": "page"}
    await svc.search(filter=flt)
    call_json = client.post.call_args[1]["json"]
    assert call_json["filter"] == flt


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_comments() -> None:
    client, svc = _make_service(get={"results": []})
    await svc.get_comments("block1")
    client.get.assert_called_once_with("comments", params={"block_id": "block1", "page_size": 100})


@pytest.mark.asyncio
async def test_create_comment_with_page_id() -> None:
    client, svc = _make_service(post={"object": "comment"})
    rich_text = [{"type": "text", "text": {"content": "hello"}}]
    await svc.create_comment(rich_text, page_id="page1")
    call_json = client.post.call_args[1]["json"]
    assert call_json["parent"] == {"type": "page_id", "page_id": "page1"}


@pytest.mark.asyncio
async def test_create_comment_requires_page_or_discussion() -> None:
    _, svc = _make_service()
    with pytest.raises(ValueError, match="page_id or discussion_id"):
        await svc.create_comment([])


@pytest.mark.asyncio
async def test_create_comment_with_discussion_id() -> None:
    client, svc = _make_service(post={"object": "comment"})
    await svc.create_comment([], discussion_id="disc1")
    call_json = client.post.call_args[1]["json"]
    assert call_json["discussion_id"] == "disc1"
