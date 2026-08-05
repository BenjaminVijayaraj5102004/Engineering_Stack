from ...prompts.db_prompt import DATABASE_MANAGER_SYSTEM_PROMPT
from ...builders.db_builder import build_database_manager
from ...util.logger import get_logger

logger = get_logger(__name__)

logger.info("Initializing Database Manager")

database_manager_subagent = {
    "name": "Database_Manager",
    "description": "Router only. Delegates database requests to RDMS_agent, NoSQL_agent, or REDIS_agent. Never implements databases.",
    "system_prompt": DATABASE_MANAGER_SYSTEM_PROMPT,
    "runnable": build_database_manager(),
}
