import Agents.config  # Initialize environment and LangSmith tracing
from deepagents import create_deep_agent
from models.ai_model import small_tool_ollama
from Agents.database.rdms import rdms_subagent
from Agents.database.nosql import nosql_subagent
from Agents.database.redis import redis_subagent
from util.checkpointer_memory import checkpointer
from prompts.db_prompt import DATABASE_MANAGER_SYSTEM_PROMPT

database_subagents = [rdms_subagent, nosql_subagent, redis_subagent]


def build_database_manager():

    return create_deep_agent(
        model=small_tool_ollama,
        subagents=[
            rdms_subagent,
            nosql_subagent,
            redis_subagent,
        ],
        system_prompt=DATABASE_MANAGER_SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )
    