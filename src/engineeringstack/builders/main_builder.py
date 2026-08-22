"""Main Agent Builder for the Engineering Stack.

Constructs the top-level orchestrator agent with intent evaluation tools,
greetings/conversation handling, and specialized helper subagents
(API_Manager, Database_Manager, Helper_Manager, and MCP_Manager).
"""

from typing import Any, Optional
from deepagents import create_deep_agent
from ..models.ai_model import build_chat_model
from ..prompts.main_agent_prompt import MAIN_AGENT_SYSTEM_PROMPT
from ..agents.managers.apimanager import api_manager_subagent
from ..agents.managers.databasemanager import database_manager_subagent
from ..agents.managers.helper_manager import helper_manager_subagent
from ..agents.managers.mcpmanager import mcp_manager_subagent
from ..tools.tools import meniscus_recall, meniscus_log, search_knowledge_base, set_active_store
from ..util.checkpointer_memory import checkpointer
from ..util.logger import get_logger
from ..util.middleware import create_router_middleware
from .backend import (
    SDK_SKILLS_DIR,
    build_default_backend,
)
from .store import build_default_store

logger = get_logger(__name__)


def get_helper_agents(
    model: Optional[Any] = None,
    backend: Optional[Any] = None,
    skills: Optional[list[str]] = None,
    include_mcp: bool = False,
) -> list[dict[str, Any]]:
    """Build and return the list of specialized manager subagents for Main Agent.

    Includes:
    - Database_Manager: Routes database tasks (SQL, NoSQL, Redis).
    - API_Manager: Routes API tasks (REST, GraphQL, gRPC, SOAP).
    - Helper_Manager: Routes generic coding to Coding_Agent and reviews to Code_Reviewer.
    - MCP_Manager (optional/included in main agent): Provisions custom MCP servers and subagents.
    """
    agents = [
        database_manager_subagent(
            model=model,
            backend=backend,
            skills=skills,
        ),
        api_manager_subagent(
            model=model,
            backend=backend,
            skills=skills,
        ),
        helper_manager_subagent(
            model=model,
            backend=backend,
            skills=skills,
        ),
    ]
    if include_mcp:
        agents.append(
            mcp_manager_subagent(
                model=model,
                backend=backend,
                skills=skills,
            )
        )
    return agents


def build_main_agent(
    model: Optional[Any] = None,
    backend: Optional[Any] = None,
    skills: Optional[list[str]] = None,
    tools: Optional[list[Any]] = None,
    store: Optional[Any] = None,
    middleware: Optional[list[Any]] = None,
    memory: Optional[list[str]] = None,
):
    """Build and compile the Main Agent with helper subagents, procedural skills, and restricted router middleware.

    Args:
        model: Optional custom LLM model instance or model name string.
        backend: Optional CompositeBackend override.
        skills: Optional list of skill directory paths (defaults to ['/skills/']).
        tools: Optional custom list of tools.
        store: Optional LangGraph BaseStore instance.
        middleware: Optional list of additional custom middlewares.
        memory: Optional memory list (optional passthrough).

    Returns:
        Compiled LangGraph state graph for the Main Agent.
    """
    selected_model = build_chat_model(model=model)
    resolved_store = store if store is not None else build_default_store()
    set_active_store(resolved_store)
    resolved_backend = backend if backend is not None else build_default_backend()
    resolved_skills = skills if skills is not None else ["/skills/"]
    resolved_tools = list(tools) if tools is not None else [meniscus_recall, meniscus_log, search_knowledge_base]

    # Resolve Helper Subagents (including MCP Manager for custom MCP provisioning)
    subagents = get_helper_agents(
        model=selected_model,
        backend=resolved_backend,
        skills=resolved_skills,
        include_mcp=True,
    )

    # Configure Middlewares:
    # Main Agent is an orchestrator: expose only read_file (for skills) alongside task tool.
    agent_middleware = create_router_middleware(backend=resolved_backend)
    if middleware:
        agent_middleware.extend(middleware)

    logger.info(
        "Building Main Agent with %d helper subagents and %d custom tools",
        len(subagents),
        len(resolved_tools),
    )

    return create_deep_agent(
        model=selected_model,
        system_prompt=MAIN_AGENT_SYSTEM_PROMPT,
        middleware=agent_middleware,
        backend=resolved_backend,
        memory=memory,
        skills=resolved_skills,
        tools=resolved_tools,
        store=resolved_store,
        subagents=subagents,
        checkpointer=checkpointer,
    )


# Graph export instances for debugging and standalone execution
main_agent = build_main_agent()
graph = main_agent
