from typing import Any, Optional
from deepagents import create_deep_agent
from deepagents.middleware.filesystem import FilesystemMiddleware
from ..models.ai_model import build_chat_model
from ..tools.tools import meniscus_recall, meniscus_log
from ..tools.mcp_tools import (
    register_mcp_server,
    list_mcp_tools,
    call_mcp_tool,
    list_registered_mcp_servers,
    remove_mcp_server,
)
from ..agents.database.rdbms import rdbms_subagent
from ..agents.database.nosql import nosql_subagent
from ..agents.database.redis import redis_subagent
from ..agents.api.rest import rest_subagent
from ..agents.api.graphql import graphql_subagent
from ..agents.api.grpc import grpc_subagent
from ..agents.api.soap import soap_subagent
from ..agents.coding.coding import coding_subagent
from ..agents.mcp_agents.mcp_subagent import mcp_subagent as mcp_custom_subagent
from .backend import build_default_backend
from ..util.checkpointer_memory import checkpointer
from ..util.middleware import NoOpMiddleware
from ..prompts.mcp_prompt import MCP_MANAGER_SYSTEM_PROMPT


def get_mcp_subagents(
    model: Optional[Any] = None,
    backend: Optional[Any] = None,
    skills: Optional[list[str]] = None,
) -> list[dict[str, Any]]:
    """Return the list of subagents accessible by MCP_Manager for tool execution and delegation."""
    selected_model = build_chat_model(model=model)
    resolved_skills = skills if skills is not None else ["/skills/"]
    resolved_backend = backend if backend is not None else build_default_backend()
    return [
        rdbms_subagent(model=selected_model, backend=resolved_backend, skills=resolved_skills),
        nosql_subagent(model=selected_model, backend=resolved_backend, skills=resolved_skills),
        redis_subagent(model=selected_model, backend=resolved_backend, skills=resolved_skills),
        rest_subagent(model=selected_model, backend=resolved_backend, skills=resolved_skills),
        graphql_subagent(model=selected_model, backend=resolved_backend, skills=resolved_skills),
        grpc_subagent(model=selected_model, backend=resolved_backend, skills=resolved_skills),
        soap_subagent(model=selected_model, backend=resolved_backend, skills=resolved_skills),
        coding_subagent(model=selected_model, backend=resolved_backend, skills=resolved_skills),
        mcp_custom_subagent(model=selected_model, backend=resolved_backend, skills=resolved_skills),
    ]


def build_mcp_manager(
    model: Optional[Any] = None,
    backend: Optional[Any] = None,
    skills: Optional[list[str]] = None,
    tools: Optional[list[Any]] = None,
    subagents: Optional[list[dict[str, Any]]] = None,
):
    """Build the MCP Manager agent with filesystem capabilities, MCP management tools, subagents, and Meniscus memory."""
    selected_model = build_chat_model(model=model)
    resolved_skills = skills if skills is not None else ["/skills/"]
    resolved_backend = backend if backend is not None else build_default_backend()
    resolved_tools = list(tools) if tools is not None else [
        register_mcp_server,
        list_mcp_tools,
        call_mcp_tool,
        list_registered_mcp_servers,
        remove_mcp_server,
        meniscus_recall,
        meniscus_log,
    ]
    resolved_subagents = subagents if subagents is not None else get_mcp_subagents(
        model=selected_model,
        backend=resolved_backend,
        skills=resolved_skills,
    )

    # MCP Manager requires write_file and filesystem inspection tools to generate configs and code
    middleware = [
        FilesystemMiddleware(
            backend=resolved_backend,
            tools=["read_file", "write_file", "edit_file", "glob", "grep"],
        ),
        NoOpMiddleware("AnthropicPromptCachingMiddleware"),
    ]

    return create_deep_agent(
        model=selected_model,
        subagents=resolved_subagents,
        tools=resolved_tools,
        middleware=middleware,
        skills=resolved_skills,
        system_prompt=MCP_MANAGER_SYSTEM_PROMPT,
        checkpointer=checkpointer,
        backend=resolved_backend,
    )


# Graph export instances for debugging and standalone execution
mcp_manager = build_mcp_manager()
mcp_subagent = mcp_manager
graph = mcp_manager

