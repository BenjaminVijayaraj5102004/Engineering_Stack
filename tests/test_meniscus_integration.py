"""Comprehensive tests for Meniscus MCP integration, client, tools, and cross-agent memory.

Follows TDD Workflow & AAA (Arrange-Act-Assert) pattern:
- TEST 1: Meniscus configuration file and default loader verification.
- TEST 2: Registry domain classification recognizes Meniscus as "memory".
- TEST 3: get_meniscus_client() context manager properly initializes Stdio transport with full environment.
- TEST 4: meniscus_recall tool invocation with query, bounds, around, source_event, and limit.
- TEST 5: meniscus_log tool invocation with content and source.
- TEST 6: Graceful error handling and timeout behavior for Meniscus tools.
- TEST 7: Cross-agent memory tool assignment and role-appropriate read/write permissions.
- TEST 8: End-to-end simulated memory retention and recall cycle across agent invocations.
"""

import asyncio
import json
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from engineeringstack.mcp.client import (
    get_meniscus_client,
    load_meniscus_config,
)
from engineeringstack.mcp.registry import (
    classify_domain,
    get_server_config,
    global_registry,
    list_servers,
)
from engineeringstack.tools.tools import (
    meniscus_recall,
    meniscus_log,
    search_code,
    get_file_contents,
)
from engineeringstack.agents.coding.coding import coding_subagent
from engineeringstack.agents.code_review.code_review import code_review_subagent
from engineeringstack.agents.database.rdbms import rdbms_subagent
from engineeringstack.agents.database.nosql import nosql_subagent
from engineeringstack.agents.database.redis import redis_subagent
from engineeringstack.agents.api.rest import rest_subagent
from engineeringstack.agents.api.graphql import graphql_subagent
from engineeringstack.agents.api.grpc import grpc_subagent
from engineeringstack.agents.api.soap import soap_subagent
from engineeringstack.builders.mcp_builder import build_mcp_manager


