from typing import Any, Optional
from ...prompts.db_prompt import DATABASE_MANAGER_SYSTEM_PROMPT
from ...builders.db_builder import build_database_manager
from ...schema.state import MainAgentOutput
from ...util.logger import get_logger

logger = get_logger(__name__)


def database_manager_subagent(
    model: Optional[Any] = None,
    backend: Optional[Any] = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build the Database Manager subagent dictionary dynamically with custom model support."""
    logger.info("Initializing Database Manager")
    return {
        "name": "Database_Manager",
        "description": "Router only. Delegates database requests to RDMS_agent, NoSQL_agent, or REDIS_agent. Never implements databases.",
        "system_prompt": DATABASE_MANAGER_SYSTEM_PROMPT,
        "runnable": build_database_manager(
            model=model,
            backend=backend,
        ),
    }



