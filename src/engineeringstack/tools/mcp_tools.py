"""Generic MCP Tool Discovery & LangChain Dynamic Adapter.

Converts MCP tool definitions discovered via `tools/list` into LangChain-compatible StructuredTools.
"""
import asyncio
import json
from typing import Any, Callable, List, Optional, Union
from langchain_core.tools import StructuredTool, tool
from langsmith import traceable
from .tools import _extract_mcp_result_text, _run_async_safely
from ..mcp.client import get_mcp_client
from ..mcp.registry import (
    add_server as _add_server,
    get_server_config as _get_server_config,
    list_servers as _list_servers,
    remove_server as _remove_server,
    global_registry,
)
from ..util.logger import get_logger

logger = get_logger(__name__)


def _parse_bool(val: Any) -> bool:
    """Parse bool or string representation of bool."""
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().lower() in ("true", "1", "yes", "y")
    return bool(val)


def _parse_dict(val: Any) -> dict[str, Any]:
    """Parse dict or json-string representation of dict."""
    if isinstance(val, dict):
        return val
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
    return {}


def _parse_list(val: Any) -> list[str]:
    """Parse list or string representation of list."""
    if isinstance(val, list):
        return [str(x) for x in val]
    if isinstance(val, str):
        val = val.strip()
        if val.startswith("[") and val.endswith("]"):
            try:
                parsed = json.loads(val)
                if isinstance(parsed, list):
                    return [str(x) for x in parsed]
            except Exception:
                pass
        return [val] if val else []
    return []


@tool
@traceable(name="register_mcp_server", run_type="tool")
def register_mcp_server(
    name: str,
    url: Optional[str] = None,
    transport: str = "http",
    command: Optional[str] = None,
    cli_args: Optional[Union[list[str], str]] = None,
    headers: Optional[Union[dict[str, str], str]] = None,
    env: Optional[Union[dict[str, str], str]] = None,
    persist: Union[bool, str] = True,
    **kwargs: Any,
) -> str:
    """Register and persist a Model Context Protocol (MCP) server configuration into mcp.json.
    
    Args:
        name: Unique identifier for the MCP server (e.g. 'postgres', 'weather', 'slack').
        url: Remote endpoint URL for HTTP or SSE transports (e.g. 'https://remote.mcpservers.org/try').
        transport: Transport protocol ('http', 'sse', or 'stdio'). Defaults to 'http'.
        command: Command executable for stdio transport (e.g. 'npx', 'python', 'docker').
        cli_args: Optional CLI arguments list or string for stdio command.
        headers: Optional HTTP headers dictionary or JSON string.
        env: Optional environment variables dictionary or JSON string for stdio transport.
        persist: Save to disk configuration file mcp.json (default True).
    """
    should_persist = _parse_bool(persist)
    resolved_headers = _parse_dict(headers)
    resolved_env = _parse_dict(env)
    raw_args = cli_args if cli_args is not None else kwargs.get("args")
    resolved_args = _parse_list(raw_args)

    logger.info(
        "[TOOL] register_mcp_server called: name=%s, url=%s, transport=%s, persist=%s",
        name,
        url,
        transport,
        should_persist,
    )

    config: dict[str, Any] = {}
    if command or transport == "stdio":
        config["type"] = "stdio"
        config["command"] = command or "npx"
        config["args"] = resolved_args
        if resolved_env:
            config["env"] = resolved_env
    elif url:
        config["type"] = transport or ("sse" if "/sse" in url else "http")
        config["url"] = url
        config["headers"] = resolved_headers
    else:
        return "Error: Either 'url' (for http/sse) or 'command' (for stdio) must be provided."

    try:
        normalized = global_registry.add_server(name, config, persist=should_persist)
        persist_msg = "and saved to mcp.json" if should_persist else "(in-memory only)"
        return (
            f"Successfully registered MCP server '{name}' {persist_msg}.\n"
            f"Configuration: {json.dumps(normalized, indent=2)}"
        )
    except Exception as exc:
        logger.error("[TOOL] register_mcp_server error: %s", exc)
        return f"Failed to register MCP server '{name}': {exc}"


