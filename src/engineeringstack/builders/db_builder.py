from typing import Any, Optional
from deepagents import create_deep_agent
from ..models.ai_model import build_chat_model
from ..agents.database.rdbms import rdbms_subagent
from ..agents.database.nosql import nosql_subagent
from ..agents.database.redis import redis_subagent
from ..agents.code_review.code_review import code_review_subagent
from .backend import build_default_backend
from ..util.checkpointer_memory import checkpointer
from ..util.middleware import create_router_middleware
from ..prompts.db_prompt import DATABASE_MANAGER_SYSTEM_PROMPT


def get_db_subagents(
    model: Optional[Any] = None,
    backend: Optional[Any] = None,
    skills: Optional[list[str]] = None,
) -> list[dict[str, Any]]:
    """Return the list of Database leaf subagents."""
    selected_model = build_chat_model(model=model)
    resolved_skills = skills if skills is not None else ["/skills/"]
    resolved_backend = backend if backend is not None else build_default_backend()
    return [
        rdbms_subagent(model=selected_model, backend=resolved_backend, skills=resolved_skills),
        nosql_subagent(model=selected_model, backend=resolved_backend, skills=resolved_skills),
        redis_subagent(model=selected_model, backend=resolved_backend, skills=resolved_skills),
        code_review_subagent(model=selected_model, backend=resolved_backend, skills=resolved_skills),
    ]


def build_database_manager(
    model: Optional[Any] = None,
    backend: Optional[Any] = None,
    skills: Optional[list[str]] = None,
    tools: Optional[list[Any]] = None,
):
    """Build the Database Manager router agent with specialized DB subagents."""
    selected_model = build_chat_model(model=model)
    resolved_skills = skills if skills is not None else ["/skills/"]
    resolved_backend = backend if backend is not None else build_default_backend()
    resolved_tools = list(tools) if tools is not None else None

    # Database Manager is a pure router: expose only `read_file` (for skills) alongside `task`
    middleware = create_router_middleware(backend=resolved_backend)
    return create_deep_agent(
        model=selected_model,
        subagents=get_db_subagents(model=selected_model, backend=resolved_backend, skills=resolved_skills),
        tools=resolved_tools,
        middleware=middleware,
        skills=resolved_skills,
        system_prompt=DATABASE_MANAGER_SYSTEM_PROMPT,
        checkpointer=checkpointer,
        backend=resolved_backend,
    )


# Graph export instances for debugging and standalone execution
database_manager = build_database_manager()
db_subagents = database_manager
graph = database_manager
