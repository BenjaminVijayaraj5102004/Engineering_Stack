import Agents.config  # Initialize environment and LangSmith tracing
from deepagents import create_deep_agent
from models.ai_model import small_tool_ollama
from tools.tools import search_code, get_file_contents
from util.checkpointer_memory import checkpointer

from prompts.api_prompt import GRAPHQL_SYSTEM_PROMPT

print("Entered GraphQL Agent")

graphql_agent = create_deep_agent(
    model=small_tool_ollama,
    tools=[search_code, get_file_contents],
    system_prompt=GRAPHQL_SYSTEM_PROMPT,
    checkpointer=checkpointer,
)

graphql_subagent = {
    "name": "GraphQL_Agent",
    "description": "Handles GraphQL API requests, schema design, resolvers, queries, mutations, subscriptions, Apollo, Strawberry, and Graphene.",
    "system_prompt": GRAPHQL_SYSTEM_PROMPT,
    "runnable": graphql_agent,
}