@tool
@traceable(name="list_mcp_tools", run_type="tool")
def list_mcp_tools(server: str) -> str:
    """Connect to an MCP server and list all available tools provided by the server.
    
    Args:
        server: Server name (e.g. 'postgres', 'github', 'meniscus') or direct URL.
    """
    logger.info("[TOOL] list_mcp_tools called for server=%s", server)

    async def _fetch_tools():
        async with get_mcp_client(server, timeout=8.0) as session:
            res = await session.list_tools()
            tools_list = getattr(res, "tools", [])
            return tools_list

    try:
        tools = _run_async_safely(asyncio.wait_for(_fetch_tools(), timeout=10.0))
        if not tools:
            return f"Connected to MCP server '{server}', but no tools are exposed by this server."

        lines = [f"Connected to MCP server '{server}'. Found {len(tools)} available tool(s):"]
        for t in tools:
            t_name = getattr(t, "name", str(t))
            t_desc = getattr(t, "description", "") or "No description provided."
            lines.append(f"- `{t_name}`: {t_desc}")
        return "\n".join(lines)
    except Exception as exc:
        logger.warning("[TOOL] list_mcp_tools failed for server '%s': %s", server, exc)
        err_msg = str(exc)
        if "getaddrinfo failed" in err_msg or "ConnectError" in err_msg:
            return (
                f"Registered MCP server '{server}' in configuration, but could not connect to endpoint "
                f"(host unreachable or DNS lookup failed: {err_msg}). Please check the endpoint URL."
            )
        elif "Timeout" in err_msg or "timed out" in err_msg or isinstance(exc, asyncio.TimeoutError):
            return (
                f"Registered MCP server '{server}', but connection timed out after 10s. "
                f"The server may be starting up or currently unreachable."
            )
        return f"Unable to retrieve tools from MCP server '{server}': {err_msg}"


@tool
@traceable(name="list_registered_mcp_servers", run_type="tool")
def list_registered_mcp_servers() -> str:
    """List all currently registered MCP servers from mcp.json and runtime registry."""
    logger.info("[TOOL] list_registered_mcp_servers called")
    try:
        servers = global_registry.list_servers()
        if not servers:
            return "No MCP servers are currently registered."
        lines = [f"Registered MCP servers ({len(servers)}):"]
        for name, cfg in servers.items():
            transport = cfg.get("type", "unknown")
            endpoint = cfg.get("url") or cfg.get("command") or ""
            lines.append(f"- `{name}` [{transport}]: {endpoint}")
        return "\n".join(lines)
    except Exception as exc:
        logger.warning("[TOOL] list_registered_mcp_servers error: %s", exc)
        return f"Failed to list MCP servers: {exc}"


@tool
@traceable(name="remove_mcp_server", run_type="tool")
def remove_mcp_server(name: str, persist: Union[bool, str] = True) -> str:
    """Remove an MCP server from the registry and mcp.json configuration file.
    
    Args:
        name: Identifier of the MCP server to remove.
        persist: Whether to remove from disk mcp.json as well (default True).
    """
    should_persist = _parse_bool(persist)
    logger.info("[TOOL] remove_mcp_server called: name=%s, persist=%s", name, should_persist)
    try:
        removed = global_registry.remove_server(name, persist=should_persist)
        if removed:
            persist_msg = "and removed from mcp.json" if should_persist else ""
            return f"Successfully removed MCP server '{name}' {persist_msg}."
        return f"MCP server '{name}' was not found in registered servers."
    except Exception as exc:
        logger.error("[TOOL] remove_mcp_server error: %s", exc)
        return f"Failed to remove MCP server '{name}': {exc}"


