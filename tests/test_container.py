"""Tests for the DI container."""

from __future__ import annotations

import pytest

from notion_mpm.api._client import NotionClient
from notion_mpm.container import Container
from notion_mpm.services.notion_service import NotionService


def test_container_creates_client() -> None:
    """Container.client should return a NotionClient."""
    container = Container("secret_test_token")
    client = container.client
    assert isinstance(client, NotionClient)


def test_container_client_is_singleton() -> None:
    """Container.client should return the same instance on repeated access."""
    container = Container("secret_test_token")
    assert container.client is container.client


def test_container_creates_service() -> None:
    """Container.service should return a NotionService."""
    container = Container("secret_test_token")
    service = container.service
    assert isinstance(service, NotionService)


def test_container_service_is_singleton() -> None:
    """Container.service should return the same instance on repeated access."""
    container = Container("secret_test_token")
    assert container.service is container.service


def test_container_service_uses_shared_client() -> None:
    """NotionService in container should hold the same client as container.client."""
    container = Container("secret_test_token")
    assert container.service._client is container.client


@pytest.mark.asyncio
async def test_container_aclose_releases_client() -> None:
    """aclose() should close the client when it has been created."""
    container = Container("secret_test_token")
    # Trigger lazy creation
    _ = container.client
    # Should not raise; httpx connection pool closed cleanly
    await container.aclose()


@pytest.mark.asyncio
async def test_container_aclose_no_op_if_client_never_created() -> None:
    """aclose() should be a no-op when client was never accessed."""
    container = Container("secret_test_token")
    # client not accessed — aclose must not crash
    await container.aclose()


def test_create_container_missing_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """create_container() should raise ValueError when no token is configured."""
    from notion_mpm.auth.token_manager import TokenManager

    monkeypatch.setattr(
        TokenManager, "get_token", lambda self: (_ for _ in ()).throw(ValueError("No token"))
    )

    from notion_mpm.container import create_container

    with pytest.raises(ValueError):
        create_container()
