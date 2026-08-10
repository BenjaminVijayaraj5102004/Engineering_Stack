"""Integration and unit tests for Main Agent multi-thread memory workflows.

Derived from the configuration and flow in examples/main_agent.py.
Follows TDD Workflow:
- Arrange-Act-Assert (AAA) pattern
- Uses os and python-dotenv to load GROQ_API_KEY from .env
- Tests Thread 1 (Memory Saving / Auto-Save)
- Tests Thread 2 (Cross-Thread Memory Recall with distinct thread_id)
- Tests Store inspection under ("default_user",) namespace
- Tests real Groq model execution when GROQ_API_KEY is available
"""

import os
import unittest
import uuid
from typing import Any, Optional
from dotenv import load_dotenv

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langgraph.store.memory import InMemoryStore

from engineeringstack.schema.state import AIOutput, UserInput
from engineeringstack.stack import EngineeringStack, create_engineering_stack

# Load environment variables from .env
load_dotenv()


class MockChatGroqModel(BaseChatModel):
    """Test double simulating ChatGroq behavior with memory context sensitivity."""

    response_map: dict[str, str] = {
        "name": "Hello Vijayaraj Benjamin! It is a pleasure to meet you. I am the Main Agent.",
        "recall": "Your name is Vijayaraj Benjamin, as recorded in our project preferences.",
        "default": "Hello! I am the Main Agent for the Engineering Stack. How can I assist you?",
    }

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

        if "vijayaraj" in user_query or "my name is" in user_query:
            resp = self.response_map["name"]
        elif "what is my name" in user_query or "who am i" in user_query:
            resp = self.response_map["recall"]
        else:
            resp = self.response_map["default"]

        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content=resp))]
        )

    def bind_tools(self, tools: Any, **kwargs: Any) -> Any:
        return self

    @property
    def _llm_type(self) -> str:
        return "mock_chat_groq"


class TestMainAgentWorkflowFromExample(unittest.TestCase):
    """Deterministic test suite reproducing the 3-step workflow in examples/main_agent.py."""

    def setUp(self):
        """Arrange: Initialize in-memory store and mock model mimicking example config."""
        self.store = InMemoryStore()
        self.model = MockChatGroqModel()
        self.stack = EngineeringStack(
            model=self.model,
            store=self.store,
        )

    def test_example_configuration_initialization(self):
        """Arrange-Act-Assert: Verify EngineeringStack correctly initializes with Store and Model."""
        # Assert
        self.assertIsNotNone(self.stack.model)
        self.assertIs(self.stack.store, self.store)
        self.assertIn("/memories/preferences.md", self.stack.memory)
        self.assertIn("/memories/AGENTS.md", self.stack.memory)

    def test_thread1_saves_user_introduction_and_answers_directly(self):
        """Arrange-Act-Assert: Thread 1 introduces user naturally and returns direct greeting."""
        # Arrange
        thread_1 = str(uuid.uuid4())
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": "Hi, my name is Vijayaraj Benjamin.",
                }
            ]
        }

        # Act
        response = self.stack.invoke(
            payload,
            config={"configurable": {"thread_id": thread_1}},
        )

        # Assert
        self.assertEqual(response["thread_id"], thread_1)
        self.assertIn("Vijayaraj Benjamin", response["final_answer"])
        self.assertIsInstance(response["ai_output"], AIOutput)
        self.assertEqual(len(response["messages"]), 2)

    def test_memory_inspection_in_store(self):
        """Arrange-Act-Assert: Verify memories can be inspected in store under ('default_user',)."""
        # Arrange
        namespace = ("default_user",)
        self.store.put(
            namespace,
            "preferences.md",
            {"content": "# User Profile\n- **Name**: Vijayaraj Benjamin\n- **Stack**: Python, PostgreSQL"},
        )

        # Act
        items = self.store.search(namespace)

        # Assert
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].key, "preferences.md")
        self.assertIn("Vijayaraj Benjamin", items[0].value["content"])

    def test_thread2_cross_thread_memory_recall(self):
        """Arrange-Act-Assert: Thread 2 recalls saved memory across distinct thread IDs."""
        # Arrange - Seed memory as if Thread 1 persisted it
        namespace = ("default_user",)
        self.store.put(
            namespace,
            "preferences.md",
            {"content": "- **User**: Vijayaraj Benjamin"},
        )
        thread_2 = str(uuid.uuid4())
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": "What is my name?",
                }
            ]
        }

        # Act
        response = self.stack.invoke(
            payload,
            config={"configurable": {"thread_id": thread_2}},
        )

        # Assert
        self.assertEqual(response["thread_id"], thread_2)
        self.assertIn("Vijayaraj Benjamin", response["final_answer"])

    def test_end_to_end_3_step_lifecycle(self):
        """Arrange-Act-Assert: Full execution of TEST 1 -> TEST 2 -> TEST 3 seamlessly."""
        # Arrange
        thread_1 = str(uuid.uuid4())
        thread_2 = str(uuid.uuid4())
        self.assertNotEqual(thread_1, thread_2)

        # Step 1: Thread 1 - User Introduction
        res_1 = self.stack.invoke(
            "Hi, my name is Vijayaraj Benjamin.",
            thread_id=thread_1,
        )
        self.assertIn("Vijayaraj Benjamin", res_1["final_answer"])

        # Step 2: Store Inspection & Verification
        self.store.put(
            ("default_user",),
            "preferences.md",
            {"content": "Name: Vijayaraj Benjamin"},
        )
        items = self.stack.store.search(("default_user",))
        self.assertGreaterEqual(len(items), 1)

        # Step 3: Thread 2 - Recall in separate conversation thread
        res_2 = self.stack.invoke(
            "What is my name?",
            thread_id=thread_2,
        )
        self.assertEqual(res_2["thread_id"], thread_2)
        self.assertIn("Vijayaraj Benjamin", res_2["final_answer"])


class TestRealGroqModelIntegration(unittest.TestCase):
    """Real live integration tests utilizing GROQ_API_KEY from .env loaded via python-dotenv."""

    def setUp(self):
        """Arrange: Load GROQ_API_KEY from .env and initialize ChatGroq."""
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if not self.groq_api_key:
            self.skipTest("GROQ_API_KEY is not set in .env file or environment.")

        from langchain_groq import ChatGroq

        model_name = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        self.real_llm = ChatGroq(
            model_name=model_name,
            api_key=self.groq_api_key,
            temperature=0,
            max_retries=1,
        )

    def test_real_groq_api_key_loaded_and_generates_response(self):
        """Arrange-Act-Assert: Verify GROQ_API_KEY loaded via dotenv successfully invokes Groq LLM."""
        response = self.real_llm.invoke("Hi, my name is Vijayaraj Benjamin.")
        self.assertIsNotNone(response.content)
        self.assertTrue(len(str(response.content)) > 0)
        self.assertIn("Vijayaraj", str(response.content))

    def test_real_groq_memory_conversation_query(self):
        """Arrange-Act-Assert: Verify real Groq LLM generates conversational memory response."""
        messages = [
            {"role": "system", "content": "You remember the user profile: Name is Vijayaraj Benjamin."},
            {"role": "user", "content": "What is my name?"},
        ]
        response = self.real_llm.invoke(messages)
        self.assertIsNotNone(response.content)
        self.assertIn("Vijayaraj", str(response.content))


if __name__ == "__main__":
    unittest.main()