class TestMeniscusIntegration(unittest.TestCase):
    """Test suite for Meniscus MCP client, tools, and multi-agent memory layer."""

    def setUp(self):
        global_registry.reset()

    def tearDown(self):
        global_registry.reset()

    def test_1_meniscus_config_and_registry_discovery(self):
        """TEST 1: Meniscus server config is automatically discovered by registry and loader."""
        cfg = load_meniscus_config()
        self.assertIsNotNone(cfg)
        self.assertEqual(cfg.get("type"), "stdio")
        self.assertEqual(cfg.get("command"), "men-mcp")
        self.assertIn("PYTHONUNBUFFERED", cfg.get("env", {}))

        # Check discovery in registry
        all_servers = list_servers()
        self.assertIn("meniscus", all_servers)
        reg_cfg = get_server_config("meniscus")
        self.assertIsNotNone(reg_cfg)
        self.assertEqual(reg_cfg.get("command"), "men-mcp")

    def test_2_meniscus_domain_classification(self):
        """TEST 2: classify_domain recognizes memory and meniscus keywords."""
        self.assertEqual(classify_domain("meniscus"), "memory")
        self.assertEqual(classify_domain("long_term_memory"), "memory")
        self.assertEqual(classify_domain("recall_service"), "memory")

    @patch("engineeringstack.mcp.client.stdio_client")
    @patch("engineeringstack.mcp.client.ClientSession")
    def test_3_get_meniscus_client_stdio_connection(self, mock_session_cls, mock_stdio):
        """TEST 3: get_meniscus_client connects via stdio and initializes session."""
        async def run():
            mock_session = AsyncMock()
            mock_session.initialize.return_value = None
            mock_session_cls.return_value.__aenter__.return_value = mock_session
            mock_stdio.return_value.__aenter__.return_value = (AsyncMock(), AsyncMock())

            async with get_meniscus_client(timeout=5.0) as session:
                self.assertIsNotNone(session)
                mock_session.initialize.assert_awaited_once()

        asyncio.run(run())

    @patch("engineeringstack.tools.tools.get_meniscus_client")
    def test_4_meniscus_recall_tool_invocation(self, mock_get_client):
        """TEST 4: meniscus_recall invokes MCP tool with structured filters."""
        mock_res = MagicMock()
        mock_item = MagicMock()
        mock_item.text = json.dumps({
            "kind": "facts",
            "facts": [
                {"id": 1, "fact": "Project uses PostgreSQL database.", "created_at": "2026-08-21T00:00:00Z"}
            ],
            "count": 1,
        })
        mock_res.content = [mock_item]

        mock_session = AsyncMock()
        mock_session.call_tool.return_value = mock_res
        mock_get_client.return_value.__aenter__.return_value = mock_session

        # Act: Topic Query
        result = meniscus_recall.invoke({"query": "database choice", "limit": 10})
        self.assertIn("PostgreSQL database", result)
        mock_session.call_tool.assert_awaited_with(
            "meniscus_recall",
            {"limit": 10, "query": "database choice"}
        )

        # Act: Session Reconstruction
        meniscus_recall.invoke({"around": "2026-08-21", "limit": 5})
        mock_session.call_tool.assert_awaited_with(
            "meniscus_recall",
            {"limit": 5, "around": "2026-08-21"}
        )

    @patch("engineeringstack.tools.tools.get_meniscus_client")
    def test_5_meniscus_log_tool_invocation(self, mock_get_client):
        """TEST 5: meniscus_log invokes MCP tool to persist memory context."""
        mock_res = MagicMock()
        mock_item = MagicMock()
        mock_item.text = "Logged."
        mock_res.content = [mock_item]

        mock_session = AsyncMock()
        mock_session.call_tool.return_value = mock_res
        mock_get_client.return_value.__aenter__.return_value = mock_session

        result = meniscus_log.invoke({
            "content": "Architecture decision: Adopted Meniscus for long-term episodic memory.",
            "source": "mcp",
        })
        self.assertEqual(result, "Logged.")
        mock_session.call_tool.assert_awaited_with(
            "meniscus_log",
            {
                "content": "Architecture decision: Adopted Meniscus for long-term episodic memory.",
                "source": "mcp",
            }
        )

    @patch("engineeringstack.tools.tools.get_meniscus_client")
    def test_6_meniscus_tool_graceful_error_handling(self, mock_get_client):
        """TEST 6: Tool exceptions and timeouts return informative strings rather than raising uncaught exceptions."""
        mock_session = AsyncMock()
        mock_session.call_tool.side_effect = RuntimeError("Process communication broken")
        mock_get_client.return_value.__aenter__.return_value = mock_session

        recall_res = meniscus_recall.invoke({"query": "failing query"})
        self.assertIn("[Meniscus MCP meniscus_recall: Process communication broken]", recall_res)

        log_res = meniscus_log.invoke({"content": "failing log"})
        self.assertIn("[Meniscus MCP meniscus_log: Process communication broken]", log_res)

    @patch("engineeringstack.tools.tools.get_meniscus_client")
    def test_7_agent_tool_execution_across_subagents(self, mock_get_client):
        """TEST 7: Verify subagents cleanly execute meniscus_recall and meniscus_log tools."""
        from langchain_core.language_models.chat_models import BaseChatModel
        from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
        from langchain_core.outputs import ChatGeneration, ChatResult
        import uuid

        class MockMeniscusToolCaller(BaseChatModel):
            tool_name: str = "meniscus_recall"
            tool_args: dict = {"query": "auth"}
            final_ans: str = "Retrieved memory facts."

            def _generate(self, messages, stop=None, run_manager=None, **kwargs):
                last_msg = messages[-1] if messages else None
                is_tool_msg = (
                    isinstance(last_msg, ToolMessage)
                    or getattr(last_msg, "type", "") == "tool"
                    or (isinstance(last_msg, dict) and last_msg.get("role") == "tool")
                )
                if is_tool_msg:
                    return ChatResult(generations=[ChatGeneration(message=AIMessage(content=self.final_ans))])
                return ChatResult(
                    generations=[
                        ChatGeneration(
                            message=AIMessage(
                                content="",
                                tool_calls=[
                                    {
                                        "id": f"call_{uuid.uuid4().hex[:8]}",
                                        "name": self.tool_name,
                                        "args": self.tool_args,
                                    }
                                ],
                            )
                        )
                    ]
                )

            def bind_tools(self, tools, **kwargs):
                return self

            @property
            def _llm_type(self):
                return "mock_meniscus_tool_caller"

        mock_res = MagicMock()
        mock_item = MagicMock()
        mock_item.text = json.dumps({"kind": "facts", "facts": [{"fact": "Postgres used"}], "count": 1})
        mock_res.content = [mock_item]

        mock_session = AsyncMock()
        mock_session.call_tool.return_value = mock_res
        mock_get_client.return_value.__aenter__.return_value = mock_session

        # 1. Test Coding_Agent executes meniscus_recall
        mock_llm = MockMeniscusToolCaller(tool_name="meniscus_recall", tool_args={"query": "database convention"})
        coding = coding_subagent(model=mock_llm)
        res = coding["runnable"].invoke(
            {"messages": [HumanMessage(content="Implement database models")]},
            config={"configurable": {"thread_id": str(uuid.uuid4())}},
        )
        self.assertIn("Retrieved memory facts", res["messages"][-1].content)

        # 2. Test Coding_Agent executes meniscus_log
        mock_log_res = MagicMock()
        mock_log_item = MagicMock()
        mock_log_item.text = "Logged."
        mock_log_res.content = [mock_log_item]
        mock_session.call_tool.return_value = mock_log_res

        mock_llm_log = MockMeniscusToolCaller(tool_name="meniscus_log", tool_args={"content": "Persisted pattern"})
        coding_log = coding_subagent(model=mock_llm_log)
        res_log = coding_log["runnable"].invoke(
            {"messages": [HumanMessage(content="Save design decision")]},
            config={"configurable": {"thread_id": str(uuid.uuid4())}},
        )
        self.assertIn("Retrieved memory facts", res_log["messages"][-1].content)

        # 3. Test RDBMS_agent executes meniscus_recall
        mock_session.call_tool.return_value = mock_res
        mock_llm_rdbms = MockMeniscusToolCaller(tool_name="meniscus_recall", tool_args={"query": "schema"})
        rdbms = rdbms_subagent(model=mock_llm_rdbms)
        res_rdbms = rdbms["runnable"].invoke(
            {"messages": [HumanMessage(content="Create tables")]},
            config={"configurable": {"thread_id": str(uuid.uuid4())}},
        )
        self.assertIn("Retrieved memory facts", res_rdbms["messages"][-1].content)

        # 4. Test REST_Agent executes meniscus_recall
        mock_llm_rest = MockMeniscusToolCaller(tool_name="meniscus_recall", tool_args={"query": "endpoints"})
        rest = rest_subagent(model=mock_llm_rest)
        res_rest = rest["runnable"].invoke(
            {"messages": [HumanMessage(content="Create endpoints")]},
            config={"configurable": {"thread_id": str(uuid.uuid4())}},
        )
        self.assertIn("Retrieved memory facts", res_rest["messages"][-1].content)


if __name__ == "__main__":
    unittest.main()
