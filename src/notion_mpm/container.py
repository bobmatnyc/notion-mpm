"""Dependency injection container — wires all services together."""

from __future__ import annotations

from functools import cached_property

from notion_mpm.api._client import NotionClient
from notion_mpm.services.notion_service import NotionService


class Container:
    """DI container that manages the lifecycle of shared service instances.

    ``NotionClient`` and ``NotionService`` are created lazily on first access
    and reused for the lifetime of the container.  Call ``aclose()`` when the
    application shuts down to release HTTP connections.

    Example::

        container = create_container()
        try:
            service = container.service
            result = await service.get_bot_user()
        finally:
            await container.aclose()

    Args:
        token: Notion integration token (``secret_...`` or ``ntn_...``).
    """

    def __init__(self, token: str) -> None:
        self._token = token

    @cached_property
    def client(self) -> NotionClient:
        """Shared, connection-pooled HTTP client."""
        return NotionClient(self._token)

    @cached_property
    def service(self) -> NotionService:
        """High-level Notion service backed by the shared client."""
        return NotionService(self.client)

    async def aclose(self) -> None:
        """Close the HTTP connection pool if the client was created."""
        if "client" in self.__dict__:
            await self.client.close()


def create_container() -> Container:
    """Create a ``Container`` from the environment.

    Loads the ``NOTION_API_KEY`` via ``TokenManager`` (which searches CWD,
    project root, and ``~`` for ``.env.local``).

    Returns:
        A ready-to-use ``Container`` instance.

    Raises:
        ValueError: If no token is found in the environment.
    """
    from notion_mpm.auth.token_manager import TokenManager

    token = TokenManager().get_token()
    return Container(token)
