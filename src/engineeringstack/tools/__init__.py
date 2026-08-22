"""Internal tool definitions for engineeringstack."""

from .tools import (
    search_code,
    get_file_contents,
    meniscus_recall,
    meniscus_log,
    search_knowledge_base,
    set_active_store,
    get_active_store,
    get_domain_tools,
)
from .mcp_tools import (
    register_mcp_server,
    list_mcp_tools,
    list_registered_mcp_servers,
    remove_mcp_server,
    create_dynamic_mcp_tool,
    discover_and_adapt_mcp_tools,
    load_server_tools,
    get_domain_mcp_tools,
)

__all__ = [
    "search_code",
    "get_file_contents",
    "meniscus_recall",
    "meniscus_log",
    "search_knowledge_base",
    "set_active_store",
    "get_active_store",
    "get_domain_tools",
    "register_mcp_server",
    "list_mcp_tools",
    "list_registered_mcp_servers",
    "remove_mcp_server",
    "create_dynamic_mcp_tool",
    "discover_and_adapt_mcp_tools",
    "load_server_tools",
    "get_domain_mcp_tools",
]
