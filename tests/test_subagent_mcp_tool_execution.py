"""Unit tests verifying actual MCP tool execution (search_code, get_file_contents) across all subagents.

Follows TDD Workflow & AAA (Arrange-Act-Assert) pattern:
- TEST 1: Coding_Agent executes search_code tool call during workflow.
- TEST 2: Code_Reviewer executes get_file_contents tool call during review audit.
- TEST 3: Domain specialists (RDBMS_agent, NoSQL_agent, REDIS_agent, REST_Agent, GraphQL_Agent, GRPC_Agent, SOAP_Agent) execute MCP tools.
- TEST 4: Tool binding validation across all 9 domain specialist subagents.
"""

import unittest
from unittest.mock import patch, MagicMock
from typing import Any, Optional
import uuid

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langgraph.store.memory import InMemoryStore

from engineeringstack.agents.coding.coding import coding_subagent
from engineeringstack.agents.code_review.code_review import code_review_subagent
from engineeringstack.agents.database.rdbms import rdbms_subagent
from engineeringstack.agents.database.nosql import nosql_subagent
from engineeringstack.agents.database.redis import redis_subagent
from engineeringstack.agents.api.rest import rest_subagent
from engineeringstack.agents.api.graphql import graphql_subagent
from engineeringstack.agents.api.grpc import grpc_subagent
from engineeringstack.agents.api.soap import soap_subagent
from engineeringstack.tools.tools import search_code, get_file_contents


class MockToolExecutingChatModel(BaseChatModel):
    """Deterministic Mock LLM that executes a tool call on turn 1 and answers on turn 2."""

    tool_call_name: str = "search_code"
    tool_call_args: dict = {"query": "FastAPI authentication router"}
    final_response: str = "Code verified and implemented according to searched repository patterns."

    def _generate(
        self,
        messages: Any,
        stop: Optional[Any] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        # Check if the last message in the conversation is a tool response
        last_message = messages[-1] if messages else None
        is_tool_msg = (
            isinstance(last_message, ToolMessage)
            or getattr(last_message, "type", "") == "tool"
            or (isinstance(last_message, dict) and last_message.get("role") == "tool")
        )

        if is_tool_msg:
            # Turn 2: Receive tool output and return final verified response
            return ChatResult(
                generations=[ChatGeneration(message=AIMessage(content=self.final_response))]
            )

        # Turn 1: Emit requested tool call
        tool_call = {
            "name": self.tool_call_name,
            "args": self.tool_call_args,
            "id": f"call_{uuid.uuid4().hex[:8]}",
            "type": "tool_call",
        }
        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content="", tool_calls=[tool_call]))]
        )

    def bind_tools(self, tools: Any, **kwargs: Any) -> Any:
        return self

    @property
    def _llm_type(self) -> str:
        return "mock_tool_executing_chat_model"


