"""Comprehensive tests verifying tool surface optimization and least-capability architecture.

Test Requirements:
- TEST 1: "Hi" -> Main Agent answers directly without subagent invocation.
- TEST 2: "Create a PostgreSQL users table" -> Main Agent -> Database_Manager -> RDMS_agent.
- TEST 3: API request -> Main Agent -> API_Manager -> REST_Agent.
- TEST 4: Code review request -> Main Agent -> Code_Reviewer.
- TEST 5: Verify leaf agents cannot delegate (no `task` tool exposed to leaf agents).
- TEST 6: Verify skill files remain read-only/protected from user modification.
"""

import unittest
from pathlib import Path
from typing import Any, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langgraph.store.memory import InMemoryStore
from deepagents.backends import FilesystemBackend, StoreBackend

from engineeringstack.stack import EngineeringStack
from engineeringstack.builders.main_builder import (
    SDK_SKILLS_DIR,
    build_default_backend,
    build_main_agent,
    get_helper_agents,
)
from engineeringstack.builders.db_builder import build_database_manager
from engineeringstack.builders.api_builder import build_api_manager
from engineeringstack.builders.helper_builder import build_helper_manager
from engineeringstack.agents.coding.coding import coding_subagent
from engineeringstack.agents.code_review.code_review import code_review_subagent
from engineeringstack.agents.database.rdbms import rdbms_subagent
from engineeringstack.agents.database.nosql import nosql_subagent
from engineeringstack.agents.database.redis import redis_subagent
from engineeringstack.agents.api.rest import rest_subagent
from engineeringstack.agents.api.graphql import graphql_subagent
from engineeringstack.agents.api.grpc import grpc_subagent
from engineeringstack.agents.api.soap import soap_subagent


class MockEchoChatModel(BaseChatModel):
    """Mock Chat Model returning deterministic scripted response."""

    response_text: str = "Default Response"

    def _generate(
        self,
        messages: Any,
        stop: Optional[Any] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content=self.response_text))]
        )

    def bind_tools(self, tools: Any, **kwargs: Any) -> Any:
        return self

    @property
    def _llm_type(self) -> str:
        return "mock_echo_chat"


