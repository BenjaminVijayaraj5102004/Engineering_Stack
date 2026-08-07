from typing import Any, Optional
from deepagents import create_deep_agent
from ...models.ai_model import build_chat_model
from ...schema.state import AIOutput
from ...util.checkpointer_memory import checkpointer
from ...util.logger import get_logger
from ...prompts.code_review_prompt import CODE_REVIEW_SYSTEM_PROMPT

logger = get_logger(__name__)


def code_review_subagent(
    model: Optional[Any] = None,
    backend: Optional[Any] = None,
    response_format: Optional[Any] = AIOutput,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build the Code Reviewer subagent dictionary dynamically with custom model support."""
    logger.info("Initializing Code Reviewer Agent")
    selected_model = build_chat_model(model=model)
    code_review_agent = create_deep_agent(
        model=selected_model,
        system_prompt=CODE_REVIEW_SYSTEM_PROMPT,
        response_format=response_format,
        checkpointer=checkpointer,
    )
    return {
        "name": "Code_Reviewer",
        "description": "Reviews existing code only. Never implements features, creates files, or delegates tasks.",
        "system_prompt": CODE_REVIEW_SYSTEM_PROMPT,
        "response_format": response_format,
        "runnable": code_review_agent,
    }


    logger.info(f"Selected model: {selected_model}")
    logger.info(f"Model class: {type(selected_model)}")
    logger.info(f"Response format: {response_format}")
    