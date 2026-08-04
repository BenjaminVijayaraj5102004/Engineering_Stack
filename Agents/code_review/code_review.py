import Agents.config  # Initialize environment and LangSmith tracing
from deepagents import create_deep_agent
from models.ai_model import small_tool_ollama
from Agents.managers.databasemanager import database_manager_subagent
from Agents.managers.apimanager import api_manager_subagent
from util.checkpointer_memory import checkpointer

from prompts.code_review_prompt import CODE_REVIEW_SYSTEM_PROMPT

review_subagents = [database_manager_subagent, api_manager_subagent]

print("Entered Code Reviewer Agent")

code_review_agent = create_deep_agent(
    model=small_tool_ollama,
    subagents=review_subagents,
    system_prompt=CODE_REVIEW_SYSTEM_PROMPT,
    checkpointer=checkpointer,
)

code_review_subagent = {
    "name": "Code_Reviewer",
    "description": "Reviews code for correctness, security, performance, maintainability, and delegates database operations.",
    "system_prompt": CODE_REVIEW_SYSTEM_PROMPT,
    "runnable": code_review_agent,
}