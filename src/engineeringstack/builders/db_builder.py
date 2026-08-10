from typing import Any, Optional
from deepagents import create_deep_agent
from ..models.ai_model import build_chat_model
from ..agents.database.rdms import rdms_subagent
from ..agents.database.nosql import nosql_subagent
from ..agents.database.redis import redis_subagent
from ..schema.state import MainAgentOutput
from ..util.checkpointer_memory import checkpointer
from ..prompts.db_prompt import DATABASE_MANAGER_SYSTEM_PROMPT


def build_database_manager(
    model: Optional[Any] = None,
    backend: Optional[Any] = None,
):
    selected_model = build_chat_model(model=model)
    return create_deep_agent(
        model=selected_model,
        subagents=[
            rdms_subagent(model=selected_model, backend=backend),
            nosql_subagent(model=selected_model, backend=backend),
            redis_subagent(model=selected_model, backend=backend),
        ],
        system_prompt=DATABASE_MANAGER_SYSTEM_PROMPT,
        checkpointer=checkpointer,
        backend=backend,
    )



