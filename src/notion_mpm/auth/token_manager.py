"""Token manager for Notion integration token lifecycle."""

import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

from notion_mpm.auth.models import NotionToken, TokenStatus

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def _load_env() -> None:
    """Load environment variables from .env and .env.local files.

    Searches multiple candidate directories in priority order so that the MCP
    server finds credentials regardless of the process working directory:

    1. Path.cwd() and each of its parents — preserves CLI / uv-run behaviour
       where the user invokes the command from inside the project tree.
    2. The project root inferred from this file's location — always resolves to
       the correct directory even when the process CWD is / or ~ (e.g. when
       Claude Desktop launches the MCP server as a GUI app).
       token_manager.py lives at src/notion_mpm/auth/token_manager.py, so
       Path(__file__).resolve().parents[3] is the project root.
    3. Path.home() — machine-wide fallback for users who place .env.local in
       their home directory.

    For each candidate directory, .env is loaded first (override=False) so
    existing environment variables take precedence, then .env.local is loaded
    with override=True so local secrets win over the shared base file.

    Search stops as soon as NOTION_API_KEY is present in os.environ.
    """
    candidates: list[Path] = []
    seen: set[Path] = set()

    def _add(directory: Path) -> None:
        resolved = directory.resolve()
        if resolved not in seen:
            seen.add(resolved)
            candidates.append(resolved)

    for ancestor in [Path.cwd(), *Path.cwd().parents]:
        _add(ancestor)

    _add(Path(__file__).resolve().parents[3])
    _add(Path.home())

    for directory in candidates:
        env_path = directory / ".env"
        if env_path.exists():
            load_dotenv(env_path, override=False)

        env_local_path = directory / ".env.local"
        if env_local_path.exists():
            load_dotenv(env_local_path, override=True)

        if os.environ.get("NOTION_API_KEY"):
            break


class TokenManager:
    """Manages Notion integration token loaded from environment variables."""

    def __init__(self) -> None:
        """Initialize token manager and load token from environment."""
        _load_env()
        self._token: str | None = os.environ.get("NOTION_API_KEY")

    @property
    def token(self) -> str | None:
        """Return the integration token if available."""
        return self._token

    def has_token(self) -> bool:
        """Return True if a token is configured."""
        return bool(self._token)

    def get_token(self) -> str:
        """Return the integration token.

        Returns:
            The token string.

        Raises:
            ValueError: If no token is configured.
        """
        if self._token:
            return self._token
        raise ValueError(
            "No Notion token found. Set NOTION_API_KEY in your environment, "
            ".env.local file, or in the MCP server's env config."
        )

    async def validate_token(self) -> NotionToken:
        """Validate the token by calling the Notion users/me endpoint.

        Returns:
            NotionToken with validation results.
        """
        if not self._token:
            return NotionToken(
                token="",  # nosec B106 — empty sentinel, not a hardcoded credential
                status=TokenStatus.MISSING,
            )

        notion_token = NotionToken(token=self._token)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{NOTION_API_BASE}/users/me",
                    headers={
                        "Authorization": f"Bearer {self._token}",
                        "Notion-Version": NOTION_VERSION,
                    },
                )
                data = response.json()

                if response.status_code == 200 and data.get("object") == "user":
                    notion_token.status = TokenStatus.VALID
                    notion_token.bot_id = data.get("id")
                    bot = data.get("bot", {})
                    workspace = bot.get("workspace_info", {}) if isinstance(bot, dict) else {}
                    notion_token.workspace_name = workspace.get("name")
                    notion_token.workspace_id = workspace.get("id")
                    notion_token.owner_type = (
                        bot.get("owner", {}).get("type") if isinstance(bot, dict) else None
                    )
                else:
                    notion_token.status = TokenStatus.INVALID

        except httpx.RequestError:
            notion_token.status = TokenStatus.UNKNOWN

        return notion_token