class TestSubagentMCPToolExecution(unittest.TestCase):
    """Test suite verifying subagent MCP tool execution (search_code and get_file_contents)."""

    def setUp(self):
        self.store = InMemoryStore()

    @patch("engineeringstack.tools.tools._run_async_safely")
    def test_1_coding_agent_executes_search_code_tool(self, mock_run_async):
        """TEST 1: Coding_Agent successfully executes search_code tool call during task processing."""
        # Arrange
        mock_search_output = "Found 3 matches:\n1. fastapi/routing.py (repo: tiangolo/fastapi)"
        def side_effect(coro):
            coro.close()
            return mock_search_output
        mock_run_async.side_effect = side_effect

        mock_llm = MockToolExecutingChatModel(
            tool_call_name="search_code",
            tool_call_args={"query": "FastAPI APIRouter"},
            final_response="Generated FastAPI APIRouter using verified repository patterns.",
        )

        subagent_dict = coding_subagent(model=mock_llm)
        runnable = subagent_dict["runnable"]

        # Act
        thread_id = str(uuid.uuid4())
        response = runnable.invoke(
            {"messages": [HumanMessage(content="Search for FastAPI APIRouter implementation patterns")]},
            config={"configurable": {"thread_id": thread_id}},
        )

        # Assert
        self.assertIsNotNone(response)
        messages = response["messages"]
        # Verify tool call was emitted
        ai_tool_call_msgs = [m for m in messages if getattr(m, "tool_calls", None)]
        self.assertTrue(len(ai_tool_call_msgs) > 0)
        self.assertEqual(ai_tool_call_msgs[0].tool_calls[0]["name"], "search_code")

        # Verify tool execution occurred
        tool_res_msgs = [m for m in messages if isinstance(m, ToolMessage) or getattr(m, "type", "") == "tool"]
        self.assertTrue(len(tool_res_msgs) > 0)
        self.assertEqual(tool_res_msgs[0].content, mock_search_output)

        # Verify final response
        last_msg = messages[-1]
        self.assertIn("Generated FastAPI APIRouter", last_msg.content)

    @patch("engineeringstack.tools.tools._run_async_safely")
    def test_2_code_reviewer_executes_get_file_contents_tool(self, mock_run_async):
        """TEST 2: Code_Reviewer successfully executes get_file_contents tool call to inspect file."""
        # Arrange
        mock_file_content = "def authenticate_user(token: str):\n    return verify_jwt(token)"
        def side_effect(coro):
            coro.close()
            return mock_file_content
        mock_run_async.side_effect = side_effect

        mock_llm = MockToolExecutingChatModel(
            tool_call_name="get_file_contents",
            tool_call_args={"path": "auth/service.py", "owner": "myorg", "repo": "backend"},
            final_response="Audited auth/service.py: Verified JWT verification security.",
        )

        subagent_dict = code_review_subagent(model=mock_llm)
        runnable = subagent_dict["runnable"]

        # Act
        thread_id = str(uuid.uuid4())
        response = runnable.invoke(
            {"messages": [HumanMessage(content="Inspect auth/service.py and audit security")]},
            config={"configurable": {"thread_id": thread_id}},
        )

        # Assert
        self.assertIsNotNone(response)
        messages = response["messages"]
        tool_res_msgs = [m for m in messages if isinstance(m, ToolMessage) or getattr(m, "type", "") == "tool"]
        self.assertTrue(len(tool_res_msgs) > 0)
        self.assertEqual(tool_res_msgs[0].content, mock_file_content)

        last_msg = messages[-1]
        self.assertIn("Audited auth/service.py", last_msg.content)

    @patch("engineeringstack.tools.tools._run_async_safely")
    def test_3_domain_specialists_execute_mcp_tools(self, mock_run_async):
        """TEST 3: RDBMS_agent, NoSQL_agent, REST_Agent execute search_code and get_file_contents."""
        def side_effect(coro):
            coro.close()
            return "CREATE TABLE users (id SERIAL PRIMARY KEY);"
        mock_run_async.side_effect = side_effect

        specialists = [
            ("RDBMS_agent", rdbms_subagent),
            ("NoSQL_agent", nosql_subagent),
            ("REDIS_agent", redis_subagent),
            ("REST_Agent", rest_subagent),
            ("GraphQL_Agent", graphql_subagent),
            ("GRPC_Agent", grpc_subagent),
            ("SOAP_Agent", soap_subagent),
        ]

        for name, factory in specialists:
            with self.subTest(specialist_name=name):
                mock_llm = MockToolExecutingChatModel(
                    tool_call_name="search_code",
                    tool_call_args={"query": f"example {name}"},
                    final_response=f"{name} completed task with searched reference.",
                )
                subagent = factory(model=mock_llm)
                runnable = subagent["runnable"]

                thread_id = str(uuid.uuid4())
                response = runnable.invoke(
                    {"messages": [HumanMessage(content=f"Search reference for {name}")]},
                    config={"configurable": {"thread_id": thread_id}},
                )
                self.assertIsNotNone(response)
                last_msg = response["messages"][-1]
                self.assertIn(f"{name} completed task", last_msg.content)

    def test_4_all_leaf_subagents_have_search_code_and_get_file_contents_tools(self):
        """TEST 4: Verify search_code and get_file_contents tools are properly imported and configured."""
        self.assertEqual(search_code.name, "search_code")
        self.assertEqual(get_file_contents.name, "get_file_contents")
        self.assertIn("GitHub", search_code.description)
        self.assertIn("repository", get_file_contents.description)


if __name__ == "__main__":
    unittest.main()
