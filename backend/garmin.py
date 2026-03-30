from contextlib import asynccontextmanager
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

from .config import settings


@asynccontextmanager
async def garmin_mcp_session(garmin_username: str, garmin_password: str):
    """
    Async context manager that starts garmin-connect-mcp as a subprocess
    and yields an active MCP ClientSession.

    Usage:
        async with garmin_mcp_session(username, password) as session:
            tools = await session.list_tools()
    """
    server_params = StdioServerParameters(
        command="node",
        args=[settings.garmin_mcp_path],
        env={
            "GARMIN_USERNAME": garmin_username,
            "GARMIN_PASSWORD": garmin_password,
            "PATH": "/usr/local/bin:/usr/bin:/bin",
        },
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session
