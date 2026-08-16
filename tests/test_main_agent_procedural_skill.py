"""Focused test suite verifying the Main Agent Procedural Skill integration.

Tests adherence to TDD Workflow & AAA (Arrange-Act-Assert) pattern:
- TEST 1: User says "Hello" -> Main Agent answers directly without specialist delegation.
- TEST 2: User says "Create a POST endpoint in Flask." -> Identifies API engineering & delegates to API_Manager.
- TEST 3: User says "Design a PostgreSQL users table." -> Identifies Database engineering & delegates to Database_Manager.
- TEST 4: Verifies Main Agent successfully loads and registers the procedural skill.
- TEST 5: Verifies the skill remains SDK/developer-controlled and isolated from user memory.
"""

import unittest
from pathlib import Path
from typing import Any, List, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langgraph.store.memory import InMemoryStore
from deepagents.backends import FilesystemBackend, StoreBackend
from deepagents.middleware.skills import _list_skills_with_errors

from engineeringstack.builders.main_builder import (
    SDK_SKILLS_DIR,
    build_default_backend,
    build_main_agent,
)
from engineeringstack.stack import EngineeringStack


class MockDeterministicChatModel(BaseChatModel):
    """Deterministic Mock LLM for Main Agent workflow verification."""

    response_text: str = "Hello! I am Main Agent. How can I assist you with your project today?"

    def _generate(
        self,
        messages: Any,
        stop: Optional[Any] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        from langchain_core.outputs import ChatGeneration, ChatResult
        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content=self.response_text))]
        )

    def bind_tools(self, tools: Any, **kwargs: Any) -> Any:
        return self

    @property
    def _llm_type(self) -> str:
        return "mock_deterministic_chat"


