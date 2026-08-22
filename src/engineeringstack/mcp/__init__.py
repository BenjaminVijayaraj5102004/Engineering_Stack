"""MCP client and dynamic runtime registry integration for engineeringstack."""

from .client import (
    get_github_client,
    get_meniscus_client,
    get_mcp_client,
    load_config,
    load_meniscus_config,
)
from .registry import (
    MCPRegistry,
    add_server,
    classify_domain,
    get_server_config,
    global_registry,
    list_servers,
    load_mcp_config,
    remove_server,
    save_mcp_config,
)

__all__ = [
    "get_github_client",
    "get_meniscus_client",
    "get_mcp_client",
    "load_config",
    "load_meniscus_config",
    "MCPRegistry",
    "global_registry",
    "load_mcp_config",
    "save_mcp_config",
    "add_server",
    "remove_server",
    "get_server_config",
    "list_servers",
    "classify_domain",
]
