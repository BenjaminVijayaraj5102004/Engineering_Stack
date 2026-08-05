from deepagents import create_deep_agent
from ...models.ai_model import small_tool_ollama
from ...tools.tools import search_code, get_file_contents
from ...util.checkpointer_memory import checkpointer
from ...util.logger import get_logger
from ...prompts.api_prompt import SOAP_SYSTEM_PROMPT

logger = get_logger(__name__)

logger.info("Initializing SOAP Agent")

soap_agent = create_deep_agent(
    model=small_tool_ollama,
    tools=[search_code, get_file_contents],
    system_prompt=SOAP_SYSTEM_PROMPT,
    checkpointer=checkpointer,
)

soap_subagent = {
    "name": "SOAP_Agent",
    "description": "Implements SOAP services only. Never handles REST, GraphQL, gRPC, or code reviews.",
    "system_prompt": SOAP_SYSTEM_PROMPT,
    "runnable": soap_agent,
}
