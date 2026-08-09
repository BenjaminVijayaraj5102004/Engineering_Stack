"""Comprehensive unit tests for input normalization and output extraction edge cases.

Follows TDD Workflow:
- AAA (Arrange-Act-Assert) pattern
- Tests Happy Path, Boundary, and Edge Cases
"""

import unittest
from langchain_core.messages import AIMessage, HumanMessage
from engineeringstack.schema.state import AIOutput, UserInput
from engineeringstack.stack import EngineeringStack


class TestNormalizationEdgeCases(unittest.TestCase):
    """Test suite for input normalization and output parsing edge cases."""

    def setUp(self):
        self.stack = EngineeringStack.__new__(EngineeringStack)

    # -------------------------------------------------------------
    # Input Normalization Tests
    # -------------------------------------------------------------

    def test_normalize_raw_string_with_excess_whitespace(self):
        """Arrange-Act-Assert: String input with whitespace is wrapped in UserInput and payload."""
        # Arrange
        raw_query = "   \n\t Build a GraphQL endpoint \t\n  "

        # Act
        user_input, payload = self.stack._normalize_input(raw_query)

        # Assert
        self.assertIsInstance(user_input, UserInput)
        self.assertEqual(user_input.query, raw_query)
        self.assertEqual(len(payload["messages"]), 1)
        self.assertIn("Build a GraphQL endpoint", payload["messages"][0]["content"])

    def test_normalize_user_input_object_with_all_fields(self):
        """Arrange-Act-Assert: UserInput object with full metadata produces structured prompt."""
        # Arrange
        input_obj = UserInput(
            query="Build User Service",
            requirements="OAuth2, JWT authentication",
            framework="FastAPI",
            language="Python",
            database="PostgreSQL",
        )

        # Act
        user_input, payload = self.stack._normalize_input(input_obj)

        # Assert
        self.assertEqual(user_input, input_obj)
        content = payload["messages"][0]["content"]
        self.assertIn("Requirements: OAuth2, JWT authentication", content)
        self.assertIn("Framework: FastAPI", content)
        self.assertIn("Language: Python", content)
        self.assertIn("Database: PostgreSQL", content)

    def test_normalize_dict_with_query_key(self):
        """Arrange-Act-Assert: Dict containing query key initializes UserInput."""
        # Arrange
        input_dict = {
            "query": "Create Redis cache layer",
            "framework": "FastAPI",
            "database": "Redis",
        }

        # Act
        user_input, payload = self.stack._normalize_input(input_dict)

        # Assert
        self.assertEqual(user_input.query, "Create Redis cache layer")
        self.assertEqual(user_input.database, "Redis")
        self.assertIn("Database: Redis", payload["messages"][0]["content"])

    def test_normalize_dict_with_messages_list_mixed_types(self):
        """Arrange-Act-Assert: Dict with mixed dict and LangChain message objects extracts history."""
        # Arrange
        input_dict = {
            "messages": [
                {"role": "user", "content": "Initial prompt"},
                {"role": "assistant", "content": "Assistant reply"},
                HumanMessage(content="Follow-up question on database indexing"),
            ]
        }

        # Act
        user_input, payload = self.stack._normalize_input(input_dict)

        # Assert
        self.assertEqual(user_input.query, "Follow-up question on database indexing")
        self.assertEqual(len(payload["messages"]), 3)
        self.assertEqual(payload["messages"][0]["role"], "user")
        self.assertEqual(payload["messages"][1]["role"], "assistant")
        self.assertEqual(payload["messages"][2]["role"], "user")
        self.assertEqual(payload["messages"][2]["content"], "Follow-up question on database indexing")

    def test_normalize_empty_dict_fallback(self):
        """Arrange-Act-Assert: Empty dict falls back to string representation without crashing."""
        # Arrange
        empty_dict = {}

        # Act
        user_input, payload = self.stack._normalize_input(empty_dict)

        # Assert
        self.assertIsInstance(user_input, UserInput)
        self.assertEqual(user_input.query, "{}")

    def test_normalize_unicode_and_emojis(self):
        """Arrange-Act-Assert: Unicode characters and emojis are handled properly."""
        # Arrange
        unicode_query = "⚡ Implement REST API with 🚀 FastAPI and 🐍 Python (日本語/العربية)"

        # Act
        user_input, payload = self.stack._normalize_input(unicode_query)

        # Assert
        self.assertEqual(user_input.query, unicode_query)
        self.assertIn("⚡ Implement REST API", payload["messages"][0]["content"])

    # -------------------------------------------------------------
    # Output Parsing & AIOutput Extraction Tests
    # -------------------------------------------------------------

    def test_extract_final_answer_from_aimessage_without_tool_calls(self):
        """Arrange-Act-Assert: Last AIMessage without tool calls is extracted as final answer."""
        # Arrange
        messages = [
            HumanMessage(content="Hello"),
            AIMessage(content="", tool_calls=[{"name": "ls", "args": {}, "id": "call_123"}]),
            AIMessage(content="Final generated response"),
        ]

        # Act
        final_answer = self.stack._extract_final_answer(messages)

        # Assert
        self.assertEqual(final_answer, "Final generated response")

    def test_extract_final_answer_from_assistant_dict_message(self):
        """Arrange-Act-Assert: Dict assistant message is extracted properly."""
        # Arrange
        messages = [
            {"role": "user", "content": "Build API"},
            {"role": "assistant", "content": "Here is your API code."},
        ]

        # Act
        final_answer = self.stack._extract_final_answer(messages)

        # Assert
        self.assertEqual(final_answer, "Here is your API code.")

    def test_extract_ai_output_with_multiple_code_blocks(self):
        """Arrange-Act-Assert: Multiple markdown code blocks are joined together."""
        # Arrange
        text = (
            "Here is the database schema:\n"
            "```sql\nCREATE TABLE users (id SERIAL PRIMARY KEY);\n```\n"
            "And here is the FastAPI router:\n"
            "```python\n@app.get('/users')\ndef get_users(): pass\n```\n"
            "- 1. Designed database table\n"
            "- 2. Built FastAPI route\n"
        )
        messages = [{"role": "assistant", "content": text}]

        # Act
        output = self.stack._extract_ai_output(messages)

        # Assert
        self.assertIsInstance(output, AIOutput)
        self.assertIn("CREATE TABLE users", output.code)
        self.assertIn("@app.get('/users')", output.code)
        self.assertEqual(len(output.summary), 5)
        self.assertIn("Designed database table", output.summary[0])

    def test_extract_ai_output_padding_fallback_bullets(self):
        """Arrange-Act-Assert: Summaries with fewer than 5 points are padded to 5."""
        # Arrange
        text = (
            "```python\ndef test(): pass\n```\n"
            "• Only one bullet point provided\n"
        )
        messages = [{"role": "assistant", "content": text}]

        # Act
        output = self.stack._extract_ai_output(messages)

        # Assert
        self.assertEqual(len(output.summary), 5)
        self.assertEqual(output.summary[0], "Only one bullet point provided")
        self.assertEqual(output.summary[1], "Routed task through Main Agent and specialized Manager.")

    def test_extract_ai_output_truncation_when_exceeding_5(self):
        """Arrange-Act-Assert: Summaries with more than 5 points are truncated to 5."""
        # Arrange
        text = (
            "```python\nx = 1\n```\n"
            "1. First step\n"
            "2. Second step\n"
            "3. Third step\n"
            "4. Fourth step\n"
            "5. Fifth step\n"
            "6. Sixth step\n"
            "7. Seventh step\n"
        )
        messages = [{"role": "assistant", "content": text}]

        # Act
        output = self.stack._extract_ai_output(messages)

        # Assert
        self.assertEqual(len(output.summary), 5)
        self.assertEqual(output.summary[4], "Fifth step")

    def test_extract_ai_output_empty_messages(self):
        """Arrange-Act-Assert: Empty message list returns default empty code and 5 fallback summary points."""
        # Arrange
        messages = []

        # Act
        output = self.stack._extract_ai_output(messages)

        # Assert
        self.assertEqual(output.code, "")
        self.assertEqual(len(output.summary), 5)


if __name__ == "__main__":
    unittest.main()
