from typing import Any, Optional
from deepagents import create_deep_agent
from ...models.ai_model import build_chat_model
from ...schema.state import AIOutput
from ...tools.tools import search_code, get_file_contents
from ...util.checkpointer_memory import checkpointer
from ...util.logger import get_logger
from ...prompts.api_prompt import SOAP_SYSTEM_PROMPT

logger = get_logger(__name__)


def soap_subagent(
    model: Optional[Any] = None,
    backend: Optional[Any] = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build the SOAP Agent subagent dictionary dynamically with custom model support."""
    logger.info("Initializing SOAP Agent")
    selected_model = build_chat_model(model=model)
    soap_agent = create_deep_agent(
        model=selected_model,
        tools=[search_code],
        system_prompt=SOAP_SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )
    return {
        "name": "SOAP_Agent",
        "description": "Implements SOAP services only. Never handles REST, GraphQL, gRPC, or code reviews.",
        "system_prompt": SOAP_SYSTEM_PROMPT,
        "runnable": soap_agent,
    }



