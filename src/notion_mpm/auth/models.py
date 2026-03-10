"""Pydantic models for Notion authentication."""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class TokenStatus(str, Enum):
    """Status of a Notion integration token."""

    VALID = "valid"
    INVALID = "invalid"
    MISSING = "missing"
    UNKNOWN = "unknown"


class NotionToken(BaseModel):
    """Represents a Notion API integration token with metadata."""

    model_config = ConfigDict(frozen=False)

    token: str = Field(..., description="The Notion integration token value")
    status: TokenStatus = Field(default=TokenStatus.UNKNOWN, description="Validation status")
    bot_id: str | None = Field(default=None, description="Bot user ID for the integration")
    workspace_id: str | None = Field(default=None, description="Workspace ID")
    workspace_name: str | None = Field(default=None, description="Workspace name")
    workspace_icon: str | None = Field(default=None, description="Workspace icon URL")
    owner_type: str | None = Field(default=None, description="Owner type: 'workspace' or 'user'")

    def is_internal_token(self) -> bool:
        """Return True if this looks like an internal integration token."""
        return self.token.startswith("secret_") or self.token.startswith("ntn_")

    def mask(self) -> str:
        """Return a masked version of the token for display."""
        if len(self.token) <= 12:
            return "***"
        return self.token[:8] + "..." + self.token[-4:]


class WorkspaceInfo(BaseModel):
    """Information about a Notion workspace."""

    workspace_id: str = Field(..., description="Workspace ID")
    workspace_name: str = Field(..., description="Workspace name")
    workspace_icon: str | None = Field(default=None, description="Workspace icon URL")
    bot_id: str | None = Field(default=None, description="Bot user ID")
    owner_type: str | None = Field(default=None, description="Owner type")
