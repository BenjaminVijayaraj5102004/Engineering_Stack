from typing import Any, Optional
from deepagents import create_deep_agent
from ...builders.backend import build_default_backend
from ...models.ai_model import build_chat_model
from ...tools.tools import get_domain_tools, search_code, get_file_contents, meniscus_recall
from ...util.checkpointer_memory import checkpointer
from ...util.logger import get_logger
from ...util.middleware import create_worker_middleware
from ...prompts.db_prompt import NOSQL_SYSTEM_PROMPT

logger = get_logger(__name__)


def nosql_subagent(
    model: Optional[Any] = None,
    backend: Optional[Any] = None,
    skills: Optional[list[str]] = None,
    tools: Optional[list[Any]] = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build the NoSQL Agent leaf subagent dictionary dynamically."""
    logger.info("Initializing NoSQL Agent")
    selected_model = build_chat_model(model=model)
    resolved_skills = skills if skills is not None else ["/skills/"]
    resolved_backend = backend if backend is not None else build_default_backend()
    resolved_tools = tools if tools is not None else get_domain_tools("nosql")

    middleware = create_worker_middleware(backend=resolved_backend)

    nosql_agent = create_deep_agent(
        model=selected_model,
        tools=resolved_tools,
        middleware=middleware,
        skills=resolved_skills,
        system_prompt=NOSQL_SYSTEM_PROMPT,
        checkpointer=checkpointer,
        backend=resolved_backend,
    )
    return {
        "name": "NoSQL_agent",
        "description": "Implements document and NoSQL schemas (MongoDB, Cassandra, DynamoDB).",
        "system_prompt": NOSQL_SYSTEM_PROMPT,
        "runnable": nosql_agent,
    }


# Graph export instances
db_subagents = nosql_subagent()["runnable"]
graph = db_subagents
