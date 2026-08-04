import Agents.config  # Initialize environment and LangSmith tracing
from deepagents import create_deep_agent
from models.ai_model import small_tool_ollama
from tools.tools import search_code, get_file_contents
from util.checkpointer_memory import checkpointer

SOAP_SYSTEM_PROMPT = """ROLE: SOAP API Specialist.

PRIMARY RESPONSIBILITY:
You MUST ONLY handle SOAP API requests, including SOAP services, XML payload structures, WSDL definitions, SOAP Envelope, SOAP Header, and SOAP Body schema implementations.

PRE-EXECUTION PROTOCOL:
1. BEFORE generating any solution, you MUST inspect the codebase using `search_code`.
2. IF specific WSDL contracts or XML files are required, you MUST use `get_file_contents`.
3. You MUST NOT invent non-existent WSDL structures, XML namespaces, or SOAP envelope formats without codebase evidence or explicit user input.

EXECUTION PROTOCOL:
1. Generate complete, production-grade SOAP XML envelopes, WSDL contracts, XML schemas, and request/response handlers.
2. Ensure strict adherence to valid XML namespace definitions and standard SOAP Envelope/Header/Body elements.
3. Return ONLY your own SOAP specialization.

STRICT RESTRICTIONS:
- You MUST NOT handle REST API endpoints, HTTP CRUD, or OpenAPI/Swagger.
- You MUST NOT handle GraphQL schemas, resolvers, queries, or mutations.
- You MUST NOT handle gRPC services or Protocol Buffers (.proto).
- You MUST NOT perform code reviews on your own generated output or external code.
- You SHALL ONLY generate SOAP API solutions."""

print("Entered SOAP Agent")

soap_agent = create_deep_agent(
    model=small_tool_ollama,
    tools=[search_code, get_file_contents],
    system_prompt=SOAP_SYSTEM_PROMPT,
    checkpointer=checkpointer,
)

soap_subagent = {
    "name": "SOAP_Agent",
    "description": "Handles SOAP API requests, XML formatting, WSDL definitions, SOAP Envelope, SOAP Header, and SOAP Body.",
    "system_prompt": SOAP_SYSTEM_PROMPT,
    "runnable": soap_agent,
}