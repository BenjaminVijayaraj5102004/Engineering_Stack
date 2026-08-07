from typing import Any, Optional
from deepagents import create_deep_agent
from ...models.ai_model import build_chat_model
from ...schema.state import AIOutput
from ...tools.tools import search_code, get_file_contents
from ...util.checkpointer_memory import checkpointer
from ...util.logger import get_logger
from ...prompts.db_prompt import RDMS_SYSTEM_PROMPT

logger = get_logger(__name__)


def rdms_subagent(
    model: Optional[Any] = None,
    backend: Optional[Any] = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build the RDMS Agent subagent dictionary dynamically with custom model support."""
    logger.info("Initializing RDMS Agent")
    selected_model = build_chat_model(model=model)
    rdms_agent = create_deep_agent(
        model=selected_model,
        tools=[search_code, get_file_contents],
        system_prompt=RDMS_SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )
    return {
        "name": "RDMS_agent",
        "description": "Implements SQL databases only. Never handles NoSQL, Redis, or code reviews.",
        "system_prompt": RDMS_SYSTEM_PROMPT,
        "runnable": rdms_agent,
    }



