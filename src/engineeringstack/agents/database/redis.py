from deepagents import create_deep_agent
from ...models.ai_model import small_tool_ollama
from ...tools.tools import search_code, get_file_contents
from ...util.checkpointer_memory import checkpointer
from ...util.logger import get_logger
from ...prompts.db_prompt import REDIS_SYSTEM_PROMPT

logger = get_logger(__name__)

logger.info("Initializing Redis Agent")

redis_agent = create_deep_agent(
    model=small_tool_ollama,
    tools=[search_code, get_file_contents],
    system_prompt=REDIS_SYSTEM_PROMPT,
    checkpointer=checkpointer,
)

redis_subagent = {
    "name": "REDIS_agent",
    "description": "Implements Redis caching only. Never handles SQL, NoSQL, or code reviews.",
    "system_prompt": REDIS_SYSTEM_PROMPT,
    "runnable": redis_agent,
}
