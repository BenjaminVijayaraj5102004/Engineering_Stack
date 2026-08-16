import asyncio
import concurrent.futures
import json
from typing import Any, Optional
from langchain.tools import tool
from langsmith import traceable
from ..mcp.client import get_github_client
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
