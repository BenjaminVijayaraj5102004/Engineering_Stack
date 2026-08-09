from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.memory import MemorySaver

from .config import settings

checkpointer = None

if settings.DATABASE_URL:
    try:
        pool = ConnectionPool(
            conninfo=settings.DATABASE_URL,
            max_size=20,
            open=True,
            kwargs={"autocommit": True},
        )
        checkpointer = PostgresSaver(pool)
        checkpointer.setup()
    except Exception as e:
        print(f"[WARNING] Postgres Checkpointer failed to initialize ({e}). Falling back to MemorySaver.")
        checkpointer = MemorySaver()
else:
    checkpointer = MemorySaver()
