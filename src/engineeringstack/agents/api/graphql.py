from deepagents import create_deep_agent
from ...models.ai_model import small_tool_ollama
from ...tools.tools import search_code, get_file_contents
from ...util.checkpointer_memory import checkpointer
from ...util.logger import get_logger
from ...prompts.api_prompt import GRAPHQL_SYSTEM_PROMPT

logger = get_logger(__name__)

logger.info("Initializing GraphQL Agent")

graphql_agent = create_deep_agent(
    model=small_tool_ollama,
    tools=[search_code, get_file_contents],
    system_prompt=GRAPHQL_SYSTEM_PROMPT,
    checkpointer=checkpointer,
)

graphql_subagent = {
    "name": "GraphQL_Agent",
    "description": "Implements GraphQL APIs only. Never handles REST, gRPC, SOAP, or code reviews.",
    "system_prompt": GRAPHQL_SYSTEM_PROMPT,
    "runnable": graphql_agent,
}