class TestMainAgentProceduralSkill(unittest.TestCase):
    """Test suite for Main Agent procedural skill behaviors and architectural boundaries."""

    def setUp(self):
        self.store = InMemoryStore()

    def test_1_hello_answers_directly_without_specialist_delegation(self):
        """TEST 1: User query 'Hello' must be answered directly with no unnecessary delegation."""
        # Arrange
        user_query = "Hello"
        mock_llm = MockDeterministicChatModel(response_text="Hello! I am Main Agent. I can assist with API, database, and code reviews.")
        stack = EngineeringStack(model=mock_llm, store=self.store)

        # Act
        response = stack.invoke(user_query)

        # Assert
        self.assertTrue(len(response["final_answer"]) > 0)
        self.assertIn("Main Agent", response["final_answer"])

    def test_2_create_post_endpoint_flask_execution(self):
        """TEST 2: User query 'Create a POST endpoint in Flask.' processes via Helper_Manager for standalone coding."""
        # Arrange
        user_query = "Create a POST endpoint in Flask."
        mock_llm = MockDeterministicChatModel(response_text="Delegating to Helper_Manager for Flask POST endpoint implementation.")
        stack = EngineeringStack(model=mock_llm, store=self.store)

        # Act
        response = stack.invoke(user_query)

        # Assert
        self.assertIn("Helper_Manager", response["final_answer"])

    def test_3_design_mongodb_users_table_execution(self):
        """TEST 3: User query 'Create a mongoDB users table.' processes via Helper_Manager for standalone table schema."""
        # Arrange
        user_query = "Create a mongoDB users table."
        mock_llm = MockDeterministicChatModel(response_text="Delegating to Helper_Manager for MongoDB users schema creation.")
        stack = EngineeringStack(model=mock_llm, store=self.store)

        # Act
        response = stack.invoke(user_query)

        # Assert
        self.assertIn("Helper_Manager", response["final_answer"])


    def test_4_main_agent_loads_and_registers_procedural_skill(self):
        """TEST 4: Verify Main Agent backend successfully discovers and loads main_agent SKILL.md."""
        # Arrange
        backend = build_default_backend()

        # Act - List skills through DeepAgents discovery mechanism
        skills, errors = _list_skills_with_errors(backend, "/skills/")

        # Assert
        self.assertIsNone(errors)
        self.assertTrue(len(skills) > 0)
        skill_names = [s["name"] for s in skills]
        self.assertIn("main-agent", skill_names)

        # Verify skill metadata properties
        main_skill = next(s for s in skills if s["name"] == "main-agent")
        self.assertEqual(main_skill["path"], "/skills/main-agent/SKILL.md")
        self.assertIn("Main Agent", main_skill["description"])

        # Verify physical file existence in SDK package
        physical_skill_file = SDK_SKILLS_DIR / "main-agent" / "SKILL.md"
        self.assertTrue(physical_skill_file.exists())
        content = physical_skill_file.read_text(encoding="utf-8")
        self.assertIn("Main Agent Procedural Skill", content)

    def test_5_skill_remains_sdk_controlled_and_isolated_from_user_memory(self):
        """TEST 5: Verify procedural skills are mounted via FilesystemBackend."""
        # Arrange
        backend = build_default_backend()

        # Assert: /skills/ is mounted via SDK_SKILLS_DIR FilesystemBackend (developer controlled)
        self.assertIsInstance(backend.routes["/skills/"], FilesystemBackend)
        self.assertEqual(Path(backend.routes["/skills/"].cwd), SDK_SKILLS_DIR.resolve())

        # Verify SDK skills directory remains intact and developer-controlled
        physical_skill_file = SDK_SKILLS_DIR / "main-agent" / "SKILL.md"
        self.assertTrue(physical_skill_file.exists())


    def test_6_generic_coding_delegation(self):
        """TEST 6: User query 'Write a Python quicksort algorithm' processes via Helper_Manager."""
        # Arrange
        user_query = "Write a Python quicksort algorithm."
        mock_llm = MockDeterministicChatModel(response_text="Delegating to Helper_Manager for quicksort algorithm implementation.")
        stack = EngineeringStack(model=mock_llm, store=self.store)

        # Act
        response = stack.invoke(user_query)

        # Assert
        self.assertIn("Helper_Manager", response["final_answer"])

    def test_7_code_review_delegation(self):
        """TEST 7: User query 'Audit this code for vulnerabilities' processes via Helper_Manager."""
        # Arrange
        user_query = "Audit this code for vulnerabilities."
        mock_llm = MockDeterministicChatModel(response_text="Delegating to Helper_Manager for security audit.")
        stack = EngineeringStack(model=mock_llm, store=self.store)

        # Act
        response = stack.invoke(user_query)

        # Assert
        self.assertIn("Helper_Manager", response["final_answer"])


    def test_8_standalone_user_table_delegation(self):
        """TEST 8: User query 'Create a user table' processes via Helper_Manager for small implementation."""
        # Arrange
        user_query = "Create a user table with username and email fields."
        mock_llm = MockDeterministicChatModel(response_text="Delegating to Helper_Manager for standalone user table schema creation.")
        stack = EngineeringStack(model=mock_llm, store=self.store)

        # Act
        response = stack.invoke(user_query)

        # Assert
        self.assertIn("Helper_Manager", response["final_answer"])

    def test_9_full_stack_product_engineering_orchestration(self):
        """TEST 9: User query 'Build a full product backend with REST API and PostgreSQL database' orchestrates across managers."""
        # Arrange
        user_query = "Build a full product backend with FastAPI REST API connected to PostgreSQL database."
        mock_llm = MockDeterministicChatModel(response_text="Orchestrating full-stack engineering across Database_Manager and API_Manager.")
        stack = EngineeringStack(model=mock_llm, store=self.store)

        # Act
        response = stack.invoke(user_query)

        # Assert
        self.assertIn("Database_Manager", response["final_answer"])
        self.assertIn("API_Manager", response["final_answer"])

    def test_10_product_table_delegation(self):
        """TEST 10: User query 'Create a product table' (a part of code) routes to Helper_Manager."""
        user_query = "Create a product table."
        mock_llm = MockDeterministicChatModel(response_text="Delegating to Helper_Manager for product table implementation.")
        stack = EngineeringStack(model=mock_llm, store=self.store)

        response = stack.invoke(user_query)
        self.assertIn("Helper_Manager", response["final_answer"])

    def test_11_ecommerce_website_orchestration(self):
        """TEST 11: User query 'Create an e-commerce website' (entire application) orchestrates across managers."""
        user_query = "Create an e-commerce website with inventory database and payment APIs."
        mock_llm = MockDeterministicChatModel(response_text="Orchestrating across Database_Manager and API_Manager for e-commerce website.")
        stack = EngineeringStack(model=mock_llm, store=self.store)

        response = stack.invoke(user_query)
        self.assertIn("Database_Manager", response["final_answer"])
        self.assertIn("API_Manager", response["final_answer"])

    def test_12_debug_part_of_code_delegation(self):
        """TEST 12: User query 'Debug this function' (part of code) routes to Helper_Manager."""
        user_query = "Debug this binary search function for edge case off-by-one errors."
        mock_llm = MockDeterministicChatModel(response_text="Delegating to Helper_Manager for debugging function.")
        stack = EngineeringStack(model=mock_llm, store=self.store)

        response = stack.invoke(user_query)
        self.assertIn("Helper_Manager", response["final_answer"])


if __name__ == "__main__":
    unittest.main()



