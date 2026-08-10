import asyncio
import concurrent.futures
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


@tool
@traceable(name="search_code_mcp", run_type="tool")
def search_code(query: str) -> str:
    """Search GitHub code."""
    logger.debug("[TOOL] search_code called with query: %s", query)

    async def run():
        async with get_github_client() as session:
            return await session.call_tool(
                "search_code",
                {"query": query},
            )

    return _run_async_safely(run())


@tool
@traceable(name="get_file_contents_mcp", run_type="tool")
def get_file_contents(path: str) -> str:
    """Get file content."""
    logger.debug("[TOOL] get_file_contents called for path: %s", path)

    async def run():
        async with get_github_client() as session:
            return await session.call_tool(
                "get_file_contents",
                {"path": path},
            )

    return _run_async_safely(run())
