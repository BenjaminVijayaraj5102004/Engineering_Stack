from typing import Any, Optional
from deepagents import create_deep_agent
from ..models.ai_model import small_tool_ollama
from ..agents.api.rest import rest_subagent
from ..agents.api.graphql import graphql_subagent
from ..agents.api.grpc import grpc_subagent
from ..agents.api.soap import soap_subagent
from ..util.checkpointer_memory import checkpointer
from ..prompts.api_prompt import API_MANAGER_SYSTEM_PROMPT


def build_api_manager(
    model: Optional[Any] = None,
    backend: Optional[Any] = None,
):
    selected_model = model if model is not None else small_tool_ollama
    return create_deep_agent(
        model=selected_model,
        subagents=[
            rest_subagent,
            graphql_subagent,
            grpc_subagent,
            soap_subagent,
        ],
        system_prompt=API_MANAGER_SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )
