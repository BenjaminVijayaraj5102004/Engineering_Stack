from typing import Any, Optional
from deepagents import create_deep_agent
from ...builders.backend import build_default_backend
from ...models.ai_model import build_chat_model
from ...tools.tools import get_domain_tools, search_code, get_file_contents, meniscus_recall
from ...util.checkpointer_memory import checkpointer
from ...util.logger import get_logger
from ...util.middleware import create_worker_middleware
from ...prompts.api_prompt import REST_SYSTEM_PROMPT

logger = get_logger(__name__)


def rest_subagent(
    model: Optional[Any] = None,
    backend: Optional[Any] = None,
    skills: Optional[list[str]] = None,
    tools: Optional[list[Any]] = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build the REST Agent leaf subagent dictionary dynamically."""
    logger.info("Initializing REST Agent")
    selected_model = build_chat_model(model=model)
    resolved_skills = skills if skills is not None else ["/skills/"]
    resolved_backend = backend if backend is not None else build_default_backend()
    resolved_tools = tools if tools is not None else get_domain_tools("rest")

    middleware = create_worker_middleware(backend=resolved_backend)

    rest_agent = create_deep_agent(
        model=selected_model,
        tools=resolved_tools,
        middleware=middleware,
        skills=resolved_skills,
        system_prompt=REST_SYSTEM_PROMPT,
        checkpointer=checkpointer,
        backend=resolved_backend,
    )

    return {
        "name": "REST_Agent",
        "description": "Implements REST API endpoints and HTTP route handlers.",
        "system_prompt": REST_SYSTEM_PROMPT,
        "runnable": rest_agent,
    }


# Graph export instances
api_subagent = rest_subagent()["runnable"]
graph = api_subagent
