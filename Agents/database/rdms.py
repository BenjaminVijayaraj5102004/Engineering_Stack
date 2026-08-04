import Agents.config  # Initialize environment and LangSmith tracing
from deepagents import create_deep_agent
from models.ai_model import small_tool_ollama
from tools.tools import search_code, get_file_contents
from util.checkpointer_memory import checkpointer

from prompts.db_prompt import RDMS_SYSTEM_PROMPT

print("Entered RDMS Agent")

rdms_agent = create_deep_agent(
    model=small_tool_ollama,
    tools=[search_code, get_file_contents],
    system_prompt=RDMS_SYSTEM_PROMPT,
    checkpointer=checkpointer,
)

rdms_subagent = {
    "name": "RDMS_agent",
    "description": "Handles all relational database (RDBMS), SQL schema design, migrations, and query optimization requests.",
    "system_prompt": RDMS_SYSTEM_PROMPT,
    "runnable": rdms_agent,
}