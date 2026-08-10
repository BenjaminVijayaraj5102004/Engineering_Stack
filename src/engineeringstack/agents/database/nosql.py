from typing import Any, Optional
from deepagents import create_deep_agent
from ...models.ai_model import build_chat_model
from ...schema.state import AIOutput
from ...tools.tools import search_code, get_file_contents
from ...util.checkpointer_memory import checkpointer
from ...util.logger import get_logger
from ...prompts.db_prompt import NOSQL_SYSTEM_PROMPT

logger = get_logger(__name__)


def nosql_subagent(
    model: Optional[Any] = None,
    backend: Optional[Any] = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build the NoSQL Agent subagent dictionary dynamically with custom model support."""
    logger.info("Initializing NoSQL Agent")
    selected_model = build_chat_model(model=model)
    nosql_agent = create_deep_agent(
        model=selected_model,
        tools=[search_code, get_file_contents],
        system_prompt=NOSQL_SYSTEM_PROMPT,
        checkpointer=checkpointer,
        backend=backend,
    )
    return {
        "name": "NoSQL_agent",
        "description": "Implements NoSQL databases only. Never handles SQL, Redis, or code reviews.",
        "system_prompt": NOSQL_SYSTEM_PROMPT,
        "runnable": nosql_agent,
    }



