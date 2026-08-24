"""MCP Subagent Implementation for Engineering Stack.

Executes custom or generic Model Context Protocol (MCP) server tools, queries,
and unclassified domain operations delegated by MCP_Manager or executed standalone.
"""

from typing import Any, Optional
from deepagents import create_deep_agent
from ...builders.backend import build_default_backend
from ...models.ai_model import build_chat_model
from ...tools.tools import get_domain_tools, search_code, get_file_contents, meniscus_recall, meniscus_log
from ...tools.mcp_tools import call_mcp_tool, list_mcp_tools
from ...util.checkpointer_memory import checkpointer
from ...util.logger import get_logger
from ...util.middleware import create_worker_middleware
from ...prompts.mcp_prompt import MCP_SUBAGENT_SYSTEM_PROMPT

logger = get_logger(__name__)


def mcp_subagent(
    model: Optional[Any] = None,
    backend: Optional[Any] = None,
    skills: Optional[list[str]] = None,
    tools: Optional[list[Any]] = None,
    agent_name: str = "MCP_Subagent",
    description: str = "Executes custom or generic Model Context Protocol (MCP) server tools, queries, and operations not handled by domain-specific agents.",
    system_prompt: Optional[str] = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build the MCP leaf subagent dictionary dynamically."""
    logger.info("Initializing MCP Subagent: %s", agent_name)
    selected_model = build_chat_model(model=model)
    resolved_skills = skills if skills is not None else ["/skills/"]
    resolved_backend = backend if backend is not None else build_default_backend()

    if tools is not None:
        resolved_tools = list(tools)
    else:
        resolved_tools = get_domain_tools("custom", extra_tools=[call_mcp_tool, list_mcp_tools])

    middleware = create_worker_middleware(backend=resolved_backend)
    resolved_prompt = system_prompt or MCP_SUBAGENT_SYSTEM_PROMPT

    agent = create_deep_agent(
        model=selected_model,
        tools=resolved_tools,
        middleware=middleware,
        skills=resolved_skills,
        system_prompt=resolved_prompt,
        checkpointer=checkpointer,
        backend=resolved_backend,
    )
    return {
        "name": agent_name,
        "description": description,
        "system_prompt": resolved_prompt,
        "runnable": agent,
    }


def dynamic_mcp_subagent(
    agent_name: str,
    description: str,
    system_prompt: str,
    tools: list[Any],
    model: Optional[Any] = None,
    backend: Optional[Any] = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Dynamic MCP Subagent factory pattern for custom server tools."""
    return mcp_subagent(
        model=model,
        backend=backend,
        tools=tools,
        agent_name=agent_name,
        description=description,
        system_prompt=system_prompt,
        **kwargs,
    )


# Graph export instances
mcp_leaf_subagent = mcp_subagent()["runnable"]
graph = mcp_leaf_subagent

__all__ = [
    "mcp_subagent",
    "dynamic_mcp_subagent",
    "mcp_leaf_subagent",
    "graph",
]
