from typing import Any, Optional
from deepagents import create_deep_agent
from ..models.ai_model import small_tool_ollama
from ..agents.database.rdms import rdms_subagent
from ..agents.database.nosql import nosql_subagent
from ..agents.database.redis import redis_subagent
from ..util.checkpointer_memory import checkpointer
from ..prompts.db_prompt import DATABASE_MANAGER_SYSTEM_PROMPT


def build_database_manager(
    model: Optional[Any] = None,
    backend: Optional[Any] = None,
):
    selected_model = model if model is not None else small_tool_ollama
    return create_deep_agent(
        model=selected_model,
        subagents=[
            rdms_subagent,
            nosql_subagent,
            redis_subagent,
        ],
        system_prompt=DATABASE_MANAGER_SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )
