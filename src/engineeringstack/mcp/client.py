"""Generic Model Context Protocol (MCP) Client.

Supports runtime dynamic connections via Streamable HTTP, SSE, and Stdio transports,
while preserving backwards compatibility for hardcoded integrations (e.g. GitHub).
"""

import asyncio
import json
import os
import shutil
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator, Optional, Union
import httpx
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamable_http_client
from mcp.client.stdio import stdio_client
from ..util.config import settings
from ..util.logger import get_logger
from .registry import get_server_config, global_registry

load_dotenv()
logger = get_logger(__name__)


def load_config():
    """Load configuration for GitHub MCP integration from dynamic registry."""
    cfg = get_server_config("github")
    if cfg:
        url = cfg.get("url", "https://api.githubcopilot.com/mcp/")
        headers = dict(cfg.get("headers", {}))
        token = settings.GITHUB_ACCESS_TOKEN or os.getenv("GITHUB_ACCESS_TOKEN") or "dummy_token"
        headers["Authorization"] = f"Bearer {token}"
        return url, headers

    # Default fallback
    url = "https://api.githubcopilot.com/mcp/"
    token = settings.GITHUB_ACCESS_TOKEN or os.getenv("GITHUB_ACCESS_TOKEN") or "dummy_token"
    return url, {"Authorization": f"Bearer {token}"}


def load_meniscus_config() -> dict[str, Any]:
    """Load configuration for Meniscus MCP integration from dynamic registry."""
    cfg = get_server_config("meniscus")
    if cfg:
        return cfg
    return {
        "type": "stdio",
        "command": "men-mcp",
        "args": [],
        "env": {
            "PYTHONUNBUFFERED": "1",
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUTF8": "1",
        },
    }


@asynccontextmanager
async def get_github_client() -> AsyncGenerator[ClientSession, None]:
    """Automated GitHub MCP client context manager."""
    async with get_mcp_client("github") as session:
        yield session


@asynccontextmanager
async def get_meniscus_client(timeout: float = 5.0) -> AsyncGenerator[ClientSession, None]:
    """Automated Meniscus MCP client context manager."""
    async with get_mcp_client("meniscus", timeout=timeout) as session:
        yield session


@asynccontextmanager
async def get_mcp_client(
    server: Union[str, dict[str, Any]],
    timeout: float = 5.0,
) -> AsyncGenerator[ClientSession, None]:
    """Generic MCP connection client supporting HTTP, SSE, and Stdio transports.
    
    Args:
        server: Server name (e.g. 'github', 'meniscus', 'postgres'), a URL string, or a config dictionary.
        timeout: Initialization timeout in seconds.
    """
    server_config: dict[str, Any] = {}

    if isinstance(server, str):
        # 1. Look up in registry
        resolved = get_server_config(server)
        if resolved is not None:
            server_config = resolved
        elif server.startswith("http://") or server.startswith("https://"):
            # 2. Treat directly as a URL
            server_config = global_registry.normalize_server_config(server)
        else:
            raise ValueError(f"MCP server '{server}' not found in registry and is not a valid URL.")
    elif isinstance(server, dict):
        server_config = global_registry.normalize_server_config(server)
    else:
        raise TypeError(f"Invalid server argument type: {type(server)}")

    transport = server_config.get("type", "http").lower()
    url = server_config.get("url", "")
    headers = dict(server_config.get("headers", {}))

    # Transport 1: Stdio local process
    if transport == "stdio" or "command" in server_config:
        raw_cmd = server_config.get("command", "")
        command = shutil.which(raw_cmd) or raw_cmd
        args = list(server_config.get("args", []))

        # Ensure npx runs non-interactively with -y
        if ("npx" in str(raw_cmd).lower() or "npx" in str(command).lower()) and "-y" not in args:
            args.insert(0, "-y")

        custom_env = server_config.get("env")
        if custom_env:
            full_env = dict(os.environ)
            full_env.update(custom_env)
        else:
            full_env = None
        logger.info("Connecting to MCP via Stdio: command=%s (raw=%s), args=%s", command, raw_cmd, args)

        params = StdioServerParameters(command=command, args=args, env=full_env)
        async with stdio_client(params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await asyncio.wait_for(session.initialize(), timeout=timeout)
                yield session

    # Transport 2: SSE remote connection
    elif transport == "sse" or "/sse" in url:
        logger.info("Connecting to MCP via SSE: url=%s", url)
        async with sse_client(url=url, headers=headers) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await asyncio.wait_for(session.initialize(), timeout=timeout)
                yield session

    # Transport 3: Streamable HTTP connection
    else:
        logger.info("Connecting to MCP via Streamable HTTP: url=%s", url)
        timeout_config = httpx.Timeout(timeout + 3.0, connect=timeout)
        async with httpx.AsyncClient(headers=headers, timeout=timeout_config) as http_client:
            async with streamable_http_client(url=url, http_client=http_client) as (
                read_stream,
                write_stream,
            ):
                async with ClientSession(read_stream, write_stream) as session:
                    await asyncio.wait_for(session.initialize(), timeout=timeout)
                    yield session
