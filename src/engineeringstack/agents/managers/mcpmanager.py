from typing import Any, Optional
from ...builders.mcp_builder import build_mcp_manager, mcp_manager, mcp_subagent, graph
from ...prompts.mcp_prompt import MCP_MANAGER_SYSTEM_PROMPT
from ...util.logger import get_logger

logger = get_logger(__name__)


def mcp_manager_subagent(
    model: Optional[Any] = None,
    backend: Optional[Any] = None,
    skills: Optional[list[str]] = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Build the MCP Manager subagent dictionary dynamically with custom model and skill support."""
    logger.info("Initializing MCP Manager")
    return {
        "name": "MCP_Manager",
        "description": "Provisions and configures custom MCP (Model Context Protocol) servers, generating config JSON, client modules, MCP tool wrappers, and dedicated subagents via write_file.",
        "system_prompt": MCP_MANAGER_SYSTEM_PROMPT,
        "runnable": build_mcp_manager(
            model=model,
            backend=backend,
            skills=skills,
        ),
    }


__all__ = [
    "mcp_manager_subagent",
    "build_mcp_manager",
    "mcp_manager",
    "mcp_subagent",
    "graph",
]
