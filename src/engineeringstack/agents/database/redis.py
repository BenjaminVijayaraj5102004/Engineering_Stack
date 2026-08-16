from typing import Any, Optional
from deepagents import create_deep_agent
from ...builders.backend import build_default_backend
from ...models.ai_model import build_chat_model
from ...tools.tools import search_code, get_file_contents
from ...util.checkpointer_memory import checkpointer
from ...util.logger import get_logger
from ...util.middleware import create_worker_middleware
from ...prompts.db_prompt import REDIS_SYSTEM_PROMPT

logger = get_logger(__name__)


def redis_subagent(
    model: Optional[Any] = None,
    backend: Optional[Any] = None,
    skills: Optional[list[str]] = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build the Redis Agent leaf subagent dictionary dynamically."""
    logger.info("Initializing Redis Agent")
    selected_model = build_chat_model(model=model)
    resolved_skills = skills if skills is not None else ["/skills/"]
    resolved_backend = backend if backend is not None else build_default_backend()

    middleware = create_worker_middleware(backend=resolved_backend)

    redis_agent = create_deep_agent(
        model=selected_model,
        tools=[search_code, get_file_contents],
        middleware=middleware,
        skills=resolved_skills,
        system_prompt=REDIS_SYSTEM_PROMPT,
        checkpointer=checkpointer,
        backend=resolved_backend,
    )
    return {
        "name": "REDIS_agent",
        "description": "Implements Redis caching configurations, session stores, and key-value layers.",
        "system_prompt": REDIS_SYSTEM_PROMPT,
        "runnable": redis_agent,
    }
