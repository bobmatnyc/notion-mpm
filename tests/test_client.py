"""Tests for NotionClient and legacy backwards-compat helpers."""

from __future__ import annotations

import httpx
import pytest

from notion_mpm.api._client import (
    NotionAPIError,
    NotionClient,
    _raise_for_notion_error,
    notion_delete,
    notion_get,
    notion_patch,
    notion_post,
)

# ---------------------------------------------------------------------------
# _raise_for_notion_error (unit — no HTTP)
# ---------------------------------------------------------------------------


def test_raise_for_notion_error_passes_on_ok() -> None:
    """Should not raise when response is a normal object."""
    data = {"object": "page", "id": "abc123"}
    _raise_for_notion_error("pages/abc123", data, 200)  # no exception


def test_raise_for_notion_error_raises_on_error() -> None:
    """Should raise NotionAPIError when response object is 'error'."""
    data = {
        "object": "error",
        "status": 404,
        "code": "object_not_found",
        "message": "Could not find page with ID: abc123",
    }
    with pytest.raises(NotionAPIError) as exc_info:
        _raise_for_notion_error("pages/abc123", data, 404)

    err = exc_info.value
    assert err.endpoint == "pages/abc123"
    assert err.status == 404
    assert err.code == "object_not_found"
    assert "Could not find page" in err.message


def test_notion_api_error_str() -> None:
    """Error __str__ should include endpoint, status, and message."""
    err = NotionAPIError("pages/x", 403, "restricted_resource", "Forbidden")
    assert "pages/x" in str(err)
    assert "403" in str(err)
    assert "restricted_resource" in str(err)


# ---------------------------------------------------------------------------
# NotionClient with mock transport
# ---------------------------------------------------------------------------


def _make_transport(responses: list[httpx.Response]) -> httpx.MockTransport:
    """Build an httpx MockTransport that serves responses in order."""
    iter_responses = iter(responses)

    def handler(request: httpx.Request) -> httpx.Response:
        return next(iter_responses)

    return httpx.MockTransport(handler)


def _json_response(data: dict, status: int = 200) -> httpx.Response:
    return httpx.Response(status, json=data)


@pytest.mark.asyncio
async def test_client_get_success() -> None:
    """GET request should return parsed JSON on 200."""
    transport = _make_transport([_json_response({"object": "page", "id": "p1"})])
    client = NotionClient.__new__(NotionClient)
    client._token = "secret_test"
    client._client = httpx.AsyncClient(base_url="https://api.notion.com/v1/", transport=transport)

    result = await client.get("pages/p1")
    assert result["id"] == "p1"
    await client.close()


@pytest.mark.asyncio
async def test_client_post_success() -> None:
    """POST request should return parsed JSON on 200."""
    transport = _make_transport([_json_response({"object": "page", "id": "new"})])
    client = NotionClient.__new__(NotionClient)
    client._token = "secret_test"
    client._client = httpx.AsyncClient(base_url="https://api.notion.com/v1/", transport=transport)

    result = await client.post("pages", json={"parent": {}, "properties": {}})
    assert result["id"] == "new"
    await client.close()


@pytest.mark.asyncio
async def test_client_patch_success() -> None:
    """PATCH request should return parsed JSON on 200."""
    transport = _make_transport([_json_response({"object": "page", "id": "p1", "archived": True})])
    client = NotionClient.__new__(NotionClient)
    client._token = "secret_test"
    client._client = httpx.AsyncClient(base_url="https://api.notion.com/v1/", transport=transport)

    result = await client.patch("pages/p1", json={"archived": True})
    assert result["archived"] is True
    await client.close()


@pytest.mark.asyncio
async def test_client_delete_success() -> None:
    """DELETE request should return parsed JSON on 200."""
    transport = _make_transport([_json_response({"object": "block", "id": "b1", "archived": True})])
    client = NotionClient.__new__(NotionClient)
    client._token = "secret_test"
    client._client = httpx.AsyncClient(base_url="https://api.notion.com/v1/", transport=transport)

    result = await client.delete("blocks/b1")
    assert result["archived"] is True
    await client.close()