def create_dynamic_mcp_tool(
    tool_name: str,
    description: str,
    server_name: str = "mcp",
    session: Optional[Any] = None,
    coroutine_caller: Optional[Callable] = None,
) -> StructuredTool:
    """Create a LangChain StructuredTool dynamically wrapping an MCP tool call.
    
    If no active session is provided, it dynamically connects to the server on-the-fly.
    
    Args:
        tool_name: Name of the tool on the MCP server.
        description: Description of the tool.
        server_name: MCP server namespace prefix.
        session: Optional active MCP ClientSession.
        coroutine_caller: Optional custom coroutine runner.
    """
    scoped_name = f"{server_name}_{tool_name}" if server_name and server_name != "custom" else tool_name

    async def _async_call(**kwargs: Any) -> str:
        logger.info("[MCP_TOOL] Calling '%s' (server: %s) with args: %s", tool_name, server_name, kwargs)
        try:
            if coroutine_caller:
                res = await coroutine_caller(tool_name, kwargs)
            elif session is not None:
                res = await session.call_tool(tool_name, kwargs)
            else:
                async with get_mcp_client(server_name, timeout=8.0) as client_session:
                    res = await client_session.call_tool(tool_name, kwargs)
            return _extract_mcp_result_text(res)
        except Exception as exc:
            logger.warning("[MCP_TOOL] Error calling '%s': %s", tool_name, exc)
            return f"[{server_name} MCP {tool_name} error: {exc}]"

    def _sync_call(**kwargs: Any) -> str:
        return _run_async_safely(_async_call(**kwargs))

    return StructuredTool.from_function(
        func=_sync_call,
        coroutine=_async_call,
        name=scoped_name,
        description=description or f"MCP tool {tool_name} from {server_name}",
    )


async def discover_and_adapt_mcp_tools(
    session: Any,
    server_name: str = "custom",
) -> List[StructuredTool]:
    """Dynamically discover tools from an active MCP session and adapt them to LangChain StructuredTools.
    
    Args:
        session: Initialized MCP ClientSession.
        server_name: Namespace prefix for tool naming.
        
    Returns:
        List of LangChain StructuredTool instances ready for agent binding.
    """
    logger.info("Discovering tools for MCP server '%s'", server_name)
    tools_list_response = await session.list_tools()
    tools_list = getattr(tools_list_response, "tools", [])

    adapted_tools = []
    for tool_def in tools_list:
        t_name = getattr(tool_def, "name", str(tool_def))
        t_desc = getattr(tool_def, "description", "") or f"MCP tool {t_name} from {server_name}"
        langchain_tool = create_dynamic_mcp_tool(
            tool_name=t_name,
            description=t_desc,
            server_name=server_name,
            session=session,
        )
        adapted_tools.append(langchain_tool)

    logger.info("Discovered %d tools for MCP server '%s'", len(adapted_tools), server_name)
    return adapted_tools


def load_server_tools(server_name: str) -> List[StructuredTool]:
    """Connect to a registered MCP server and dynamically discover its tools as LangChain StructuredTools."""
    async def _fetch():
        async with get_mcp_client(server_name, timeout=5.0) as session:
            return await discover_and_adapt_mcp_tools(session, server_name=server_name)

    try:
        return _run_async_safely(asyncio.wait_for(_fetch(), timeout=8.0))
    except Exception as exc:
        logger.warning("Could not dynamically load tools for MCP server '%s': %s", server_name, exc)
        # Return fallback dynamic execute tool for this server
        return [
            create_dynamic_mcp_tool(
                tool_name="execute",
                description=f"Execute query or operation against MCP server '{server_name}'.",
                server_name=server_name,
            )
        ]


def get_domain_mcp_tools(domain: str) -> List[StructuredTool]:
    """Automatically discover and aggregate MCP tools registered for a given domain from mcp.json/registry."""
    discovered: List[StructuredTool] = []
    try:
        servers = global_registry.list_servers()
        for s_name, s_cfg in servers.items():
            if s_name in ("github", "meniscus"):
                continue  # Handled by base standard tools
            s_domain = global_registry.classify_domain(
                s_name,
                description=s_cfg.get("url") or s_cfg.get("command"),
            )
            if s_domain == domain:
                tools = load_server_tools(s_name)
                discovered.extend(tools)
    except Exception as exc:
        logger.warning("Error fetching domain MCP tools for '%s': %s", domain, exc)
    return discovered
