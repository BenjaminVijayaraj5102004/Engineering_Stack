"""Automated LangGraph BaseStore factory with preloaded organizational standards and policies."""

from langgraph.store.memory import InMemoryStore
from langgraph.store.base import BaseStore
from ..util.logger import get_logger

logger = get_logger(__name__)


def build_default_store() -> BaseStore:
    """Build and initialize an automated BaseStore preloaded with organizational engineering standards."""
    store = InMemoryStore()

    # Preload organizational engineering and architectural standards into RAG memory
    store.put(
        ("org_standards",),
        "database_policy.md",
        {
            "content": (
                "Org Technical Standard DB-202: PostgreSQL is the primary relational database standard for the organization. "
                "All database tables must use UUID primary keys. "
                "Production environments must strictly enforce sslmode=require and connection pooling (PgBouncer)."
            )
        },
    )
    store.put(
        ("org_standards",),
        "api_policy.md",
        {
            "content": (
                "Org Technical Standard API-101: All REST APIs must follow OpenAPI 3.1 specifications, "
                "use semantic HTTP status codes, and enforce JWT bearer token authentication with RBAC."
            )
        },
    )
    store.put(
        ("org_standards",),
        "security_policy.md",
        {
            "content": (
                "Org Security Standard SEC-301: Secrets, tokens, and credentials must NEVER be committed to repositories. "
                "Use environment variables or cloud secret managers with automated rotation."
            )
        },
    )

    logger.info("Initialized automated default knowledge base store with organizational standards.")
    return store
