from builders.api_builder import build_api_manager
from prompts.api_prompt import API_MANAGER_SYSTEM_PROMPT


api_manager_subagent = {
    "name": "API_Manager",
    "description": (
        "Routes API-related requests to the appropriate specialist "
        "(REST, GraphQL, gRPC, SOAP)."
    ),
    "system_prompt": API_MANAGER_SYSTEM_PROMPT,
    "runnable": build_api_manager(),
}