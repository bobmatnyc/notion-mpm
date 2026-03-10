"""Tests for the Notion API client helpers."""

from __future__ import annotations

import pytest

from notion_mpm.api._client import NotionAPIError, _raise_for_notion_error


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
