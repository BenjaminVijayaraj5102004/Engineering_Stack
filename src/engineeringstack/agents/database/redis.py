from typing import Any, Optional
from deepagents import create_deep_agent
from ...models.ai_model import build_chat_model
from ...schema.state import AIOutput
from ...tools.tools import search_code, get_file_contents
from ...util.checkpointer_memory import checkpointer
from ...util.logger import get_logger
from ...prompts.db_prompt import REDIS_SYSTEM_PROMPT

logger = get_logger(__name__)


def redis_subagent(
    model: Optional[Any] = None,
    backend: Optional[Any] = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build the Redis Agent subagent dictionary dynamically with custom model support."""
    logger.info("Initializing Redis Agent")
    selected_model = build_chat_model(model=model)
    redis_agent = create_deep_agent(
        model=selected_model,
        tools=[search_code, get_file_contents],
        system_prompt=REDIS_SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )
    return {
        "name": "REDIS_agent",
        "description": "Implements Redis caching only. Never handles SQL, NoSQL, or code reviews.",
        "system_prompt": REDIS_SYSTEM_PROMPT,
        "runnable": redis_agent,
    }



