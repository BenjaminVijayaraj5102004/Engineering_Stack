from typing import Any, Optional
from deepagents import create_deep_agent
from ...builders.backend import build_default_backend
from ...models.ai_model import build_chat_model
from ...tools.tools import get_domain_tools, search_code, get_file_contents, meniscus_recall
from ...util.checkpointer_memory import checkpointer
from ...util.logger import get_logger
from ...util.middleware import create_worker_middleware
from ...prompts.api_prompt import GRAPHQL_SYSTEM_PROMPT

logger = get_logger(__name__)


def graphql_subagent(
    model: Optional[Any] = None,
    backend: Optional[Any] = None,
    skills: Optional[list[str]] = None,
    tools: Optional[list[Any]] = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build the GraphQL Agent leaf subagent dictionary dynamically."""
    logger.info("Initializing GraphQL Agent")
    selected_model = build_chat_model(model=model)
    resolved_skills = skills if skills is not None else ["/skills/"]
    resolved_backend = backend if backend is not None else build_default_backend()
    resolved_tools = tools if tools is not None else get_domain_tools("graphql")

    middleware = create_worker_middleware(backend=resolved_backend)

    graphql_agent = create_deep_agent(
        model=selected_model,
        tools=resolved_tools,
        middleware=middleware,
        skills=resolved_skills,
        system_prompt=GRAPHQL_SYSTEM_PROMPT,
        checkpointer=checkpointer,
        backend=resolved_backend,
    )
    return {
        "name": "GraphQL_Agent",
        "description": "Implements GraphQL schemas, resolvers, and types.",
        "system_prompt": GRAPHQL_SYSTEM_PROMPT,
        "runnable": graphql_agent,
    }


# Graph export instances
api_subagent = graphql_subagent()["runnable"]
graph = api_subagent
