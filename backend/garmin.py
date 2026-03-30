import os
from contextlib import asynccontextmanager
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

from .config import settings


def session_exists(user_id: int) -> bool:
    """
    Return True if a saved garmin-connect-mcp session file exists for this user.
    The session is stored at GARMIN_HOME_DIR/{user_id}/.garmin-connect-mcp/session.json
    """
    session_file = (
        Path(settings.garmin_home_dir)
        / str(user_id)
        / ".garmin-connect-mcp"
        / "session.json"
    )
    return session_file.exists()


@asynccontextmanager
async def garmin_mcp_session(user_id: int):
    """
    Async context manager that starts garmin-connect-mcp as a subprocess
    with a per-user HOME directory and yields an active MCP ClientSession.

    garmin-connect-mcp loads its session from $HOME/.garmin-connect-mcp/session.json,
    so setting HOME to GARMIN_HOME_DIR/{user_id} gives each user an isolated session.

    Usage:
        async with garmin_mcp_session(user_id) as session:
            tools = await session.list_tools()
    """
    user_home = str(Path(settings.garmin_home_dir) / str(user_id))

    server_params = StdioServerParameters(
        command="node",
        args=[settings.garmin_mcp_path],
        env={
            **os.environ,
            "HOME": user_home,
            "PLAYWRIGHT_BROWSERS_PATH": settings.playwright_browsers_path,
        },
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session