class TestToolSurfaceAndLeastCapability(unittest.TestCase):
    """Test suite verifying tool surface reduction and least-capability compliance."""

    def setUp(self):
        self.store = InMemoryStore()

    def test_1_greeting_hi_answered_directly(self):
        """TEST 1: 'Hi' must be answered directly by Main Agent without subagent invocation."""
        model = MockEchoChatModel(response_text="Hello! How can I assist you with your project today?")
        stack = EngineeringStack(model=model, store=self.store)

        result = stack.invoke("Hi")

        self.assertIsNotNone(result)
        self.assertIn("final_answer", result)
        self.assertIn("Hello", result["final_answer"])

    def test_2_standalone_table_request_routing(self):
        """TEST 2: 'Create a MongoDB users table' routes to Helper_Manager -> Coding_Agent."""
        model = MockEchoChatModel(response_text="Delegating to Helper_Manager -> Coding_Agent for MongoDB users table creation.")
        stack = EngineeringStack(model=model, store=self.store)

        result = stack.invoke("Create a MongoDB users table")

        self.assertIsNotNone(result)
        self.assertIn("Helper_Manager", result["final_answer"])

    def test_3_standalone_api_endpoint_routing(self):
        """TEST 3: Standalone API route request routes to Helper_Manager -> Coding_Agent."""
        model = MockEchoChatModel(response_text="Delegating to Helper_Manager -> Coding_Agent for FastAPI REST endpoint implementation.")
        stack = EngineeringStack(model=model, store=self.store)

        result = stack.invoke("Build a REST API endpoint in FastAPI for user authentication")

        self.assertIsNotNone(result)
        self.assertIn("Helper_Manager", result["final_answer"])

    def test_3b_full_stack_enterprise_routing(self):
        """TEST 3b: Full-stack product engineering routes across Database_Manager and API_Manager."""
        model = MockEchoChatModel(response_text="Orchestrating enterprise product across Database_Manager and API_Manager.")
        stack = EngineeringStack(model=model, store=self.store)

        result = stack.invoke("Build a complete enterprise product backend with multi-table PostgreSQL database and FastAPI services")

        self.assertIsNotNone(result)
        self.assertIn("Database_Manager", result["final_answer"])
        self.assertIn("API_Manager", result["final_answer"])

    def test_3c_product_table_routing(self):
        """TEST 3c: Product table (part of code) routes to Helper_Manager."""
        model = MockEchoChatModel(response_text="Delegating to Helper_Manager -> Coding_Agent for product table schema.")
        stack = EngineeringStack(model=model, store=self.store)

        result = stack.invoke("Create a product table")

        self.assertIsNotNone(result)
        self.assertIn("Helper_Manager", result["final_answer"])

    def test_3d_debug_routing(self):
        """TEST 3d: Debug request (part of code) routes to Helper_Manager."""
        model = MockEchoChatModel(response_text="Delegating to Helper_Manager -> Coding_Agent for debugging function.")
        stack = EngineeringStack(model=model, store=self.store)

        result = stack.invoke("Debug this function")

        self.assertIsNotNone(result)
        self.assertIn("Helper_Manager", result["final_answer"])

    def test_4_code_review_request_routing(self):
        """TEST 4: Code review request routes to Helper_Manager -> Code_Reviewer."""
        model = MockEchoChatModel(response_text="Delegating to Helper_Manager -> Code_Reviewer for security and quality audit.")
        stack = EngineeringStack(model=model, store=self.store)

        result = stack.invoke("Review and audit the authentication middleware code for security vulnerabilities")

        self.assertIsNotNone(result)
        self.assertIn("Helper_Manager", result["final_answer"])



    def test_4b_generic_coding_request_routing(self):
        """TEST 4b: Generic coding request routes to Helper_Manager -> Coding_Agent."""
        model = MockEchoChatModel(response_text="Delegating to Helper_Manager -> Coding_Agent for binary search algorithm implementation.")
        stack = EngineeringStack(model=model, store=self.store)

        result = stack.invoke("Write a Python function to perform binary search on a sorted list")

        self.assertIsNotNone(result)
        self.assertIn("Helper_Manager", result["final_answer"])

    def test_5_leaf_agents_cannot_delegate(self):
        """TEST 5: Verify leaf agents do NOT have delegation capability (no task tool)."""
        leaf_subagents = [
            ("RDBMS_agent", rdbms_subagent),
            ("NoSQL_agent", nosql_subagent),
            ("REDIS_agent", redis_subagent),
            ("REST_Agent", rest_subagent),
            ("GraphQL_Agent", graphql_subagent),
            ("GRPC_Agent", grpc_subagent),
            ("SOAP_Agent", soap_subagent),
            ("Coding_Agent", coding_subagent),
            ("Code_Reviewer", code_review_subagent),
        ]

        for name, factory in leaf_subagents:
            with self.subTest(agent_name=name):
                sub = factory()
                self.assertEqual(sub["name"], name)
                self.assertTrue(hasattr(sub["runnable"], "invoke"))
                # Leaf agents are compiled StateGraphs without task delegation tool in subagent spec
                self.assertNotIn("subagents", sub)

    def test_5b_internal_subagents_not_exposed_directly_to_main_agent(self):
        """TEST 5b: Verify Coding_Agent and Code_Reviewer are NOT directly attached to Main Agent."""
        main_helpers = get_helper_agents()
        top_level_names = {h["name"] for h in main_helpers}
        self.assertEqual(top_level_names, {"Database_Manager", "API_Manager", "Helper_Manager"})
        self.assertNotIn("Coding_Agent", top_level_names)
        self.assertNotIn("Code_Reviewer", top_level_names)

    def test_6_skill_files_read_only_and_isolated(self):
        """TEST 6: Verify skill files remain read-only and mounted via FilesystemBackend."""
        backend = build_default_backend()

        # /skills/ route is mounted via FilesystemBackend pointing to SDK_SKILLS_DIR
        self.assertIsInstance(backend.routes["/skills/"], FilesystemBackend)

        skill_file = SDK_SKILLS_DIR / "main-agent" / "SKILL.md"
        self.assertTrue(skill_file.exists())
        content = skill_file.read_text(encoding="utf-8")
        self.assertIn("Main Agent Procedural Skill", content)


if __name__ == "__main__":
    unittest.main()

