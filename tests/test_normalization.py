"""Unit tests for EngineeringStack input normalization and response extraction logic.

Follows TDD Workflow:
- Tests Arrange-Act-Assert (AAA) pattern
- Covers happy path, edge cases, and fallback mechanisms
"""

import unittest
from langchain_core.messages import AIMessage, HumanMessage
from engineeringstack.stack import EngineeringStack
from engineeringstack.schema.state import UserInput, AIOutput


class DummyAgent:
    """Mock agent for unit testing helper methods."""

    def invoke(self, payload, config=None, **kwargs):
        return {
            "messages": [
                {"role": "user", "content": "hello"},
                {"role": "assistant", "content": "Sample output\n\n```python\nprint('hello')\n```\n- Point 1\n- Point 2"},
            ]
        }


class TestInputNormalization(unittest.TestCase):
    """Test suite for EngineeringStack._normalize_input method."""

    def setUp(self):
        self.stack = EngineeringStack(agent=DummyAgent())

    def test_normalize_input_from_plain_string(self):
        """Arrange-Act-Assert: String input converts to UserInput and message payload."""
        # Arrange
        query_text = "Create a Flask REST API"

        # Act
        user_input, payload = self.stack._normalize_input(query_text)

        # Assert
        self.assertIsInstance(user_input, UserInput)
        self.assertEqual(user_input.query, query_text)
        self.assertIn("messages", payload)
        self.assertEqual(len(payload["messages"]), 1)
        self.assertEqual(payload["messages"][0]["role"], "user")
        self.assertIn(query_text, payload["messages"][0]["content"])

    def test_normalize_input_from_user_input_instance(self):
        """Arrange-Act-Assert: Direct UserInput instance retains all fields."""
        # Arrange
        custom_input = UserInput(
            query="Build MongoDB schema",
            framework="FastAPI",
            database="MongoDB",
        )

        # Act
        user_input, payload = self.stack._normalize_input(custom_input)

        # Assert
        self.assertEqual(user_input, custom_input)
        self.assertIn("Database: MongoDB", payload["messages"][0]["content"])
        self.assertIn("Framework: FastAPI", payload["messages"][0]["content"])

    def test_normalize_input_from_dict_with_query(self):
        """Arrange-Act-Assert: Dictionary containing 'query' parses into UserInput."""
        # Arrange
        data = {"query": "Write unit tests", "framework": "Pytest"}

        # Act
        user_input, payload = self.stack._normalize_input(data)

        # Assert
        self.assertEqual(user_input.query, "Write unit tests")
        self.assertEqual(user_input.framework, "Pytest")

    def test_normalize_input_from_dict_with_messages(self):
        """Arrange-Act-Assert: Dictionary containing conversation messages preserves history."""
        # Arrange
        data = {
            "messages": [
                {"role": "user", "content": "First question"},
                {"role": "assistant", "content": "First answer"},
                {"role": "user", "content": "Second question"},
            ]
        }

        # Act
        user_input, payload = self.stack._normalize_input(data)

        # Assert
        self.assertEqual(user_input.query, "Second question")
        self.assertEqual(len(payload["messages"]), 3)
        self.assertEqual(payload["messages"][0]["role"], "user")
        self.assertEqual(payload["messages"][1]["role"], "assistant")
        self.assertEqual(payload["messages"][2]["role"], "user")


class TestOutputExtraction(unittest.TestCase):
    """Test suite for final answer and AIOutput extraction."""

    def setUp(self):
        self.stack = EngineeringStack(agent=DummyAgent())

    def test_extract_final_answer_from_ai_messages(self):
        """Arrange-Act-Assert: Extract answer text from langchain AIMessage list."""
        # Arrange
        messages = [
            HumanMessage(content="Hello"),
            AIMessage(content="Final assistant response"),
        ]

        # Act
        answer = self.stack._extract_final_answer(messages)

        # Assert
        self.assertEqual(answer, "Final assistant response")

    def test_extract_final_answer_from_dict_messages(self):
        """Arrange-Act-Assert: Extract answer text from dictionary message format."""
        # Arrange
        messages = [
            {"role": "user", "content": "Query"},
            {"role": "assistant", "content": "Assistant answer"},
        ]

        # Act
        answer = self.stack._extract_final_answer(messages)

        # Assert
        self.assertEqual(answer, "Assistant answer")

    def test_extract_ai_output_code_blocks_and_bullet_points(self):
        """Arrange-Act-Assert: Code blocks and bullet points are properly extracted."""
        # Arrange
        assistant_content = (
            "Here is the solution:\n\n"
            "- Step 1: Initialize database\n"
            "- Step 2: Define ORM models\n"
            "- Step 3: Create FastAPI routes\n"
            "- Step 4: Write integration tests\n"
            "- Step 5: Package and deploy\n\n"
            "```python\ndef app():\n    return 'OK'\n```"
        )
        messages = [{"role": "assistant", "content": assistant_content}]

        # Act
        ai_output = self.stack._extract_ai_output(messages)

        # Assert
        self.assertIsInstance(ai_output, AIOutput)
        self.assertEqual(len(ai_output.summary), 5)
        self.assertEqual(ai_output.summary[0], "Step 1: Initialize database")
        self.assertIn("def app():", ai_output.code)

    def test_extract_ai_output_fallback_bullets_when_fewer_than_five(self):
        """Arrange-Act-Assert: Fewer than 5 bullets triggers fallback completion to reach exactly 5."""
        # Arrange
        assistant_content = (
            "Short answer:\n"
            "- Step 1: Configured service\n\n"
            "```python\nx = 42\n```"
        )
        messages = [{"role": "assistant", "content": assistant_content}]

        # Act
        ai_output = self.stack._extract_ai_output(messages)

        # Assert
        self.assertEqual(len(ai_output.summary), 5)
        self.assertEqual(ai_output.summary[0], "Step 1: Configured service")
        # Ensure remaining 4 items come from fallback bullets
        self.assertEqual(
            ai_output.summary[1],
            "Routed task through Main Agent and specialized Manager.",
        )


if __name__ == "__main__":
    unittest.main()
