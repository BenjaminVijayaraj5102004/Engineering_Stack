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


def unwrap_mcp_error(exc: BaseException, server_name: str = "") -> Exception:
    """Extract and unwrap inner exceptions from ExceptionGroup / TaskGroup with clear diagnostic messaging."""
    errors = []

    def _collect(e: BaseException):
        if hasattr(e, "exceptions"):
            for sub in e.exceptions:
                _collect(sub)
        else:
            errors.append(e)

    _collect(exc)

    messages = []
    for err in errors:
        err_str = str(err)
        err_type = type(err).__name__
        if "401" in err_str or "Unauthorized" in err_str or "unauthorized" in err_str:
            messages.append("Authentication failed (HTTP 401 Unauthorized). Please check your API access token in .env.")
        elif "403" in err_str or "Forbidden" in err_str:
            messages.append("Access forbidden (HTTP 403 Forbidden). Access token lacks required permissions.")
        elif "404" in err_str or "Not Found" in err_str:
            messages.append("Resource or endpoint not found (HTTP 404). Check the MCP server URL.")
        elif "getaddrinfo failed" in err_str or "ConnectError" in err_str or "NameResolutionError" in err_str:
            messages.append(f"Network connection failed: {err_str}")
        elif "Timeout" in err_str or "timed out" in err_str or isinstance(err, asyncio.TimeoutError):
            messages.append("Connection timed out.")
        elif "Server returned an error response" in err_str:
            messages.append(f"Server returned an error response (authentication or parameter invalid). Please check access token in .env.")
        else:
            messages.append(f"{err_type}: {err_str}")

    prefix = f"MCP server '{server_name}' error: " if server_name else "MCP error: "
    combined_msg = prefix + "; ".join(messages) if messages else f"{prefix}{exc}"
    return RuntimeError(combined_msg)


def load_config():
    """Load configuration for GitHub MCP integration from dynamic registry."""
    cfg = get_server_config("github")
    if cfg:
        url = cfg.get("url", "https://api.githubcopilot.com/mcp/")
        headers = dict(cfg.get("headers", {}))
        token = os.getenv("GITHUB_ACCESS_TOKEN") or getattr(settings, "GITHUB_ACCESS_TOKEN", "") or ""
        if token and "Authorization" not in headers:
            headers["Authorization"] = f"Bearer {token}"
        return url, headers

    # Default fallback
    url = "https://api.githubcopilot.com/mcp/"
    token = os.getenv("GITHUB_ACCESS_TOKEN") or getattr(settings, "GITHUB_ACCESS_TOKEN", "") or ""
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return url, headers


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
        server: Server name (e.g. 'supabase', 'github', 'meniscus', 'postgres'), a URL string, or a config dictionary.
        timeout: Initialization timeout in seconds.
    """
    server_config: dict[str, Any] = {}
    server_name = server if isinstance(server, str) else "custom"

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
        server_name = server_config.get("name", "custom")
    else:
        raise TypeError(f"Invalid server argument type: {type(server)}")

    transport = server_config.get("type", "http").lower()
    url = server_config.get("url", "")
    headers = dict(server_config.get("headers", {}))

    # Clean headers and detect missing tokens (e.g. 'Bearer ' with no token)
    cleaned_headers: dict[str, str] = {}
    for k, v in headers.items():
        if isinstance(v, str):
            v_stripped = v.strip()
            if v_stripped in ("Bearer", "Bearer ", "bearer", "bearer "):
                raise ValueError(
                    f"MCP server '{server_name}' access token is missing. "
                    f"Please configure the required environment variable (e.g. SUPABASE_ACCESS_TOKEN) in your .env file or environment."
                )
            elif v_stripped:
                cleaned_headers[k] = v_stripped

    try:
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
            async with sse_client(url=url, headers=cleaned_headers) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await asyncio.wait_for(session.initialize(), timeout=timeout)
                    yield session

        # Transport 3: Streamable HTTP connection
        else:
            logger.info("Connecting to MCP via Streamable HTTP: url=%s", url)
            timeout_config = httpx.Timeout(timeout + 3.0, connect=timeout)
            async with httpx.AsyncClient(headers=cleaned_headers, timeout=timeout_config) as http_client:
                async with streamable_http_client(url=url, http_client=http_client) as (
                    read_stream,
                    write_stream,
                ):
                    async with ClientSession(read_stream, write_stream) as session:
                        await asyncio.wait_for(session.initialize(), timeout=timeout)
                        yield session
    except BaseException as exc:
        if isinstance(exc, (GeneratorExit, asyncio.CancelledError)):
            raise
        logger.warning("MCP connection to '%s' failed: %s", server_name, exc)
        raise unwrap_mcp_error(exc, server_name) from None
