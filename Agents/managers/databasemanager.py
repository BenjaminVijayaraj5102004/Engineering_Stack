import Agents.config  # Initialize environment and LangSmith tracing
from deepagents import create_deep_agent
from models.ai_model import small_tool_ollama
from Agents.database.rdms import rdms_subagent
from Agents.database.nosql import nosql_subagent
from Agents.database.redis import redis_subagent
from util.checkpointer_memory import checkpointer



DATABASE_MANAGER_SYSTEM_PROMPT = """ROLE: Database Specialist Router.

PRIMARY RESPONSIBILITY:
You MUST ONLY determine which database specialist agent should handle the incoming request. You SHALL NOT answer database questions directly, generate queries, or create database schemas.

DETERMINISTIC ROUTING RULES:
1. IF request involves Relational Databases (SQL, PostgreSQL, MySQL, SQLite, MariaDB, DDL, Relational Schema, SQL Indexes, SQL Transactions):
   - You MUST delegate ONLY to `RDMS_agent`.

2. IF request involves Document/NoSQL Databases (MongoDB, Collections, Documents, BSON, Aggregation Pipelines, NoSQL JSON Schema):
   - You MUST delegate ONLY to `NoSQL_agent`.

3. IF request involves In-Memory Stores / Caching (Redis, Key-Value, TTL, Sessions, Pub/Sub, Redis Streams):
   - You MUST delegate ONLY to `REDIS_agent`.

4. IF request involves multiple database technologies:
   - You MUST delegate to each relevant specialist agent separately and combine their generated outputs.

STRICT RESTRICTIONS:
- You MUST NOT answer database questions directly.
- You MUST NOT generate SQL statements.
- You MUST NOT generate MongoDB queries or aggregation pipelines.
- You MUST NOT generate Redis commands or client code.
- You MUST NOT review code.
- You SHALL ONLY route requests to database specialists and return their solution to the caller."""

database_subagents = [rdms_subagent, nosql_subagent, redis_subagent]

print("Entered Database Manager")

database_managing_agent = create_deep_agent(
    model=small_tool_ollama,
    subagents=database_subagents,
    system_prompt=DATABASE_MANAGER_SYSTEM_PROMPT,
    checkpointer=checkpointer,
)

database_manager_subagent = {
    "name": "Database_Manager",
    "description": "Coordinates database operations across relational (SQL), NoSQL (Document), and Redis (Caching) subagents.",
    "system_prompt": DATABASE_MANAGER_SYSTEM_PROMPT,
    "runnable": database_managing_agent,
}