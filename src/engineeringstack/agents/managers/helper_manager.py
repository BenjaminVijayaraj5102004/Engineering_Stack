from typing import Any, Optional
from ...prompts.helper_prompt import HELPER_MANAGER_SYSTEM_PROMPT
from ...builders.helper_builder import build_helper_manager, helper_manager, helping_subagent, graph
from ...util.logger import get_logger

logger = get_logger(__name__)


def helper_manager_subagent(
    model: Optional[Any] = None,
    backend: Optional[Any] = None,
    skills: Optional[list[str]] = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build the Helper Manager subagent dictionary dynamically with custom model and skill support."""
    logger.info("Initializing Helper Manager")
    return {
        "name": "Helper_Manager",
        "description": "Router only: Routes standalone code requests (single table, schema, endpoint, algorithm, script, bug fix) and code reviews through Coding_Agent and Code_Reviewer. Never implements directly.",
        "system_prompt": HELPER_MANAGER_SYSTEM_PROMPT,
        "runnable": build_helper_manager(
            model=model,
            backend=backend,
            skills=skills,
        ),
    }


__all__ = [
    "helper_manager_subagent",
    "build_helper_manager",
    "helper_manager",
    "helping_subagent",
    "graph",
]
