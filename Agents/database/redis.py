import Agents.config  # Initialize environment and LangSmith tracing
from deepagents import create_deep_agent
from models.ai_model import small_tool_ollama
from tools.tools import search_code, get_file_contents
from util.checkpointer_memory import checkpointer

from prompts.db_prompt import REDIS_SYSTEM_PROMPT

print("Entered Redis Agent")

redis_agent = create_deep_agent(
    model=small_tool_ollama,
    tools=[search_code, get_file_contents],
    system_prompt=REDIS_SYSTEM_PROMPT,
    checkpointer=checkpointer,
)

redis_subagent = {
    "name": "REDIS_agent",
    "description": "Handles all Redis, in-memory caching, key-value data structures, TTL, and session management requests.",
    "system_prompt": REDIS_SYSTEM_PROMPT,
    "runnable": redis_agent,
}
