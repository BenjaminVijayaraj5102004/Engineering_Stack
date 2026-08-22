"""Dynamic Model Context Protocol (MCP) Server Registry.

Manages runtime in-memory server configurations, environment variable expansion,
and optional JSON persistence (mcp.json).
"""

import json
import os
import re
from pathlib import Path
from typing import Any, Optional
from dotenv import load_dotenv
from ..util.config import settings
from ..util.logger import get_logger

load_dotenv()
logger = get_logger(__name__)

DEFAULT_CONFIG_PATH = Path(__file__).parent / "config" / "mcp.json"
LEGACY_CONFIG_PATH = Path(__file__).parent / "config" / "github.json"


def _expand_env_vars(value: Any) -> Any:
    """Recursively expand environment variables formatted as ${VAR_NAME} or $VAR_NAME."""
    if isinstance(value, str):
        # Match ${VAR_NAME} or ${input:VAR_NAME}
        pattern = re.compile(r"\$\{(?:input:)?([A-Za-z0-9_]+)\}")

        def replace_match(match):
            var_name = match.group(1)
            # Try settings first, then os.environ
            if hasattr(settings, var_name) and getattr(settings, var_name):
                return str(getattr(settings, var_name))
            val = os.getenv(var_name)
            if val is not None:
                return val
            if var_name == "github_mcp_pat" or var_name == "GITHUB_ACCESS_TOKEN":
                return getattr(settings, "GITHUB_ACCESS_TOKEN", "") or "dummy_token"
            return match.group(0)

        expanded = pattern.sub(replace_match, value)
        return os.path.expandvars(expanded)
    elif isinstance(value, dict):
        return {k: _expand_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_expand_env_vars(item) for item in value]
    return value


