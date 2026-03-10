"""Tests for block helper functions."""

from __future__ import annotations

from notion_mpm.api.blocks import (
    make_bulleted_item,
    make_code,
    make_heading,
    make_paragraph,
    make_todo,
)


def test_make_paragraph_default() -> None:
    block = make_paragraph("Hello world")
    assert block["type"] == "paragraph"
    rt = block["paragraph"]["rich_text"][0]
    assert rt["text"]["content"] == "Hello world"
    assert rt["annotations"]["bold"] is False


def test_make_paragraph_bold() -> None:
    block = make_paragraph("Bold text", bold=True)
    assert block["paragraph"]["rich_text"][0]["annotations"]["bold"] is True


def test_make_heading_h1() -> None:
    block = make_heading("My Heading", level=1)
    assert block["type"] == "heading_1"
    assert block["heading_1"]["rich_text"][0]["text"]["content"] == "My Heading"


def test_make_heading_h2() -> None:
    block = make_heading("Sub", level=2)
    assert block["type"] == "heading_2"


def test_make_heading_h3() -> None:
    block = make_heading("Sub-sub", level=3)
    assert block["type"] == "heading_3"


def test_make_heading_invalid_level() -> None:
    import pytest

    with pytest.raises(ValueError, match="level must be 1, 2, or 3"):
        make_heading("Bad", level=4)


def test_make_bulleted_item() -> None:
    block = make_bulleted_item("Item one")
    assert block["type"] == "bulleted_list_item"
    assert block["bulleted_list_item"]["rich_text"][0]["text"]["content"] == "Item one"


def test_make_todo_unchecked() -> None:
    block = make_todo("Do this")
    assert block["type"] == "to_do"
    assert block["to_do"]["checked"] is False


def test_make_todo_checked() -> None:
    block = make_todo("Done", checked=True)
    assert block["to_do"]["checked"] is True


def test_make_code() -> None:
    block = make_code("print('hello')", "python")
    assert block["type"] == "code"
    assert block["code"]["language"] == "python"
    assert block["code"]["rich_text"][0]["text"]["content"] == "print('hello')"
