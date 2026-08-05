from ...builders.api_builder import build_api_manager
from ...prompts.api_prompt import API_MANAGER_SYSTEM_PROMPT
from ...util.logger import get_logger

logger = get_logger(__name__)

logger.info("Initializing API Manager")

api_manager_subagent = {
    "name": "API_Manager",
    "description": "Router only. Delegates API requests to REST_Agent, GraphQL_Agent, GRPC_Agent, or SOAP_Agent. Never implements APIs.",
    "system_prompt": API_MANAGER_SYSTEM_PROMPT,
    "runnable": build_api_manager(),
}
