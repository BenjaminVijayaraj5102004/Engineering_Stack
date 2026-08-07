from typing import Any, Optional
from deepagents import create_deep_agent
from ..models.ai_model import build_chat_model
from ..agents.api.rest import rest_subagent
from ..agents.api.graphql import graphql_subagent
from ..agents.api.grpc import grpc_subagent
from ..agents.api.soap import soap_subagent
from ..schema.state import MainAgentOutput
from ..util.checkpointer_memory import checkpointer
from ..prompts.api_prompt import API_MANAGER_SYSTEM_PROMPT


def build_api_manager(
    model: Optional[Any] = None,
    backend: Optional[Any] = None,
):
    selected_model = build_chat_model(model=model)
    return create_deep_agent(
        model=selected_model,
        subagents=[
            rest_subagent(model=selected_model, backend=backend),
            graphql_subagent(model=selected_model, backend=backend),
            grpc_subagent(model=selected_model, backend=backend),
            soap_subagent(model=selected_model, backend=backend),
        ],
        system_prompt=API_MANAGER_SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )



