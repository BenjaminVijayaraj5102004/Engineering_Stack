"""Main Agent Builder for the Engineering Stack.

Constructs the top-level orchestrator agent with intent evaluation tools,
greetings/conversation handling, and specialized helper subagents
(API_Manager, Database_Manager, and Code_Reviewer).
"""

from pathlib import Path
from typing import Any, Optional, Union
from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend, StoreBackend
from langgraph.store.memory import InMemoryStore
from ..models.ai_model import build_chat_model
from ..prompts.main_agent_prompt import MAIN_AGENT_SYSTEM_PROMPT
from ..agents.managers.apimanager import api_manager_subagent
from ..agents.managers.databasemanager import database_manager_subagent
from ..agents.code_review.code_review import code_review_subagent
from ..schema.state import UserInput, MainAgentOutput, AIOutput
from ..util.checkpointer_memory import checkpointer
from ..util.helper import (
    DEFAULT_MAIN_TOOLS,
    HelperAgentType,
    IntentType,
    RouteAction,
    RoutingDecision,
    classify_intent,
    classify_user_intent_tool,
    extract_query_text,
    generate_conversational_response,
    generate_greeting_response_tool,
    get_main_agent_action,
    get_routing_advice_tool,
    is_coding_or_complex_task,
    is_conversation,
    is_greeting,
    is_greeting_or_conversation,
    main_agent_helper,
    should_delegate_to_helpers,
)
from ..util.logger import get_logger

logger = get_logger(__name__)

# SDK Default Memory & Skills
DEFAULT_MEMORY = ["/memories/preferences.md", "/memories/AGENTS.md"]
DEFAULT_SKILLS = ["/skills/"]


def _default_user_namespace(rt: Any) -> tuple[str, ...]:
    """Safe namespace for multi-tenant production cloud with local fallback."""
    user = getattr(getattr(rt, "server_info", None), "user", None)
    user_id = user.identity if user else "default_user"
    return (user_id,)


def build_default_backend(
    local_memory_dir: Optional[Union[str, Path]] = None,
    local_skills_dir: Optional[Union[str, Path]] = None,
    store: Optional[Any] = None,
) -> CompositeBackend:
    """Builds a composite backend: uses FilesystemBackend if local dir provided, else StoreBackend."""
    routes: dict[str, Any] = {}

    # /memories/ route: Local disk if specified, else StoreBackend (Cloud/Virtual)
    if local_memory_dir is not None:
        Path(local_memory_dir).mkdir(parents=True, exist_ok=True)
        routes["/memories/"] = FilesystemBackend(root_dir=str(local_memory_dir))
    else:
        routes["/memories/"] = StoreBackend(store=store, namespace=_default_user_namespace)

    # /skills/ route: Local disk if specified, else StoreBackend
    if local_skills_dir is not None:
        Path(local_skills_dir).mkdir(parents=True, exist_ok=True)
        routes["/skills/"] = FilesystemBackend(root_dir=str(local_skills_dir))
    else:
        routes["/skills/"] = StoreBackend(store=store, namespace=_default_user_namespace)

    return CompositeBackend(
        default=StateBackend(),
        routes=routes,
    )


def get_helper_agents(
    model: Optional[Any] = None,
    backend: Optional[Any] = None,
) -> list[dict[str, Any]]:
    """Build and return the list of specialized helper subagents for Main Agent.

    Includes:
    - Database_Manager: Routes database tasks (SQL, NoSQL, Redis).
    - API_Manager: Routes API tasks (REST, GraphQL, gRPC, SOAP).
    - Code_Reviewer: Reviews, audits, and verifies implementation code.
    """
    return [
        database_manager_subagent(
            model=model,
            backend=backend,
        ),
        api_manager_subagent(
            model=model,
            backend=backend,
        ),
        code_review_subagent(
            model=model,
            backend=backend,
        ),
    ]


def evaluate_main_agent_input(input_data: Any) -> RoutingDecision:
    """Helper function to evaluate user input before or during Main Agent reasoning.

    Determines whether the input is a greeting/normal conversation (to answer directly)
    or a coding/complex task (to delegate to helper agents).

    Args:
        input_data: String query, UserInput object, or message state payload.

    Returns:
        RoutingDecision with intent, action, target_agent, and suggested responses/instructions.
    """
    return main_agent_helper(input_data)


def build_main_agent(
    model: Optional[Any] = None,
    backend: Optional[Any] = None,
    memory: Optional[list[str]] = None,
    skills: Optional[list[str]] = None,
    skill: Optional[Any] = None,
    tools: Optional[list[Any]] = None,
    local_memory_dir: Optional[Union[str, Path]] = None,
    local_skills_dir: Optional[Union[str, Path]] = None,
    store: Optional[Any] = None,
):
    """Build and compile the Main Agent with helper subagents, tools, and intent handling.

    Args:
        model: Optional custom LLM model instance or model name string.
        backend: Optional CompositeBackend override.
        memory: Optional list of virtual memory paths (defaults to ['/memories/AGENTS.md']).
        skills: Optional list of skill directory paths (defaults to ['/skills/']).
        skill: Alias for skills.
        tools: Optional custom list of tools. Defaults to DEFAULT_MAIN_TOOLS (intent evaluation & routing tools).
        local_memory_dir: Optional local directory for disk-based memories.
        local_skills_dir: Optional local directory for disk-based skills.
        store: Optional LangGraph BaseStore instance.

    Returns:
        Compiled LangGraph state graph for the Main Agent.
    """
    selected_model = build_chat_model(model=model)
    resolved_store = store if store is not None else InMemoryStore()

    # 1. Resolve Backend: Custom Backend > Local Directory Routes > Default Virtual Backend
    if backend is None:
        backend = build_default_backend(
            local_memory_dir=local_memory_dir,
            local_skills_dir=local_skills_dir,
            store=resolved_store,
        )

    # 2. Resolve Memory & Skills: User custom list > SDK default
    resolved_skills = skills if skills is not None else skill
    resolved_skills = resolved_skills if resolved_skills is not None else DEFAULT_SKILLS
    resolved_memory = memory if memory is not None else DEFAULT_MEMORY

    # 3. Resolve Tools: User custom list > SDK default helper tools
    resolved_tools = list(tools) if tools is not None else list(DEFAULT_MAIN_TOOLS)

    # 4. Resolve Helper Subagents
    subagents = get_helper_agents(
        model=selected_model,
        backend=backend,
    )

    logger.info(
        "Building Main Agent with %d helper subagents and %d tools",
        len(subagents),
        len(resolved_tools),
    )

    return create_deep_agent(
        model=selected_model,
        system_prompt=MAIN_AGENT_SYSTEM_PROMPT,
        tools=resolved_tools,
        backend=backend,
        memory=resolved_memory,
        skills=resolved_skills,
        store=resolved_store,
        subagents=subagents,
        checkpointer=checkpointer,
    )