@pytest.mark.asyncio
async def test_client_raises_notion_error() -> None:
    """Should raise NotionAPIError when API returns error envelope."""
    transport = _make_transport(
        [
            _json_response(
                {
                    "object": "error",
                    "status": 404,
                    "code": "object_not_found",
                    "message": "Not found",
                },
                status=404,
            )
        ]
    )
    client = NotionClient.__new__(NotionClient)
    client._token = "secret_test"
    client._client = httpx.AsyncClient(base_url="https://api.notion.com/v1/", transport=transport)

    with pytest.raises(NotionAPIError) as exc_info:
        await client.get("pages/missing")

    assert exc_info.value.code == "object_not_found"
    assert exc_info.value.status == 404
    await client.close()


@pytest.mark.asyncio
async def test_client_retries_on_429(monkeypatch: pytest.MonkeyPatch) -> None:
    """Should retry once after 429, honouring Retry-After header."""

    async def _noop_sleep(_: float) -> None:
        pass

    monkeypatch.setattr("anyio.sleep", _noop_sleep)

    responses = iter(
        [
            httpx.Response(429, json={}, headers={"Retry-After": "1"}),
            _json_response({"object": "page", "id": "p1"}),
        ]
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return next(responses)

    client = NotionClient.__new__(NotionClient)
    client._token = "secret_test"
    client._client = httpx.AsyncClient(
        base_url="https://api.notion.com/v1/",
        transport=httpx.MockTransport(handler),
    )

    result = await client.get("pages/p1")
    assert result["id"] == "p1"
    await client.close()


@pytest.mark.asyncio
async def test_client_context_manager() -> None:
    """Should work as an async context manager."""
    transport = _make_transport([_json_response({"object": "page", "id": "cm"})])

    # Build a real NotionClient but inject a mock transport
    client = NotionClient("secret_test")
    # Replace the internal httpx client with a mock-transport version
    await client._client.aclose()
    client._client = httpx.AsyncClient(base_url="https://api.notion.com/v1/", transport=transport)

    async with client as c:
        result = await c.get("pages/cm")

    assert result["id"] == "cm"


# ---------------------------------------------------------------------------
# Legacy backwards-compat wrappers
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_notion_get_compat(monkeypatch: pytest.MonkeyPatch) -> None:
    """notion_get should still work as a backwards-compat wrapper."""

    async def mock_get(self: NotionClient, endpoint: str, params: dict | None = None) -> dict:
        return {"object": "page", "id": "compat", "endpoint": endpoint}

    monkeypatch.setattr(NotionClient, "get", mock_get)
    result = await notion_get("secret_test", "pages/compat")
    assert result["id"] == "compat"


@pytest.mark.asyncio
async def test_notion_post_compat(monkeypatch: pytest.MonkeyPatch) -> None:
    """notion_post should still work as a backwards-compat wrapper."""

    async def mock_post(self: NotionClient, endpoint: str, json: dict | None = None) -> dict:
        return {"object": "page", "id": "post_compat"}

    monkeypatch.setattr(NotionClient, "post", mock_post)
    result = await notion_post("secret_test", "pages", json_data={})
    assert result["id"] == "post_compat"


@pytest.mark.asyncio
async def test_notion_patch_compat(monkeypatch: pytest.MonkeyPatch) -> None:
    """notion_patch should still work as a backwards-compat wrapper."""

    async def mock_patch(self: NotionClient, endpoint: str, json: dict | None = None) -> dict:
        return {"object": "page", "id": "patch_compat"}

    monkeypatch.setattr(NotionClient, "patch", mock_patch)
    result = await notion_patch("secret_test", "pages/p1", json_data={})
    assert result["id"] == "patch_compat"


@pytest.mark.asyncio
async def test_notion_delete_compat(monkeypatch: pytest.MonkeyPatch) -> None:
    """notion_delete should still work as a backwards-compat wrapper."""

    async def mock_delete(self: NotionClient, endpoint: str) -> dict:
        return {"object": "block", "id": "del_compat", "archived": True}

    monkeypatch.setattr(NotionClient, "delete", mock_delete)
    result = await notion_delete("secret_test", "blocks/b1")
    assert result["archived"] is True
