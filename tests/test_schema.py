"""Unit tests for EngineeringStack schemas (UserInput, MainAgentOutput, AIOutput).

Follows TDD Workflow:
- Arrange, Act, Assert (AAA) pattern
- Tests behaviors, boundary conditions, and validation rules
"""

import unittest
from pydantic import ValidationError
from engineeringstack.schema.state import UserInput, MainAgentOutput, AIOutput


class TestUserInputSchema(unittest.TestCase):
    """Test suite for UserInput schema."""

    def test_user_input_creation_happy_path(self):
        """Arrange-Act-Assert: Valid instantiation with all fields."""
        # Arrange
        data = {
            "query": "Build a FastAPI microservice",
            "requirements": "Auth and CRUD endpoints",
            "framework": "FastAPI",
            "language": "Python",
            "database": "PostgreSQL",
        }

        # Act
        user_input = UserInput(**data)

        # Assert
        self.assertEqual(user_input.query, "Build a FastAPI microservice")
        self.assertEqual(user_input.requirements, "Auth and CRUD endpoints")
        self.assertEqual(user_input.framework, "FastAPI")
        self.assertEqual(user_input.language, "Python")
        self.assertEqual(user_input.database, "PostgreSQL")

    def test_user_input_defaults_for_optional_fields(self):
        """Arrange-Act-Assert: Optional fields default to None."""
        # Arrange & Act
        user_input = UserInput(query="Simple query")

        # Assert
        self.assertEqual(user_input.query, "Simple query")
        self.assertIsNone(user_input.requirements)
        self.assertIsNone(user_input.framework)
        self.assertIsNone(user_input.language)
        self.assertIsNone(user_input.database)

    def test_user_input_missing_query_raises_validation_error(self):
        """Arrange-Act-Assert: Missing required query field raises ValidationError."""
        # Arrange
        invalid_data = {"framework": "Flask"}

        # Act & Assert
        with self.assertRaises(ValidationError):
            UserInput(**invalid_data)


class TestMainAgentOutputSchema(unittest.TestCase):
    """Test suite for MainAgentOutput schema."""

    def test_main_agent_output_defaults(self):
        """Arrange-Act-Assert: All fields default to None when empty."""
        # Act
        output = MainAgentOutput()

        # Assert
        self.assertIsNone(output.requirements)
        self.assertIsNone(output.framework)
        self.assertIsNone(output.manager)
        self.assertIsNone(output.specialist)

    def test_main_agent_output_custom_values(self):
        """Arrange-Act-Assert: Custom manager and specialist fields populate correctly."""
        # Arrange
        data = {
            "requirements": "Create users table with migrations",
            "framework": "SQLAlchemy",
            "manager": "Database_Manager",
            "specialist": "RDMS_Agent",
        }

        # Act
        output = MainAgentOutput(**data)

        # Assert
        self.assertEqual(output.manager, "Database_Manager")
        self.assertEqual(output.specialist, "RDMS_Agent")
        self.assertEqual(output.framework, "SQLAlchemy")


class TestAIOutputSchema(unittest.TestCase):
    """Test suite for AIOutput schema."""

    def test_ai_output_valid_creation(self):
        """Arrange-Act-Assert: AIOutput with summary list and code."""
        # Arrange
        summary_bullets = [
            "Parsed request",
            "Configured models",
            "Created router",
            "Implemented DB layer",
            "Ran tests",
        ]
        code = "print('Hello World')"

        # Act
        ai_output = AIOutput(summary=summary_bullets, code=code)

        # Assert
        self.assertEqual(len(ai_output.summary), 5)
        self.assertEqual(ai_output.code, code)

    def test_ai_output_missing_code_raises_error(self):
        """Arrange-Act-Assert: AIOutput requires code field."""
        # Arrange
        invalid_data = {"summary": ["Step 1", "Step 2"]}

        # Act & Assert
        with self.assertRaises(ValidationError):
            AIOutput(**invalid_data)


if __name__ == "__main__":
    unittest.main()
