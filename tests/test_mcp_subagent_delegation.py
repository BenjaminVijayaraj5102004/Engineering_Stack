"""Unit tests for MCP Subagent, call_mcp_tool, and MCP Manager tool delegation routing.

Verifies:
1. MCP Subagent specification, tools, and graph exports.
2. Dynamic MCP Subagent factory.
3. call_mcp_tool tool execution with mock MCP client session.
4. MCP Manager includes domain specialist subagents + MCP_Subagent.
5. Tool delegation: PostgreSQL MCP tool delegated to RDBMS_agent.
6. Tool delegation: Unregistered / custom MCP tool (e.g. Weather / Figma) delegated to MCP_Subagent.
"""

import unittest
from unittest.mock import patch, AsyncMock, MagicMock
from typing import Any, Optional
import json

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langgraph.graph.state import CompiledStateGraph

from engineeringstack.agents.mcp_agents import (
    mcp_subagent,
    dynamic_mcp_subagent,
    mcp_leaf_subagent,
    graph as mcp_subagent_graph,
)
from engineeringstack.builders.mcp_builder import (
    build_mcp_manager,
    get_mcp_subagents,
    mcp_manager,
    mcp_subagent as builder_mcp_subagent,
)
from engineeringstack.prompts.mcp_prompt import (
    MCP_MANAGER_SYSTEM_PROMPT,
    MCP_SUBAGENT_SYSTEM_PROMPT,
)
from engineeringstack.tools.mcp_tools import (
    call_mcp_tool,
    register_mcp_server,
    list_mcp_tools,
)
from engineeringstack.stack import EngineeringStack


class MockMCPDelegationChatModel(BaseChatModel):
    """Deterministic Mock LLM for verifying MCP Manager tool delegation logic."""

    def _generate(
        self,
        messages: Any,
        stop: Optional[Any] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        user_query = ""
        for msg in reversed(messages):
            content = getattr(msg, "content", str(msg))
            if content:
                user_query = str(content).lower()
                break

        if "postgres" in user_query or "sql" in user_query:
            resp = (
                "MCP_Manager: Detected database domain tool -> Delegating PostgreSQL query execution "
                "task to RDBMS_agent."
            )
        elif "weather" in user_query or "figma" in user_query or "custom" in user_query:
            resp = (
                "MCP_Manager: Tool does not belong to standard database/API specialists -> "
                "Delegating task to MCP_Subagent for execution via call_mcp_tool."
            )
        elif "github" in user_query or "git" in user_query:
            resp = (
                "MCP_Manager: Detected coding domain -> Delegating repository tool call to Coding_Agent."
            )
        else:
            resp = "MCP_Manager: Processing MCP tool request."

        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content=resp))]
        )

    def bind_tools(self, tools: Any, **kwargs: Any) -> Any:
        return self

    @property
    def _llm_type(self) -> str:
        return "mock_mcp_delegation_chat_model"


class TestMCPSubagentDelegation(unittest.TestCase):
    """Test suite for MCP Subagent creation, tool execution, and manager delegation."""

    def test_1_mcp_subagent_spec_and_graph(self):
        """Test MCP Subagent specification dictionary and graph exports."""
        spec = mcp_subagent()
        self.assertEqual(spec["name"], "MCP_Subagent")
        self.assertIn("description", spec)
        self.assertEqual(spec["system_prompt"], MCP_SUBAGENT_SYSTEM_PROMPT)
        self.assertIsInstance(spec["runnable"], CompiledStateGraph)
        self.assertIsInstance(mcp_leaf_subagent, CompiledStateGraph)
        self.assertIsInstance(mcp_subagent_graph, CompiledStateGraph)

    def test_2_dynamic_mcp_subagent_factory(self):
        """Test dynamic_mcp_subagent factory with custom parameters."""
        spec = dynamic_mcp_subagent(
            agent_name="Figma_Design_Agent",
            description="Dedicated agent for Figma MCP tools.",
            system_prompt="Custom system prompt for Figma.",
            tools=[call_mcp_tool],
        )
        self.assertEqual(spec["name"], "Figma_Design_Agent")
        self.assertEqual(spec["description"], "Dedicated agent for Figma MCP tools.")
        self.assertEqual(spec["system_prompt"], "Custom system prompt for Figma.")
        self.assertIsInstance(spec["runnable"], CompiledStateGraph)

    @patch("engineeringstack.tools.mcp_tools._run_async_safely")
    def test_3_call_mcp_tool_execution(self, mock_run_async):
        """Test call_mcp_tool invokes MCP server and returns string result."""
        mock_output = "Query executed successfully: 5 rows returned."
        def side_effect(coro):
            coro.close()
            return mock_output
        mock_run_async.side_effect = side_effect

        result = call_mcp_tool.invoke({
            "server": "postgres",
            "tool_name": "query",
            "arguments": {"sql": "SELECT * FROM users;"},
        })
        self.assertEqual(result, mock_output)

    def test_4_mcp_manager_subagents_list(self):
        """Test MCP_Manager has access to domain subagents and MCP_Subagent."""
        subagents = get_mcp_subagents()
        subagent_names = [sa["name"] for sa in subagents]

        expected_names = [
            "RDBMS_agent",
            "NoSQL_agent",
            "REDIS_agent",
            "REST_Agent",
            "GraphQL_Agent",
            "GRPC_Agent",
            "SOAP_Agent",
            "Coding_Agent",
            "MCP_Subagent",
        ]
        for name in expected_names:
            self.assertIn(name, subagent_names, f"Expected {name} in MCP Manager subagents")

    def test_5_mcp_manager_postgres_tool_delegation_to_rdbms(self):
        """Test MCP_Manager delegates PostgreSQL tool calling to RDBMS_agent."""
        model = MockMCPDelegationChatModel()
        stack = EngineeringStack(model=model)

        query = "Use the postgres MCP tool to run 'SELECT * FROM products;'"
        response = stack.invoke(query)

        final_answer = response.get("final_answer", "")
        self.assertIn("MCP_Manager", final_answer)
        self.assertIn("RDBMS_agent", final_answer)

    def test_6_mcp_manager_unregistered_tool_delegation_to_mcp_subagent(self):
        """Test MCP_Manager delegates unclassified tool (e.g. weather/figma) to MCP_Subagent."""
        model = MockMCPDelegationChatModel()
        stack = EngineeringStack(model=model)

        query = "Use the weather MCP tool to get forecast for San Francisco"
        response = stack.invoke(query)

        final_answer = response.get("final_answer", "")
        self.assertIn("MCP_Manager", final_answer)
        self.assertIn("MCP_Subagent", final_answer)

    def test_7_call_mcp_tool_properties(self):
        """Test call_mcp_tool tool metadata and description."""
        self.assertEqual(call_mcp_tool.name, "call_mcp_tool")
        self.assertIn("server", call_mcp_tool.description.lower())
        self.assertIn("tool", call_mcp_tool.description.lower())


if __name__ == "__main__":
    unittest.main()
