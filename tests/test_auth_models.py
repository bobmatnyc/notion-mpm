"""Tests for Notion auth models."""

from __future__ import annotations

from notion_mpm.auth.models import NotionToken, TokenStatus


def test_token_mask_short() -> None:
    token = NotionToken(token="short", status=TokenStatus.VALID)
    assert token.mask() == "***"


def test_token_mask_long() -> None:
    token = NotionToken(token="secret_abc123def456ghi789", status=TokenStatus.VALID)
    masked = token.mask()
    assert masked.startswith("secret_")
    assert "..." in masked
    assert masked.endswith(token.token[-4:])


def test_is_internal_token_secret() -> None:
    token = NotionToken(token="secret_xyz", status=TokenStatus.VALID)
    assert token.is_internal_token() is True


def test_is_internal_token_ntn() -> None:
    token = NotionToken(token="ntn_abc123", status=TokenStatus.VALID)
    assert token.is_internal_token() is True


def test_is_internal_token_other() -> None:
    token = NotionToken(token="other_abc123", status=TokenStatus.VALID)
    assert token.is_internal_token() is False


def test_token_defaults() -> None:
    token = NotionToken(token="secret_test")
    assert token.status == TokenStatus.UNKNOWN
    assert token.bot_id is None
    assert token.workspace_name is None
