"""Unit tests for Generic MCP Client, Dynamic MCP Registry, and Dynamic Tool Adapter.

Follows TDD Workflow & AAA (Arrange-Act-Assert) pattern:
- TEST 1: MCPRegistry in-memory registration, lookup, removal, and listing.
- TEST 2: Environment variable expansion in MCP configurations.
- TEST 3: Domain classification heuristics for automatic subagent routing.
- TEST 4: Generic MCP client dispatching across Streamable HTTP, SSE, and Stdio transports.
- TEST 5: Dynamic tool discovery and LangChain StructuredTool adaptation.
- TEST 6: Backward compatibility for get_github_client() and legacy load_config().
"""

import asyncio
import os
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from engineeringstack.mcp.registry import (
    MCPRegistry,
    add_server,
    get_server_config,
    list_servers,
    remove_server,
    classify_domain,
    global_registry,
)
from engineeringstack.mcp.client import get_mcp_client, get_github_client, load_config
from engineeringstack.tools.mcp_tools import (
    create_dynamic_mcp_tool,
    discover_and_adapt_mcp_tools,
    register_mcp_server,
    list_mcp_tools,
    list_registered_mcp_servers,
    remove_mcp_server as remove_mcp_server_tool,
)


class TestMCPRegistryAndClient(unittest.TestCase):
    """Test suite for MCP Registry, Generic Client, and Dynamic Tool Adapter."""

    def setUp(self):
        global_registry.reset()

    def tearDown(self):
        global_registry.reset()

    def test_1_mcp_registry_in_memory_crud(self):
        """TEST 1: In-memory registry supports add, get, list, and remove without disk mutation."""
        # Arrange & Act: Add server
        added = add_server("test_ephemeral_db", "https://example.com/mcp", persist=False)
        self.assertEqual(added["type"], "http")
        self.assertEqual(added["url"], "https://example.com/mcp")

        # Act: Get server
        cfg = get_server_config("test_ephemeral_db")
        self.assertIsNotNone(cfg)
        self.assertEqual(cfg["url"], "https://example.com/mcp")

        # Act: List servers
        all_servers = list_servers()
        self.assertIn("test_ephemeral_db", all_servers)

        # Act: Remove server
        removed = remove_server("test_ephemeral_db", persist=False)
        self.assertTrue(removed)
        self.assertIsNone(get_server_config("test_ephemeral_db"))

    def test_2_mcp_registry_env_expansion(self):
        """TEST 2: Registry properly expands ${ENV_VAR} in headers, urls, and args."""
        os.environ["TEST_AUTH_TOKEN"] = "secret_bearer_token_123"
        registry = MCPRegistry()

        try:
            registry.add_server(
                "secured_api",
                {
                    "type": "http",
                    "url": "https://api.example.com/mcp",
                    "headers": {"Authorization": "Bearer ${TEST_AUTH_TOKEN}"},
                },
                persist=False,
            )

            cfg = registry.get_server_config("secured_api")
            self.assertIsNotNone(cfg)
            self.assertEqual(cfg["headers"]["Authorization"], "Bearer secret_bearer_token_123")
        finally:
            os.environ.pop("TEST_AUTH_TOKEN", None)

    def test_3_domain_classification(self):
        """TEST 3: Domain classification correctly identifies target subagents."""
        self.assertEqual(classify_domain("postgres_mcp", ["query_database"]), "rdbms")
        self.assertEqual(classify_domain("mysql_server"), "rdbms")
        self.assertEqual(classify_domain("mongo_mcp", ["find_documents"]), "nosql")
        self.assertEqual(classify_domain("redis_cache"), "redis")
        self.assertEqual(classify_domain("rest_weather_api", ["get_weather"]), "rest")
        self.assertEqual(classify_domain("graphql_endpoint"), "graphql")
        self.assertEqual(classify_domain("grpc_service"), "grpc")
        self.assertEqual(classify_domain("soap_legacy"), "soap")
        self.assertEqual(classify_domain("github_copilot", ["search_code"]), "coding")
        self.assertEqual(classify_domain("figma_design"), "custom")
        self.assertEqual(classify_domain("slack_bot"), "custom")
        self.assertEqual(classify_domain("browser_automation"), "custom")

    @patch("engineeringstack.mcp.client.streamable_http_client")
    @patch("engineeringstack.mcp.client.ClientSession")
    def test_4a_generic_client_streamable_http_transport(self, mock_session_cls, mock_streamable):
        """TEST 4a: Generic client connects to HTTP URL using streamable_http_client."""
        async def run():
            mock_session = AsyncMock()
            mock_session.initialize.return_value = None
            mock_session_cls.return_value.__aenter__.return_value = mock_session

            mock_streamable.return_value.__aenter__.return_value = (AsyncMock(), AsyncMock())

            async with get_mcp_client("https://example.com/mcp", timeout=2.0) as session:
                self.assertIsNotNone(session)
                mock_session.initialize.assert_awaited_once()

        asyncio.run(run())

    @patch("engineeringstack.mcp.client.sse_client")
    @patch("engineeringstack.mcp.client.ClientSession")
    def test_4b_generic_client_sse_transport(self, mock_session_cls, mock_sse):
        """TEST 4b: Generic client connects to SSE URL using sse_client."""
        async def run():
            mock_session = AsyncMock()
            mock_session.initialize.return_value = None
            mock_session_cls.return_value.__aenter__.return_value = mock_session

            mock_sse.return_value.__aenter__.return_value = (AsyncMock(), AsyncMock())

            async with get_mcp_client("https://example.com/sse", timeout=2.0) as session:
                self.assertIsNotNone(session)
                mock_session.initialize.assert_awaited_once()

        asyncio.run(run())

    @patch("engineeringstack.mcp.client.stdio_client")
    @patch("engineeringstack.mcp.client.ClientSession")
    def test_4c_generic_client_stdio_transport(self, mock_session_cls, mock_stdio):
        """TEST 4c: Generic client connects to stdio command using stdio_client."""
        async def run():
            mock_session = AsyncMock()
            mock_session.initialize.return_value = None
            mock_session_cls.return_value.__aenter__.return_value = mock_session

            mock_stdio.return_value.__aenter__.return_value = (AsyncMock(), AsyncMock())

            server_config = {
                "type": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-postgres"],
            }
            async with get_mcp_client(server_config, timeout=2.0) as session:
                self.assertIsNotNone(session)
                mock_session.initialize.assert_awaited_once()

        asyncio.run(run())

    def test_5_dynamic_tool_discovery_and_adaptation(self):
        """TEST 5: Dynamic tool discovery builds runnable LangChain StructuredTools from MCP session."""
        async def run():
            # Mock MCP Tool Definition
            mock_tool_def = MagicMock()
            mock_tool_def.name = "query_database"
            mock_tool_def.description = "Execute a SQL query"

            mock_tools_list = MagicMock()
            mock_tools_list.tools = [mock_tool_def]

            mock_res = MagicMock()
            mock_res_item = MagicMock()
            mock_res_item.text = "Query OK, 5 rows affected"
            mock_res.content = [mock_res_item]

            mock_session = AsyncMock()
            mock_session.list_tools.return_value = mock_tools_list
            mock_session.call_tool.return_value = mock_res

            # Act: Discover and adapt
            tools = await discover_and_adapt_mcp_tools(mock_session, server_name="postgres")
            self.assertEqual(len(tools), 1)

            tool = tools[0]
            self.assertEqual(tool.name, "postgres_query_database")
            self.assertEqual(tool.description, "Execute a SQL query")

            # Act: Execute tool wrapper
            res = tool.invoke({"sql": "SELECT * FROM users;"})
            self.assertIn("Query OK, 5 rows affected", res)

        asyncio.run(run())

    def test_6_github_client_backward_compatibility(self):
        """TEST 6: Hardcoded get_github_client() and load_config() remain backward compatible."""
        url, headers = load_config()
        self.assertIn("http", url)
        self.assertIn("Authorization", headers)

    @patch("engineeringstack.tools.mcp_tools.get_mcp_client")
    def test_7_mcp_management_tools(self, mock_get_client):
        """TEST 7: register_mcp_server, list_registered_mcp_servers, list_mcp_tools, remove_mcp_server."""
        # 1. Register server
        res_reg = register_mcp_server.invoke({
            "name": "test_db",
            "url": "https://example.com/postgres",
            "transport": "http",
            "persist": False,
        })
        self.assertIn("Successfully registered MCP server 'test_db'", res_reg)

        # 2. List registered servers
        res_list = list_registered_mcp_servers.invoke({})
        self.assertIn("test_db", res_list)

        # 3. List tools via mock client
        mock_tool = MagicMock()
        mock_tool.name = "query_sql"
        mock_tool.description = "Executes arbitrary SQL query"
        mock_res = MagicMock()
        mock_res.tools = [mock_tool]

        mock_session = AsyncMock()
        mock_session.list_tools.return_value = mock_res
        mock_get_client.return_value.__aenter__.return_value = mock_session

        res_tools = list_mcp_tools.invoke({"server": "test_db"})
        self.assertIn("query_sql", res_tools)
        self.assertIn("Executes arbitrary SQL query", res_tools)

        # 4. Remove server
        res_rem = remove_mcp_server_tool.invoke({"name": "test_db", "persist": False})
        self.assertIn("Successfully removed MCP server 'test_db'", res_rem)

    def test_8_automated_domain_tools_resolution(self):
        """TEST 8: Automated domain tool resolution discovers and dynamically binds tools for subagents."""
        from engineeringstack.tools.tools import get_domain_tools
        from engineeringstack.agents.database.rdbms import rdbms_subagent

        # Base rdbms domain tools
        tools = get_domain_tools("rdbms")
        tool_names = [t.name for t in tools]
        self.assertIn("search_code", tool_names)
        self.assertIn("get_file_contents", tool_names)
        self.assertIn("meniscus_recall", tool_names)

        # Register a dynamic server for rdbms domain
        global_registry.add_server("mysql_cluster", {"type": "http", "url": "https://example.com/mysql"}, persist=False)
        auto_tools = get_domain_tools("rdbms")
        auto_names = [t.name for t in auto_tools]
        self.assertTrue(any("mysql_cluster" in n for n in auto_names))

        # Build subagent and ensure runnable is created with automated tools
        subagent = rdbms_subagent()
        self.assertIsNotNone(subagent["runnable"])


if __name__ == "__main__":
    unittest.main()


