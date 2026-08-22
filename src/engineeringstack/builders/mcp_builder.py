from typing import Any, Optional
from deepagents import create_deep_agent
from deepagents.middleware.filesystem import FilesystemMiddleware
from ..models.ai_model import build_chat_model
from ..tools.tools import meniscus_recall, meniscus_log
from ..tools.mcp_tools import (
    register_mcp_server,
    list_mcp_tools,
    list_registered_mcp_servers,
    remove_mcp_server,
)
from .backend import build_default_backend
from ..util.checkpointer_memory import checkpointer
from ..util.middleware import NoOpMiddleware
from ..prompts.mcp_prompt import MCP_MANAGER_SYSTEM_PROMPT


def build_mcp_manager(
    model: Optional[Any] = None,
    backend: Optional[Any] = None,
    skills: Optional[list[str]] = None,
    tools: Optional[list[Any]] = None,
):
    """Build the MCP Manager agent with filesystem capabilities, MCP management tools, and Meniscus memory."""
    selected_model = build_chat_model(model=model)
    resolved_skills = skills if skills is not None else ["/skills/"]
    resolved_backend = backend if backend is not None else build_default_backend()
    resolved_tools = list(tools) if tools is not None else [
        register_mcp_server,
        list_mcp_tools,
        list_registered_mcp_servers,
        remove_mcp_server,
        meniscus_recall,
        meniscus_log,
    ]

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
