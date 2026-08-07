from typing import Any, Optional
from deepagents import create_deep_agent
from ...models.ai_model import build_chat_model
from ...schema.state import AIOutput
from ...tools.tools import search_code, get_file_contents
from ...util.checkpointer_memory import checkpointer
from ...util.logger import get_logger
from ...prompts.api_prompt import GRPC_SYSTEM_PROMPT

logger = get_logger(__name__)


def grpc_subagent(
    model: Optional[Any] = None,
    backend: Optional[Any] = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build the gRPC Agent subagent dictionary dynamically with custom model support."""
    logger.info("Initializing gRPC Agent")
    selected_model = build_chat_model(model=model)
    grpc_agent = create_deep_agent(
        model=selected_model,
        tools=[search_code, get_file_contents],
        system_prompt=GRPC_SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )
    return {
        "name": "GRPC_Agent",
        "description": "Implements gRPC services only. Never handles REST, GraphQL, SOAP, or code reviews.",
        "system_prompt": GRPC_SYSTEM_PROMPT,
        "runnable": grpc_agent,
    }



