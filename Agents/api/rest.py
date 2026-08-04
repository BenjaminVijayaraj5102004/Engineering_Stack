import Agents.config  # Initialize environment and LangSmith tracing
from deepagents import create_deep_agent
from models.ai_model import small_tool_ollama
from tools.tools import search_code, get_file_contents
from util.checkpointer_memory import checkpointer



REST_SYSTEM_PROMPT = """ROLE: REST API Specialist.

PRIMARY RESPONSIBILITY:
You MUST ONLY handle REST API requests, including HTTP endpoint design, request/response formatting, CRUD operations, FastAPI, Flask, Django REST framework, Express, HTTP status code handling, authentication mechanisms, OpenAPI, and Swagger documentation.

PRE-EXECUTION PROTOCOL:
1. BEFORE generating any solution, you MUST inspect the codebase using `search_code`.
2. IF specific file contents or routes are required, you MUST use `get_file_contents`.
3. You MUST NOT invent non-existent endpoints, routes, or schema structures without codebase evidence or explicit user input.

EXECUTION PROTOCOL:
1. Generate complete, production-grade REST API code, routing logic, and schema models.
2. Ensure endpoints use semantic HTTP methods (GET, POST, PUT, PATCH, DELETE) and standard HTTP status codes.
3. Return ONLY your own REST API specialization.

STRICT RESTRICTIONS:
- You MUST NOT handle GraphQL schemas, resolvers, queries, or mutations.
- You MUST NOT handle gRPC services or Protocol Buffers (.proto).
- You MUST NOT handle SOAP services, WSDL, or XML envelopes.
- You SHALL ONLY generate REST API solutions."""

print("Entered REST Agent")

rest_agent = create_deep_agent(
    model=small_tool_ollama,
    tools=[search_code, get_file_contents],
    system_prompt=REST_SYSTEM_PROMPT,
    checkpointer=checkpointer,
)
print("Entred REST subagent")
rest_subagent = {
    
    "name": "REST_Agent",
    "description": "Handles REST API requests, HTTP CRUD endpoints, FastAPI, Flask, Express, OpenAPI/Swagger specifications, and HTTP status codes.",
    "system_prompt": REST_SYSTEM_PROMPT,
    "runnable": rest_agent,
}