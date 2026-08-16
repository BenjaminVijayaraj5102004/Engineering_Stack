from typing import Any, Optional
from deepagents import create_deep_agent
from ...models.ai_model import build_chat_model
from ...builders.backend import build_default_backend
from ...tools.tools import search_code, get_file_contents
from ...util.checkpointer_memory import checkpointer
from ...util.logger import get_logger
from ...util.middleware import create_reviewer_middleware
from ...prompts.code_review_prompt import CODE_REVIEW_SYSTEM_PROMPT

logger = get_logger(__name__)


def code_review_subagent(
    model: Optional[Any] = None,
    backend: Optional[Any] = None,
    skills: Optional[list[str]] = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build the Code Reviewer leaf subagent dictionary dynamically."""
    logger.info("Initializing Code Reviewer Agent")
    selected_model = build_chat_model(model=model)
    resolved_skills = skills if skills is not None else ["/skills/"]
    resolved_backend = backend if backend is not None else build_default_backend()

    middleware = create_reviewer_middleware(backend=resolved_backend)

    code_review_agent = create_deep_agent(
        model=selected_model,
        tools=[search_code, get_file_contents],
        system_prompt=CODE_REVIEW_SYSTEM_PROMPT,
        middleware=middleware,
        skills=resolved_skills,
        checkpointer=checkpointer,
        backend=resolved_backend,
    )
    return {
        "name": "Code_Reviewer",
        "description": "Reviews existing code only and provides 5 bullet points of QA findings and polished code in markdown fences.",
        "system_prompt": CODE_REVIEW_SYSTEM_PROMPT,
        "runnable": code_review_agent,
    }
