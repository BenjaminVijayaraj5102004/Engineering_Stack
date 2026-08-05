from langchain.tools import tool
import asyncio
from langsmith import traceable
from ..mcp.client import get_github_client


@tool
@traceable(name="search_code_mcp", run_type="tool")
def search_code(query: str) -> str:
    """Search GitHub code."""
    print(f"[TOOL] search_code called with query: {query}")

    async def run():
        async with get_github_client() as session:
            return await session.call_tool(
                "search_code",
                {"query": query},
            )

    return asyncio.run(run())


@tool
@traceable(name="get_file_contents_mcp", run_type="tool")
def get_file_contents(path: str) -> str:
    """Get file content."""
    print(f"[TOOL] get_file_contents called for path: {path}")

    async def run():
        async with get_github_client() as session:
            return await session.call_tool(
                "get_file_contents",
                {"path": path},
            )

    return asyncio.run(run())
