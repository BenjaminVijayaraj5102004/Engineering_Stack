from typing import Any
from langchain.agents.middleware import AgentMiddleware
from deepagents.middleware.filesystem import FilesystemMiddleware


class NoOpMiddleware(AgentMiddleware):
    """Pass-through middleware to disable/deny default built-in middlewares like Anthropic prompt caching."""

    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def wrap_model_call(self, request: Any, handler: Any) -> Any:
        return handler(request)

    async def awrap_model_call(self, request: Any, handler: Any) -> Any:
        return await handler(request)


def create_router_middleware(backend: Any) -> list[AgentMiddleware]:
    """Create middleware stack for router agents (Main Agent, Managers).
    
    Exposes only `read_file` (for skills/memory) alongside `task` tool.
    """
    return [
        FilesystemMiddleware(backend=backend, tools=["read_file"]),
        NoOpMiddleware("AnthropicPromptCachingMiddleware"),
    ]


def create_worker_middleware(backend: Any) -> list[AgentMiddleware]:
    """Create middleware stack for worker subagents (Coding, DB, API).
    
    Exposes full filesystem tools (read_file, write_file, edit_file, glob, grep),
    disables task delegation, and disables prompt caching.
    """
    return [
        FilesystemMiddleware(backend=backend, tools=["read_file", "write_file", "edit_file", "glob", "grep"]),
        NoOpMiddleware("SubAgentMiddleware"),
        NoOpMiddleware("AnthropicPromptCachingMiddleware"),
    ]


def create_reviewer_middleware(backend: Any) -> list[AgentMiddleware]:
    """Create middleware stack for reviewer subagent (Code_Reviewer).
    
    Exposes full filesystem tools (read_file, write_file, edit_file, glob, grep),
    disables task delegation, and disables prompt caching.
    """
    return [
        FilesystemMiddleware(backend=backend, tools=["read_file", "write_file", "edit_file", "glob", "grep"]),
        NoOpMiddleware("SubAgentMiddleware"),
        NoOpMiddleware("AnthropicPromptCachingMiddleware"),
    ]

