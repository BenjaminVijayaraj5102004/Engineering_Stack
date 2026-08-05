from deepagents import create_deep_agent
from ...models.ai_model import small_tool_ollama
from ...tools.tools import search_code, get_file_contents
from ...util.checkpointer_memory import checkpointer
from ...util.logger import get_logger
from ...prompts.api_prompt import GRPC_SYSTEM_PROMPT

logger = get_logger(__name__)

logger.info("Initializing gRPC Agent")

grpc_agent = create_deep_agent(
    model=small_tool_ollama,
    tools=[search_code, get_file_contents],
    system_prompt=GRPC_SYSTEM_PROMPT,
    checkpointer=checkpointer,
)

grpc_subagent = {
    "name": "GRPC_Agent",
    "description": "Implements gRPC services only. Never handles REST, GraphQL, SOAP, or code reviews.",
    "system_prompt": GRPC_SYSTEM_PROMPT,
    "runnable": grpc_agent,
}
