import Agents.config  # Initialize environment and LangSmith tracing
from deepagents import create_deep_agent
from models.ai_model import small_tool_ollama
from tools.tools import search_code, get_file_contents
from util.checkpointer_memory import checkpointer



from prompts.api_prompt import REST_SYSTEM_PROMPT

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