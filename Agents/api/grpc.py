import Agents.config  # Initialize environment and LangSmith tracing
from deepagents import create_deep_agent
from models.ai_model import small_tool_ollama
from tools.tools import search_code, get_file_contents
from util.checkpointer_memory import checkpointer

from prompts.api_prompt import GRPC_SYSTEM_PROMPT

print("Entered gRPC Agent")

grpc_agent = create_deep_agent(
    model=small_tool_ollama,
    tools=[search_code, get_file_contents],
    system_prompt=GRPC_SYSTEM_PROMPT,
    checkpointer=checkpointer,
)

grpc_subagent = {
    "name": "GRPC_Agent",
    "description": "Handles gRPC API requests, Protocol Buffers (.proto), Unary RPCs, Server Streaming, Client Streaming, and Bidirectional Streaming.",
    "system_prompt": GRPC_SYSTEM_PROMPT,
    "runnable": grpc_agent,
}