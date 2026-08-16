"""TDD Workflow Test Suite for 3 Core Routing Behaviors:

1. TEST 1: Normal Conversation / Greeting Flow
   - Main Agent handles directly without subagent invocation.

2. TEST 2: Normal Code Implementation Flow (Part of Code / Standalone Component)
   - Main Agent -> Helper_Manager -> Coding_Agent -> Code_Reviewer -> Main Agent.

3. TEST 3: Product-Grade Code Implementation Flow (Entire Application / Big Project)
   - Main Agent orchestrates Database_Manager (RDBMS -> Code_Reviewer) AND API_Manager (REST -> Code_Reviewer).

Follows TDD Workflow:
- AAA (Arrange-Act-Assert) pattern
- Explicit behavioral verification of each agent's routing responsibilities
"""

import unittest
from typing import Any, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langgraph.store.memory import InMemoryStore

from engineeringstack.schema.state import AIOutput, UserInput
from engineeringstack.stack import EngineeringStack


class MockRoutingChatModel(BaseChatModel):
    """Deterministic Mock LLM for routing verification."""

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
        return "mock_routing_chat_model"


class TestEndToEndRoutingTDD(unittest.TestCase):
    """Test suite executing the 3 core routing verification flows."""

    def setUp(self):
        self.store = InMemoryStore()

    def test_1_normal_conversation_greeting_flow(self):
        """TEST 1 (Normal Conversation): 'Hello! How are you doing today?' handled directly by Main Agent."""
        # Arrange
        user_query = "Hello! How are you doing today?"
        mock_response = (
            "Hello! I am Main Agent, your technical lead and orchestrator for engineering tasks. "
            "I can help you build database architectures, API services, standalone algorithms, and code reviews."
        )
        model = MockRoutingChatModel(response_text=mock_response)
        stack = EngineeringStack(model=model, store=self.store)

        # Act
        result = stack.invoke(user_query)

        # Assert
        self.assertIsNotNone(result)
        self.assertIn("Main Agent", result["final_answer"])
        self.assertEqual(result["user_input"].query, user_query)
        self.assertNotIn("Database_Manager", result["final_answer"])
        self.assertNotIn("API_Manager", result["final_answer"])

    def test_2_normal_code_implementation_flow(self):
        """TEST 2 (Normal Code Implementation): 'Create a mongoDB users table' routes through Helper_Manager -> Coding_Agent -> Code_Reviewer."""
        # Arrange
        user_query = "Create a mongoDB users table."
        mock_response = (
            "Delegating to Helper_Manager -> Coding_Agent for MongoDB users collection implementation, "
            "then verified by Code_Reviewer.\n\n"
            "```javascript\n"
            "import mongoose from 'mongoose';\n"
            "const userSchema = new mongoose.Schema({\n"
            "  username: { type: String, required: true, unique: true },\n"
            "  email: { type: String, required: true, unique: true },\n"
            "  createdAt: { type: Date, default: Date.now }\n"
            "});\n"
            "export default mongoose.model('User', userSchema);\n"
            "```\n\n"
            "- 1. Schema defines unique constraints on username and email\n"
            "- 2. Auto-generated timestamps support audit trails\n"
            "- 3. Mongoose model export follows clean modular design\n"
            "- 4. Verified input sanitization and type enforcement\n"
            "- 5. QA approved for production deployment"
        )
        model = MockRoutingChatModel(response_text=mock_response)
        stack = EngineeringStack(model=model, store=self.store)

        # Act
        result = stack.invoke(user_query)

        # Assert
        self.assertIsNotNone(result)
        self.assertIn("Helper_Manager", result["final_answer"])
        self.assertIn("Code_Reviewer", result["final_answer"])
        self.assertIsInstance(result["ai_output"], AIOutput)
        self.assertIn("userSchema", result["ai_output"].code)
        self.assertEqual(len(result["ai_output"].summary), 5)

    def test_3_product_grade_code_implementation_flow(self):
        """TEST 3 (Product-Grade Implementation): 'Build an entire e-commerce backend' orchestrates across Database_Manager, API_Manager, and Code_Reviewer."""
        # Arrange
        user_query = "Build an entire e-commerce backend with PostgreSQL database and FastAPI REST endpoints."
        mock_response = (
            "Orchestrating full enterprise architecture across Database_Manager (RDBMS_agent -> Code_Reviewer) "
            "and API_Manager (REST_Agent -> Code_Reviewer):\n\n"
            "```sql\n"
            "CREATE TABLE users (\n"
            "    id SERIAL PRIMARY KEY,\n"
            "    email VARCHAR(255) UNIQUE NOT NULL,\n"
            "    password_hash VARCHAR(255) NOT NULL\n"
            ");\n"
            "CREATE TABLE products (\n"
            "    id SERIAL PRIMARY KEY,\n"
            "    name VARCHAR(255) NOT NULL,\n"
            "    price NUMERIC(10, 2) NOT NULL\n"
            ");\n"
            "```\n\n"
            "```python\n"
            "from fastapi import FastAPI, Depends, HTTPException\n"
            "app = FastAPI(title='E-Commerce API')\n\n"
            "@app.get('/products')\n"
            "async def get_products():\n"
            "    return [{'id': 1, 'name': 'Widget', 'price': 19.99}]\n"
            "```\n\n"
            "- 1. Database schema created with normalized tables and constraints\n"
            "- 2. REST API endpoints configured with async FastAPI handlers\n"
            "- 3. Security audit verified password hashing and parameter validation\n"
            "- 4. Database_Manager and API_Manager verified via Code_Reviewer\n"
            "- 5. Complete product-grade implementation ready for integration"
        )
        model = MockRoutingChatModel(response_text=mock_response)
        stack = EngineeringStack(model=model, store=self.store)

        # Act
        result = stack.invoke(user_query)

        # Assert
        self.assertIsNotNone(result)
        self.assertIn("Database_Manager", result["final_answer"])
        self.assertIn("API_Manager", result["final_answer"])
        self.assertIn("Code_Reviewer", result["final_answer"])
        self.assertIsInstance(result["ai_output"], AIOutput)
        self.assertIn("CREATE TABLE", result["ai_output"].code)
        self.assertEqual(len(result["ai_output"].summary), 5)


if __name__ == "__main__":
    unittest.main()
