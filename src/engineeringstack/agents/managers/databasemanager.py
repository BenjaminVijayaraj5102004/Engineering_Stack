from typing import Any, Optional
from ...prompts.db_prompt import DATABASE_MANAGER_SYSTEM_PROMPT
from ...builders.db_builder import build_database_manager
from ...util.logger import get_logger

logger = get_logger(__name__)


def database_manager_subagent(
    model: Optional[Any] = None,
    backend: Optional[Any] = None,
    skills: Optional[list[str]] = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build the Database Manager subagent dictionary dynamically with custom model and skill support."""
    logger.info("Initializing Database Manager")
    return {
        "name": "Database_Manager",
        "description": "Router only: Routes multi-database architecture and persistence for entire applications (RDBMS_agent, NoSQL_agent, REDIS_agent) with Code_Reviewer QA. Never used for single standalone tables.",
        "system_prompt": DATABASE_MANAGER_SYSTEM_PROMPT,
        "runnable": build_database_manager(
            model=model,
            backend=backend,
            skills=skills,
        ),
    }
