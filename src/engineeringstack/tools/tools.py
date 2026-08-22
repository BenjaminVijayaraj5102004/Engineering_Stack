import asyncio
import concurrent.futures
import json
from typing import Any, Optional
from langchain.tools import tool
from langsmith import traceable
from ..mcp.client import get_github_client, get_meniscus_client
from ..util.logger import get_logger

logger = get_logger(__name__)


def _run_async_safely(coro):
    """Run an async coroutine synchronously even if already within a running event loop."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    else:
        return asyncio.run(coro)


def _extract_mcp_result_text(result: Any, max_items: int = 5) -> str:
    """Extract string content from MCP CallToolResult items (TextContent, EmbeddedResource, etc.)."""
    if hasattr(result, "content") and isinstance(result.content, list):
        text_parts = []
        for item in result.content:
            text = ""
            if hasattr(item, "text") and item.text:
                text = str(item.text)
            elif hasattr(item, "resource") and hasattr(item.resource, "text") and item.resource.text:
                text = str(item.resource.text)
            else:
                text = str(item)

            # If it's a raw GitHub search JSON, format concisely to save context tokens
            try:
                data = json.loads(text)
                if isinstance(data, dict) and "items" in data:
                    items = data.get("items", [])[:max_items]
                    summary_items = []
                    for idx, it in enumerate(items, 1):
                        path = it.get("path", "")
                        repo = it.get("repository", {}).get("full_name", "") if isinstance(it.get("repository"), dict) else str(it.get("repository", ""))
                        summary_items.append(f"{idx}. {path} (repo: {repo})")
                    text = f"Found {data.get('total_count', len(items))} matches (showing top {len(summary_items)}):\n" + "\n".join(summary_items)
            except Exception:
                pass

            text_parts.append(text)
        return "\n".join(text_parts) if text_parts else str(result)
    return str(result)


@tool
@traceable(name="search_code_mcp", run_type="tool")
def search_code(query: str) -> str:
    """Search GitHub code via MCP.
    
    Args:
        query: GitHub search query (e.g. 'FastAPI repo:tiangolo/fastapi' or 'langgraph').
    """
    logger.info("[TOOL] search_code invoked with query: %s", query)

    async def run():
        async with get_github_client() as session:
            res = await session.call_tool(
                "search_code",
                {"query": query},
            )
            return _extract_mcp_result_text(res)

    try:
        return _run_async_safely(asyncio.wait_for(run(), timeout=5.0))
    except Exception as exc:
        logger.warning("[TOOL] search_code exception: %s", exc)
        return f"[GitHub MCP search_code: {exc}]"


@tool
@traceable(name="get_file_contents_mcp", run_type="tool")
def get_file_contents(
    path: str = "/",
    owner: Optional[str] = None,
    repo: Optional[str] = None,
) -> str:
    """Get file or directory contents from a GitHub repository via MCP.
    
    Args:
        path: Path to file or directory within the repository (default '/').
        owner: GitHub repository owner (username or organization).
        repo: GitHub repository name.
    """
    logger.info("[TOOL] get_file_contents invoked for path=%s, owner=%s, repo=%s", path, owner, repo)

    # If owner/repo not passed directly, try extracting from path like "owner/repo/path/to/file"
    if not owner or not repo:
        parts = path.strip("/").split("/", 2)
        if len(parts) >= 2 and not owner and not repo:
            owner, repo = parts[0], parts[1]
            path = parts[2] if len(parts) == 3 else "/"

    async def run():
        async with get_github_client() as session:
            params = {
                "owner": owner or "langchain-ai",
                "repo": repo or "langgraph",
                "path": path,
            }
            res = await session.call_tool("get_file_contents", params)
            return _extract_mcp_result_text(res)

    try:
        return _run_async_safely(asyncio.wait_for(run(), timeout=5.0))
    except Exception as exc:
        logger.warning("[TOOL] get_file_contents exception: %s", exc)
        return f"[GitHub MCP get_file_contents: {exc}]"


@tool
@traceable(name="meniscus_recall_mcp", run_type="tool")
def meniscus_recall(
    query: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    around: Optional[str] = None,
    source_event: Optional[int] = None,
    limit: int = 30,
) -> str:
    """Read and retrieve from Meniscus long-term memory.
    
    Supports topic keyword/semantic search (`query`), date range filtering (`start`, `end`),
    episodic session reconstruction (`around`), or inspecting original raw source events (`source_event`).
    
    Args:
        query: Topic keywords or question to search relevant memory (e.g. 'sqlite choice', 'auth bug').
        start: Start date in ISO-8601 format (YYYY-MM-DD).
        end: End date in ISO-8601 format (YYYY-MM-DD).
        around: Topic or ISO date to reconstruct the whole contiguous session around that moment.
        source_event: Event ID from a returned fact to retrieve verbatim raw event text.
        limit: Maximum number of facts to return (default 30).
    """
    logger.info(
        "[TOOL] meniscus_recall invoked: query=%s, start=%s, end=%s, around=%s, source_event=%s, limit=%s",
        query, start, end, around, source_event, limit
    )

    async def run():
        async with get_meniscus_client(timeout=15.0) as session:
            params: dict[str, Any] = {"limit": limit}
            if query is not None:
                params["query"] = query
            if start is not None:
                params["start"] = start
            if end is not None:
                params["end"] = end
            if around is not None:
                params["around"] = around
            if source_event is not None:
                params["source_event"] = source_event

            res = await session.call_tool("meniscus_recall", params)
            return _extract_mcp_result_text(res)

    try:
        return _run_async_safely(asyncio.wait_for(run(), timeout=30.0))
    except asyncio.TimeoutError:
        logger.warning("[TOOL] meniscus_recall timed out after 30s")
        return "[Meniscus MCP meniscus_recall error: operation timed out]"
    except Exception as exc:
        logger.warning("[TOOL] meniscus_recall exception: %s", exc)
        return f"[Meniscus MCP meniscus_recall: {exc}]"


@tool
@traceable(name="meniscus_log_mcp", run_type="tool")
def meniscus_log(
    content: str,
    source: str = "mcp",
) -> str:
    """Record and store knowledge, decisions, preferences, or conversation turns into Meniscus long-term memory.
    
    Args:
        content: The text, note, decision, or observation to record into memory.
        source: Source identifier for provenance (default 'mcp').
    """
    logger.info("[TOOL] meniscus_log invoked: source=%s, length=%d", source, len(content))

    async def run():
        async with get_meniscus_client(timeout=15.0) as session:
            res = await session.call_tool(
                "meniscus_log",
                {"content": content, "source": source},
            )
            return _extract_mcp_result_text(res)

    try:
        return _run_async_safely(asyncio.wait_for(run(), timeout=30.0))
    except asyncio.TimeoutError:
        logger.warning("[TOOL] meniscus_log timed out after 30s")
        return "[Meniscus MCP meniscus_log error: operation timed out]"
    except Exception as exc:
        logger.warning("[TOOL] meniscus_log exception: %s", exc)
        return f"[Meniscus MCP meniscus_log: {exc}]"


_ACTIVE_STORE: Optional[Any] = None


def set_active_store(store: Any) -> None:
    """Set the active BaseStore instance for RAG memory tools."""
    global _ACTIVE_STORE
    _ACTIVE_STORE = store


def get_active_store() -> Optional[Any]:
    """Get the active BaseStore instance."""
    return _ACTIVE_STORE


@tool
@traceable(name="search_knowledge_base", run_type="tool")
def search_knowledge_base(query: str) -> str:
    """Search internal organizational knowledge base documents, policies, and technical standards (RAG memory).
    
    Args:
        query: Search keywords or topic to find in organizational documentation and standards (e.g. 'postgres', 'security standard SEC-101', 'auth rate limit').
    """
    logger.info("[TOOL] search_knowledge_base invoked: query=%s", query)
    store = get_active_store()
    if store is None:
        return "No organizational knowledge base store is currently attached."

    try:
        results = []
        # Attempt semantic/text search if supported by store
        if hasattr(store, "search"):
            items = store.search(tuple(), query=query, limit=10)
            if not items:
                # Fallback to search without query filter if query parsing didn't match
                items = store.search(tuple(), limit=20)
            for it in items:
                val = getattr(it, "value", it)
                key = getattr(it, "key", "item")
                ns = getattr(it, "namespace", ())
                ns_str = "/".join(ns) if isinstance(ns, (list, tuple)) else str(ns)
                results.append(f"[{ns_str}/{key}]: {val}")
        elif hasattr(store, "_data"):
            for k, v in store._data.items():
                results.append(f"[{k}]: {v}")

        if results:
            return "Found Knowledge Base Documents:\n" + "\n\n".join(results)
        return f"No organizational documents found matching '{query}'."
    except Exception as exc:
        logger.warning("[TOOL] search_knowledge_base exception: %s", exc)
        return f"[Knowledge base error: {exc}]"


def get_domain_tools(
    domain: str,
    extra_tools: Optional[list[Any]] = None,
) -> list[Any]:
    """Automatically resolve and return domain-specific tools for any specialist agent.
    
    Combines:
    1. Base tools (search_code, get_file_contents, meniscus_recall, meniscus_log).
    2. Any dynamic MCP tools discovered for this domain from mcp.json / registry.
    """
    from .mcp_tools import get_domain_mcp_tools

    base_tools: list[Any] = [search_code, get_file_contents, meniscus_recall]
    if domain in ("coding", "helper"):
        base_tools.append(meniscus_log)

    domain_mcp_tools = get_domain_mcp_tools(domain)
    all_tools = list(base_tools) + list(domain_mcp_tools)

    if extra_tools:
        all_tools.extend(extra_tools)
    return all_tools



