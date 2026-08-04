import Agents.config  # Initialize environment and LangSmith tracing
from deepagents import create_deep_agent
from models.ai_model import small_tool_ollama
from tools.tools import search_code, get_file_contents
from util.checkpointer_memory import checkpointer

from prompts.db_prompt import NOSQL_SYSTEM_PROMPT

print("Entered NoSQL Agent")

nosql_agent = create_deep_agent(
    model=small_tool_ollama,
    tools=[search_code, get_file_contents],
    system_prompt=NOSQL_SYSTEM_PROMPT,
    checkpointer=checkpointer,
)

nosql_subagent = {
    "name": "NoSQL_agent",
    "description": "Handles all NoSQL, MongoDB, document schema design, and aggregation pipeline requests.",
    "system_prompt": NOSQL_SYSTEM_PROMPT,
    "runnable": nosql_agent,
}