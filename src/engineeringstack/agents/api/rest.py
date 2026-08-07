from typing import Any, Optional
from deepagents import create_deep_agent
from ...models.ai_model import build_chat_model
from ...schema.state import AIOutput
from ...tools.tools import search_code
from ...util.checkpointer_memory import checkpointer
from ...util.logger import get_logger
from ...prompts.api_prompt import REST_SYSTEM_PROMPT

logger = get_logger(__name__)


def rest_subagent(
    model: Optional[Any] = None,
    backend: Optional[Any] = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build the REST Agent subagent dictionary dynamically with custom model support."""
    logger.info("Initializing REST Agent")
    selected_model = build_chat_model(model=model)
    rest_agent = create_deep_agent(
        model=selected_model,
        tools=[search_code],
        system_prompt=REST_SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )
    logger.info("REST model: %s", selected_model.model_name)
    logger.info("REST Agent initialized successfully")

    return {
        "name": "REST_Agent",
        "description": "Implements REST APIs only. Never handles GraphQL, gRPC, SOAP, or code reviews.",
        "system_prompt": REST_SYSTEM_PROMPT,
        "runnable": rest_agent,
    }



