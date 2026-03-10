"""CLI entry points for Notion MCP server."""

import asyncio
import sys

import click

from notion_mpm.__version__ import __version__
from notion_mpm.auth.token_manager import TokenManager


@click.group()
@click.version_option(version=__version__, prog_name="notion-mpm")
def main() -> None:
    """Notion MCP Server - Notion workspace integration via Model Context Protocol."""


@main.command()
def setup() -> None:
    """Verify Notion token configuration and workspace connectivity."""
    click.echo("Notion MCP Setup")
    click.echo("=" * 50)

    manager = TokenManager()

    if not manager.has_token():
        click.echo(click.style("ERROR: NOTION_API_KEY is not set.", fg="red"))
        click.echo()
        click.echo("To fix this:")
        click.echo("  1. Copy .env.local.example to .env.local")
        click.echo("  2. Add your integration token: NOTION_API_KEY=secret_...")
        click.echo()
        click.echo("Create an integration at: https://www.notion.so/my-integrations")
        sys.exit(1)

    click.echo(f"Integration token found: {_mask_token(manager.token or '')}")

    click.echo()
    click.echo("Validating token with Notion API...")

    async def _validate() -> None:
        result = await manager.validate_token()
        if result.status.value == "valid":
            click.echo(click.style("Token: VALID", fg="green"))
            if result.workspace_name:
                click.echo(f"  Workspace: {result.workspace_name}")
            if result.workspace_id:
                click.echo(f"  Workspace ID: {result.workspace_id}")
            if result.bot_id:
                click.echo(f"  Bot User ID: {result.bot_id}")
            if result.owner_type:
                click.echo(f"  Owner type: {result.owner_type}")
        else:
            click.echo(click.style(f"Token: INVALID ({result.status.value})", fg="red"))
            click.echo()
            click.echo("Make sure your integration token is correct and has not expired.")
            click.echo("Verify at: https://www.notion.so/my-integrations")
            sys.exit(1)

    asyncio.run(_validate())

    click.echo()
    click.echo(
        click.style("Setup complete! Run 'notion-mpm mcp' to start the MCP server.", fg="green")
    )


@main.command()
def doctor() -> None:
    """Check Notion MCP installation health and configuration status."""
    click.echo("Notion MCP Doctor")
    click.echo("=" * 50)

    # Check Python version
    py_version = sys.version_info
    py_ok = py_version >= (3, 10)
    py_status = click.style("OK", fg="green") if py_ok else click.style("FAIL", fg="red")
    click.echo(f"Python version {py_version.major}.{py_version.minor}: [{py_status}]")

    if not py_ok:
        click.echo(click.style("  Requires Python 3.10+", fg="red"))

    # Check dependencies
    click.echo()
    click.echo("Checking dependencies...")

    deps = {
        "mcp": "mcp",
        "click": "click",
        "pydantic": "pydantic",
        "httpx": "httpx",
        "dotenv": "dotenv",
        "anyio": "anyio",
    }

    all_deps_ok = True
    for name, module in deps.items():
        try:
            __import__(module)
            click.echo(f"  {name}: [{click.style('OK', fg='green')}]")
        except ImportError:
            click.echo(f"  {name}: [{click.style('MISSING', fg='red')}]")
            all_deps_ok = False

    if not all_deps_ok:
        click.echo(click.style("\nRun 'uv sync' to install missing dependencies.", fg="yellow"))

    # Check token configuration
    click.echo()
    click.echo("Checking token configuration...")

    manager = TokenManager()

    if manager.has_token():
        click.echo(
            f"  NOTION_API_KEY: [{click.style('SET', fg='green')}] "
            f"({_mask_token(manager.token or '')})"
        )
    else:
        click.echo(f"  NOTION_API_KEY: [{click.style('MISSING', fg='red')}] (required)")

    # Token validation
    if manager.has_token():
        click.echo()
        click.echo("Validating token...")

        async def _check_token() -> None:
            result = await manager.validate_token()
            if result.status.value == "valid":
                workspace = result.workspace_name or "unknown"
                click.echo(
                    f"  Notion API (users/me): [{click.style('PASS', fg='green')}] "
                    f"(workspace: {workspace})"
                )
            else:
                click.echo(
                    f"  Notion API (users/me): [{click.style('FAIL', fg='red')}] "
                    f"(status: {result.status.value})"
                )

        asyncio.run(_check_token())

    click.echo()
    if manager.has_token() and all_deps_ok and py_ok:
        click.echo(click.style("All checks passed! Ready to run.", fg="green"))
    else:
        click.echo(click.style("Some checks failed. See above for details.", fg="yellow"))


@main.command(name="mcp")
def mcp_server() -> None:
    """Start the Notion MCP server in stdio mode for use with Claude Desktop."""
    import anyio

    from notion_mpm.container import create_container
    from notion_mpm.server.notion_mcp_server import NotionMCPServer

    container = create_container()
    server = NotionMCPServer(container.service)

    anyio.run(server.run, container)


def _mask_token(token: str) -> str:
    """Return a masked version of a token for display."""
    if not token or len(token) <= 12:
        return "***"
    return token[:8] + "..." + token[-4:]


if __name__ == "__main__":
    main()
