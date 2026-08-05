from deepagents import create_deep_agent
from ...models.ai_model import small_tool_ollama
from ...tools.tools import search_code, get_file_contents
from ...util.checkpointer_memory import checkpointer
from ...util.logger import get_logger
from ...prompts.db_prompt import NOSQL_SYSTEM_PROMPT

logger = get_logger(__name__)

logger.info("Initializing NoSQL Agent")

nosql_agent = create_deep_agent(
    model=small_tool_ollama,
    tools=[search_code, get_file_contents],
    system_prompt=NOSQL_SYSTEM_PROMPT,
    checkpointer=checkpointer,
)

nosql_subagent = {
    "name": "NoSQL_agent",
    "description": "Implements NoSQL databases only. Never handles SQL, Redis, or code reviews.",
    "system_prompt": NOSQL_SYSTEM_PROMPT,
    "runnable": nosql_agent,
}
