from deepagents import create_deep_agent

from models.ai_model import small_tool_ollama
from prompts.main_agent_prompt import MAIN_AGENT_SYSTEM_PROMPT
from Agents.managers.apimanager import api_manager_subagent
from Agents.managers.databasemanager import database_manager_subagent
from Agents.code_review.code_review import code_review_subagent
from util.checkpointer_memory import checkpointer


def build_main_agent():
    return create_deep_agent(
        model=small_tool_ollama,
        system_prompt=MAIN_AGENT_SYSTEM_PROMPT,
        subagents=[
            database_manager_subagent,
            api_manager_subagent,
            code_review_subagent,
        ],
        checkpointer=checkpointer,
    )