class MCPRegistry:
    """In-memory runtime MCP registry with optional file persistence."""

    def __init__(self, config_path: Optional[Path | str] = None):
        self.config_path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
        self._in_memory_servers: dict[str, dict[str, Any]] = {}

    def load_config_file(self, path: Optional[Path | str] = None) -> dict[str, Any]:
        """Load and parse configuration from disk (mcp.json, github.json, meniscus.json, etc.)."""
        servers = {}

        if path:
            target_path = Path(path)
            files_to_load = [target_path] if target_path.exists() else []
        else:
            config_dir = self.config_path.parent
            files_to_load = []
            if config_dir.exists() and config_dir.is_dir():
                # Load individual server configs first (e.g. github.json, meniscus.json)
                for f in sorted(config_dir.glob("*.json")):
                    if f.name != "mcp.json":
                        files_to_load.append(f)
            # Load main mcp.json last so it can override or aggregate
            if self.config_path.exists():
                files_to_load.append(self.config_path)
            elif LEGACY_CONFIG_PATH.exists() and LEGACY_CONFIG_PATH not in files_to_load:
                files_to_load.append(LEGACY_CONFIG_PATH)

        for file_path in files_to_load:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    if "mcpServers" in data and isinstance(data["mcpServers"], dict):
                        servers.update(data["mcpServers"])
                    if "servers" in data and isinstance(data["servers"], dict):
                        servers.update(data["servers"])
            except Exception as exc:
                logger.warning("Failed to load MCP config from %s: %s", file_path, exc)

        return {"mcpServers": servers}

    def save_config_file(
        self,
        config: dict[str, Any],
        path: Optional[Path | str] = None,
    ) -> None:
        """Persist configuration dictionary to disk."""
        target_path = Path(path) if path else self.config_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

    def normalize_server_config(self, config_or_url: dict[str, Any] | str) -> dict[str, Any]:
        """Normalize a server config input (URL string or dict) into standard schema."""
        if isinstance(config_or_url, str):
            url = config_or_url.strip()
            transport = "sse" if "/sse" in url else "http"
            return {
                "type": transport,
                "url": url,
                "headers": {},
            }
        elif isinstance(config_or_url, dict):
            norm = dict(config_or_url)
            if "command" in norm:
                norm["type"] = norm.get("type", "stdio")
            elif "url" in norm:
                url = norm["url"]
                if "type" not in norm:
                    norm["type"] = "sse" if "/sse" in url else "http"
            return norm
        else:
            raise ValueError(f"Invalid server configuration type: {type(config_or_url)}")

    def add_server(
        self,
        name: str,
        config: dict[str, Any] | str,
        persist: bool = False,
    ) -> dict[str, Any]:
        """Add or update an MCP server in the runtime registry.
        
        Args:
            name: Unique server identifier (e.g. 'postgres', 'filesystem', 'github').
            config: Server URL string or configuration dictionary.
            persist: If True, writes update to mcp.json; default False (in-memory only).
        """
        normalized = self.normalize_server_config(config)
        self._in_memory_servers[name] = normalized
        logger.info("Added MCP server '%s' to in-memory registry (persist=%s)", name, persist)

        if persist:
            current = self.load_config_file()
            current_servers = current.setdefault("mcpServers", {})
            current_servers[name] = normalized
            self.save_config_file(current)

        return normalized

    def remove_server(self, name: str, persist: bool = False) -> bool:
        """Remove an MCP server from the registry.
        
        Args:
            name: Server identifier to remove.
            persist: If True, removes from disk mcp.json as well.
        """
        removed = False
        if name in self._in_memory_servers:
            del self._in_memory_servers[name]
            removed = True

        if persist:
            current = self.load_config_file()
            current_servers = current.get("mcpServers", {})
            if name in current_servers:
                del current_servers[name]
                self.save_config_file(current)
                removed = True

        logger.info("Removed MCP server '%s' (success=%s, persist=%s)", name, removed, persist)
        return removed

    def get_server_config(self, name: str) -> Optional[dict[str, Any]]:
        """Retrieve resolved configuration for a named server, expanding environment variables."""
        config: Optional[dict[str, Any]] = None

        # Check in-memory registrations first
        if name in self._in_memory_servers:
            config = dict(self._in_memory_servers[name])
        else:
            # Fallback to disk configuration
            disk_config = self.load_config_file()
            servers = disk_config.get("mcpServers", {})
            if name in servers:
                config = dict(servers[name])

        if config is not None:
            return _expand_env_vars(config)

        return None

    def list_servers(self) -> dict[str, dict[str, Any]]:
        """List all registered MCP servers (combining disk and in-memory registrations)."""
        disk_config = self.load_config_file()
        all_servers = dict(disk_config.get("mcpServers", {}))
        all_servers.update(self._in_memory_servers)
        return {k: _expand_env_vars(v) for k, v in all_servers.items()}

    def reset(self) -> None:
        """Reset in-memory server registrations."""
        self._in_memory_servers.clear()

    @staticmethod
    def classify_domain(
        server_name: str,
        tool_names: Optional[list[str]] = None,
        description: Optional[str] = None,
    ) -> str:
        """Classify the agent domain for routing based on server and tool metadata."""
        text = f"{server_name} {' '.join(tool_names or [])} {description or ''}".lower()

        if any(k in text for k in ["postgres", "mysql", "sqlite", "oracle", "sql", "rdbms", "mariadb"]):
            return "rdbms"
        if any(k in text for k in ["mongo", "dynamo", "couch", "cassandra", "nosql"]):
            return "nosql"
        if any(k in text for k in ["redis", "keyvalue", "valkey", "memcached"]):
            return "redis"
        if any(k in text for k in ["graphql", "gql"]):
            return "graphql"
        if any(k in text for k in ["grpc", "protobuf", "proto"]):
            return "grpc"
        if any(k in text for k in ["soap", "wsdl"]):
            return "soap"
        if any(k in text for k in ["rest", "openapi", "swagger", "http_api", "endpoint"]):
            return "rest"
        if any(k in text for k in ["github", "gitlab", "bitbucket", "git", "repo", "coding"]):
            return "coding"
        if any(k in text for k in ["meniscus", "memory", "long_term_memory", "recall", "log_memory"]):
            return "memory"

        return "custom"


# Global default registry instance
global_registry = MCPRegistry()


def load_mcp_config(path: Optional[Path | str] = None) -> dict[str, Any]:
    """Load MCP configuration from disk."""
    return global_registry.load_config_file(path)


def save_mcp_config(config: dict[str, Any], path: Optional[Path | str] = None) -> None:
    """Save MCP configuration to disk."""
    global_registry.save_config_file(config, path)


def add_server(
    name: str,
    config: dict[str, Any] | str,
    persist: bool = False,
) -> dict[str, Any]:
    """Register an MCP server dynamically."""
    return global_registry.add_server(name, config, persist=persist)


def remove_server(name: str, persist: bool = False) -> bool:
    """Remove an MCP server from the registry."""
    return global_registry.remove_server(name, persist=persist)


def get_server_config(name: str) -> Optional[dict[str, Any]]:
    """Get resolved configuration for a server."""
    return global_registry.get_server_config(name)


def list_servers() -> dict[str, dict[str, Any]]:
    """List all registered MCP servers."""
    return global_registry.list_servers()


def classify_domain(
    server_name: str,
    tool_names: Optional[list[str]] = None,
    description: Optional[str] = None,
) -> str:
    """Classify the domain of an MCP server."""
    return MCPRegistry.classify_domain(server_name, tool_names, description)
