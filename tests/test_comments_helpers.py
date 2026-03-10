"""Tests for comment helper functions."""

from __future__ import annotations

import pytest

from notion_mpm.api.comments import create_comment, make_rich_text


def test_make_rich_text_plain() -> None:
    rt = make_rich_text("Hello comment")
    assert len(rt) == 1
    assert rt[0]["type"] == "text"
    assert rt[0]["text"]["content"] == "Hello comment"
    assert rt[0]["annotations"]["bold"] is False
    assert rt[0]["annotations"]["italic"] is False


def test_make_rich_text_bold() -> None:
    rt = make_rich_text("Bold", bold=True)
    assert rt[0]["annotations"]["bold"] is True


def test_make_rich_text_italic() -> None:
    rt = make_rich_text("Italic", italic=True)
    assert rt[0]["annotations"]["italic"] is True


@pytest.mark.asyncio
async def test_create_comment_requires_parent() -> None:
    """create_comment should raise if neither page_id nor discussion_id provided."""
    with pytest.raises(ValueError, match="Either page_id or discussion_id"):
        await create_comment("fake_token", make_rich_text("test"))
