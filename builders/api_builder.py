import Agents.config  # Initialize environment and LangSmith tracing
from deepagents import create_deep_agent
from models.ai_model import small_tool_ollama
from Agents.api.rest import rest_subagent
from Agents.api.graphql import graphql_subagent
from Agents.api.grpc import grpc_subagent
from Agents.api.soap import soap_subagent
from util.checkpointer_memory import checkpointer
from prompts.api_prompt import API_MANAGER_SYSTEM_PROMPT


def build_api_manager():

    return create_deep_agent(
        model=small_tool_ollama,
        subagents=[
            rest_subagent,
            graphql_subagent,
            grpc_subagent,
            soap_subagent,
        ],
        system_prompt=API_MANAGER_SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )