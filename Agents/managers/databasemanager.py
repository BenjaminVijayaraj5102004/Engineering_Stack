import Agents.config  # Initialize environment and LangSmith tracing
from prompts.db_prompt import DATABASE_MANAGER_SYSTEM_PROMPT
from builders.db_builder import build_database_manager


database_manager_subagent = {
    "name": "Database_Manager",
    "description": "Coordinates database operations across relational (SQL), NoSQL (Document), and Redis (Caching) subagents.",
    "system_prompt": DATABASE_MANAGER_SYSTEM_PROMPT,
    "runnable": build_database_manager(),
}