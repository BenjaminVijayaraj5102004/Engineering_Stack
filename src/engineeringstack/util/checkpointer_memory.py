from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.memory import MemorySaver

from .config import settings
from .logger import get_logger

logger = get_logger(__name__)

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
        logger.warning("Postgres Checkpointer failed to initialize (%s). Falling back to MemorySaver.", e)
        checkpointer = MemorySaver()
else:
    checkpointer = MemorySaver()
