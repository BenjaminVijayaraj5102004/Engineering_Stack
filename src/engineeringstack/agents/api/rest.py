from deepagents import create_deep_agent
from ...models.ai_model import small_tool_ollama
from ...tools.tools import search_code, get_file_contents
from ...util.checkpointer_memory import checkpointer
from ...util.logger import get_logger
from ...prompts.api_prompt import REST_SYSTEM_PROMPT

logger = get_logger(__name__)

logger.info("Initializing REST Agent")

rest_agent = create_deep_agent(
    model=small_tool_ollama,
    tools=[search_code],
    system_prompt=REST_SYSTEM_PROMPT,
    checkpointer=checkpointer,
)
logger.info("REST Agent initialized successfully")

rest_subagent = {
    "name": "REST_Agent",
    "description": "Implements REST APIs only. Never handles GraphQL, gRPC, SOAP, or code reviews.",
    "system_prompt": REST_SYSTEM_PROMPT,
    "runnable": rest_agent,
}
