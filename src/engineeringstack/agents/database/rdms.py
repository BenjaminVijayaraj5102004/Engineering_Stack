from deepagents import create_deep_agent
from ...models.ai_model import small_tool_ollama
from ...tools.tools import search_code, get_file_contents
from ...util.checkpointer_memory import checkpointer
from ...util.logger import get_logger
from ...prompts.db_prompt import RDMS_SYSTEM_PROMPT

logger = get_logger(__name__)

logger.info("Initializing RDMS Agent")

rdms_agent = create_deep_agent(
    model=small_tool_ollama,
    tools=[search_code, get_file_contents],
    system_prompt=RDMS_SYSTEM_PROMPT,
    checkpointer=checkpointer,
)

rdms_subagent = {
    "name": "RDMS_agent",
    "description": "Implements SQL databases only. Never handles NoSQL, Redis, or code reviews.",
    "system_prompt": RDMS_SYSTEM_PROMPT,
    "runnable": rdms_agent,
}
