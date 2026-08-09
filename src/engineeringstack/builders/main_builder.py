from pathlib import Path
from typing import Any, Optional, Union
from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend, StoreBackend
from ..models.ai_model import build_chat_model
from ..prompts.main_agent_prompt import MAIN_AGENT_SYSTEM_PROMPT
from ..agents.managers.apimanager import api_manager_subagent
from ..agents.managers.databasemanager import database_manager_subagent
from ..agents.code_review.code_review import code_review_subagent
from ..schema.state import UserInput, MainAgentOutput, AIOutput
from ..util.checkpointer_memory import checkpointer

# SDK Default Memory & Skills
DEFAULT_MEMORY = ["/memories/AGENTS.md"]
DEFAULT_SKILLS = ["/skills/"]


def _default_user_namespace(rt: Any) -> tuple[str, ...]:
    """Safe namespace for multi-tenant production cloud with local fallback."""
    user = getattr(getattr(rt, "server_info", None), "user", None)
    user_id = user.identity if user else "default_user"
    return (user_id,)


def build_default_backend(
    local_memory_dir: Optional[Union[str, Path]] = None,
    local_skills_dir: Optional[Union[str, Path]] = None,
) -> CompositeBackend:
    """Builds a composite backend: uses FilesystemBackend if local dir provided, else StoreBackend."""
    routes: dict[str, Any] = {}

    # /memories/ route: Local disk if specified, else StoreBackend (Cloud/Virtual)
    if local_memory_dir is not None:
        Path(local_memory_dir).mkdir(parents=True, exist_ok=True)
        routes["/memories/"] = FilesystemBackend(root_dir=str(local_memory_dir))
    else:
        routes["/memories/"] = StoreBackend(namespace=_default_user_namespace)

    # /skills/ route: Local disk if specified, else StoreBackend
    if local_skills_dir is not None:
        Path(local_skills_dir).mkdir(parents=True, exist_ok=True)
        routes["/skills/"] = FilesystemBackend(root_dir=str(local_skills_dir))
    else:
        routes["/skills/"] = StoreBackend(namespace=_default_user_namespace)

    return CompositeBackend(
        default=StateBackend(),
        routes=routes,
    )


def build_main_agent(
    model: Optional[Any] = None,
    backend: Optional[Any] = None,
    memory: Optional[list[str]] = None,
    skills: Optional[list[str]] = None,
    skill: Optional[Any] = None,
    local_memory_dir: Optional[Union[str, Path]] = None,
    local_skills_dir: Optional[Union[str, Path]] = None,
    store: Optional[Any] = None,
):
    selected_model = build_chat_model(model=model)

    # 1. Resolve Backend: Custom Backend > Local Directory Routes > Default Virtual Backend
    if backend is None:
        backend = build_default_backend(
            local_memory_dir=local_memory_dir,
            local_skills_dir=local_skills_dir,
        )

    # 2. Resolve Memory & Skills: User custom list > SDK default
    resolved_skills = skills if skills is not None else skill
    resolved_skills = resolved_skills if resolved_skills is not None else DEFAULT_SKILLS
    resolved_memory = memory if memory is not None else DEFAULT_MEMORY

    return create_deep_agent(
        model=selected_model,
        system_prompt=MAIN_AGENT_SYSTEM_PROMPT,
        backend=backend,
        memory=resolved_memory,
        skills=resolved_skills,
        store=store,
        subagents=[
            database_manager_subagent(
                model=selected_model,
                backend=backend,
            ),
            api_manager_subagent(
                model=selected_model,
                backend=backend,
            ),
            code_review_subagent(
                model=selected_model,
                backend=backend,
            ),
        ],
        checkpointer=checkpointer,
    )
