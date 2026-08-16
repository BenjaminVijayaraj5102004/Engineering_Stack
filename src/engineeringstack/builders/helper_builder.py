from typing import Any, Optional
from deepagents import create_deep_agent
from ..models.ai_model import build_chat_model
from ..agents.coding.coding import coding_subagent
from ..agents.code_review.code_review import code_review_subagent
from .backend import build_default_backend
from ..util.checkpointer_memory import checkpointer
from ..util.middleware import create_router_middleware
from ..prompts.helper_prompt import HELPER_MANAGER_SYSTEM_PROMPT


def build_helper_manager(
    model: Optional[Any] = None,
    backend: Optional[Any] = None,
    skills: Optional[list[str]] = None,
    tools: Optional[list[Any]] = None,
):
    """Build the Helper Manager router agent with Coding_Agent/Code_Reviewer subagents."""
    selected_model = build_chat_model(model=model)
    resolved_skills = skills if skills is not None else ["/skills/"]
    resolved_backend = backend if backend is not None else build_default_backend()
    resolved_tools = list(tools) if tools is not None else None

    # Helper Manager is a router: expose only `read_file` (for skills) alongside `task`
    middleware = create_router_middleware(backend=resolved_backend)
    return create_deep_agent(
        model=selected_model,
        subagents=[
            coding_subagent(model=selected_model, backend=resolved_backend, skills=resolved_skills),
            code_review_subagent(model=selected_model, backend=resolved_backend, skills=resolved_skills),
        ],
        tools=resolved_tools,
        middleware=middleware,
        skills=resolved_skills,
        system_prompt=HELPER_MANAGER_SYSTEM_PROMPT,
        checkpointer=checkpointer,
        backend=resolved_backend,
    )
