from typing import Any, Optional
from ...builders.api_builder import build_api_manager
from ...prompts.api_prompt import API_MANAGER_SYSTEM_PROMPT
from ...util.logger import get_logger

logger = get_logger(__name__)


def api_manager_subagent(
    model: Optional[Any] = None,
    backend: Optional[Any] = None,
    skills: Optional[list[str]] = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build the API Manager subagent dictionary dynamically with custom model and skill support."""
    logger.info("Initializing API Manager")
    return {
        "name": "API_Manager",
        "description": "Router only: Routes multi-protocol API suites and services for entire applications (REST_Agent, GraphQL_Agent, GRPC_Agent, SOAP_Agent) with Code_Reviewer QA. Never used for single standalone endpoints.",
        "system_prompt": API_MANAGER_SYSTEM_PROMPT,
        "runnable": build_api_manager(
            model=model,
            backend=backend,
            skills=skills,
        ),
    }
