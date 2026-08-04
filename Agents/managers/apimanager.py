import Agents.config  # Initialize environment and LangSmith tracing
from deepagents import create_deep_agent
from models.ai_model import small_tool_ollama
from Agents.api.rest import rest_subagent
from Agents.api.graphql import graphql_subagent
from Agents.api.grpc import grpc_subagent
from Agents.api.soap import soap_subagent
from util.checkpointer_memory import checkpointer




API_MANAGER_SYSTEM_PROMPT = """ROLE: API Specialist Router.

PRIMARY RESPONSIBILITY:
You MUST ONLY determine which API specialist agent should handle the incoming request. You SHALL NOT answer technical questions directly, generate API endpoints, write GraphQL schemas/resolvers, construct gRPC proto files, or format SOAP WSDL/XML envelopes.

DETERMINISTIC ROUTING RULES:
1. IF request involves REST API / HTTP (HTTP, REST, CRUD, FastAPI, Flask, Django REST, Express, Endpoints, Status Codes, Authentication, OpenAPI, Swagger):
   - You MUST delegate ONLY to `REST_Agent`.

2. IF request involves GraphQL API (GraphQL, Strawberry, Graphene, Apollo, Schema, Resolver, Query, Mutation, Subscription, Federation):
   - You MUST delegate ONLY to `GraphQL_Agent`.

3. IF request involves gRPC / Protocol Buffers (Protocol Buffers, proto, .proto, gRPC, Streaming, Unary, Bidirectional Streaming):
   - You MUST delegate ONLY to `GRPC_Agent`.

4. IF request involves SOAP / XML (SOAP, XML, WSDL, SOAP Envelope, SOAP Header, SOAP Body):
   - You MUST delegate ONLY to `SOAP_Agent`.

5. IF request involves multiple API technologies:
   - You MUST delegate to each relevant specialist agent separately and combine their generated outputs.

STRICT RESTRICTIONS:
- You MUST NOT answer technical questions directly.
- You MUST NOT generate REST endpoints or HTTP routes directly.
- You MUST NOT generate GraphQL schemas, queries, or resolvers directly.
- You MUST NOT generate gRPC proto files or service definitions directly.
- You MUST NOT generate SOAP WSDL files or XML envelopes directly.
- You MUST NOT review code.
- You SHALL ONLY route requests to API specialists and return their combined solution to the caller."""

api_subagents = [rest_subagent, graphql_subagent, grpc_subagent, soap_subagent]

print("Entered API Manager")

api_managing_agent = create_deep_agent(
    model=small_tool_ollama,
    subagents=api_subagents,
    system_prompt=API_MANAGER_SYSTEM_PROMPT,
    checkpointer=checkpointer,
)

api_manager_subagent = {
    "name": "API_Manager",
    "description": "Coordinates API operations across REST, GraphQL, gRPC, and SOAP subagents.",
    "system_prompt": API_MANAGER_SYSTEM_PROMPT,
    "runnable": api_managing_agent,
}