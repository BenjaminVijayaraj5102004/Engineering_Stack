"""Unit tests for the Main Agent helper utility in engineeringstack.util.helper."""

import unittest
from engineeringstack.schema.state import UserInput
from engineeringstack.util.helper import (
    HelperAgentType,
    IntentType,
    RouteAction,
    RoutingDecision,
    classify_intent,
    determine_helper_agent,
    extract_query_text,
    format_delegation_payload,
    generate_conversational_response,
    get_main_agent_action,
    is_coding_or_complex_task,
    is_conversation,
    is_greeting,
    is_greeting_or_conversation,
    main_agent_helper,
    should_delegate_to_helpers,
)


class TestMainAgentHelper(unittest.TestCase):
    """Test suite for Main Agent helper functions."""

    def test_extract_query_text(self):
        """Test extraction of query string across different input structures."""
        # 1. Plain string
        self.assertEqual(extract_query_text("Hello world"), "Hello world")
        self.assertEqual(extract_query_text("   trimmed query   "), "trimmed query")

        # 2. UserInput object
        user_input = UserInput(query="Build a FastAPI app")
        self.assertEqual(extract_query_text(user_input), "Build a FastAPI app")

        # 3. Dict with query
        self.assertEqual(extract_query_text({"query": "Create PostgreSQL table"}), "Create PostgreSQL table")

        # 4. Dict with messages payload
        payload = {
            "messages": [
                {"role": "system", "content": "System prompt"},
                {"role": "user", "content": "Review my Python code"},
            ]
        }
        self.assertEqual(extract_query_text(payload), "Review my Python code")

        # 5. None / empty
        self.assertEqual(extract_query_text(None), "")
        self.assertEqual(extract_query_text(""), "")

    def test_greeting_detection(self):
        """Test greeting detection for standard greetings."""
        greetings = [
            "Hi",
            "Hello there!",
            "Hey",
            "good morning",
            "Good afternoon",
            "howdy partner",
            "Greetings!",
            "sup",
            "Yo!",
        ]
        for g in greetings:
            self.assertTrue(is_greeting(g), f"Failed to identify '{g}' as greeting")
            self.assertTrue(is_greeting_or_conversation(g), f"Failed to identify '{g}' as greeting/conversation")
            self.assertFalse(is_coding_or_complex_task(g), f"False positive: '{g}' marked as coding")

    def test_conversation_detection(self):
        """Test detection of normal casual conversations."""
        convs = [
            "Who are you?",
            "What can you do?",
            "How are you doing today?",
            "Tell me about yourself",
            "Thank you so much!",
            "Thanks a lot",
            "Goodbye!",
            "Bye, see you later",
            "Cool, got it.",
            "understood",
        ]
        for c in convs:
            self.assertTrue(is_conversation(c) or is_greeting_or_conversation(c), f"Failed to detect conversation: '{c}'")
            self.assertFalse(is_coding_or_complex_task(c), f"False positive: '{c}' marked as coding")

    def test_coding_and_complex_task_detection(self):
        """Test detection of coding, API, database, and complex tasks."""
        tasks = [
            "Create a Flask REST API for user registration",
            "Build a FastAPI endpoint with JWT authentication",
            "Design a PostgreSQL database schema for e-commerce",
            "Write MongoDB aggregation queries for monthly sales reports",
            "Configure Redis caching for session tokens",
            "Review this Python function for security vulnerabilities and race conditions",
            "Implement a Quicksort algorithm in TypeScript",
            "Build a gRPC service for real-time order processing",
            "Create a GraphQL mutation for updating product inventory",
            "Refactor this Django model and add database migration",
        ]
        for t in tasks:
            self.assertTrue(is_coding_or_complex_task(t), f"Failed to detect technical task: '{t}'")
            self.assertFalse(is_greeting_or_conversation(t), f"False negative: '{t}' marked as conversation")

    def test_intent_classification(self):
        """Test classification of specific intent categories."""
        self.assertEqual(classify_intent("Hello!"), IntentType.GREETING)
        self.assertEqual(classify_intent("Who are you and what do you do?"), IntentType.CONVERSATION)
        self.assertEqual(classify_intent("Build a REST API with FastAPI"), IntentType.API_TASK)
        self.assertEqual(classify_intent("Design a PostgreSQL schema with indexes"), IntentType.DATABASE_TASK)
        self.assertEqual(classify_intent("Review this code for bugs and memory leaks"), IntentType.CODE_REVIEW_TASK)
        self.assertEqual(classify_intent("Write a Python function to compute Fibonacci"), IntentType.GENERAL_CODING_TASK)

    def test_determine_helper_agent(self):
        """Test target helper subagent selection based on intent."""
        self.assertEqual(
            determine_helper_agent(IntentType.API_TASK, "FastAPI endpoint"),
            HelperAgentType.API_MANAGER.value,
        )
        self.assertEqual(
            determine_helper_agent(IntentType.DATABASE_TASK, "Postgres table"),
            HelperAgentType.DATABASE_MANAGER.value,
        )
        self.assertEqual(
            determine_helper_agent(IntentType.CODE_REVIEW_TASK, "Audit security"),
            HelperAgentType.CODE_REVIEWER.value,
        )
        self.assertIsNone(determine_helper_agent(IntentType.GREETING, "Hello"))

    def test_main_agent_helper_for_greetings(self):
        """Test main_agent_helper routing decision for greetings (direct answer)."""
        queries = ["Hello!", "Hi there", "Good morning"]
        for q in queries:
            decision = main_agent_helper(q)
            self.assertIsInstance(decision, RoutingDecision)
            self.assertEqual(decision.action, RouteAction.DIRECT_ANSWER)
            self.assertIsNone(decision.target_agent)
            self.assertTrue(decision.is_conversational)
            self.assertFalse(decision.is_coding_or_complex)
            self.assertIsNotNone(decision.direct_response)
            self.assertIn("Main Agent", decision.direct_response)
            self.assertFalse(should_delegate_to_helpers(q))

    def test_main_agent_helper_for_normal_conversation(self):
        """Test main_agent_helper routing decision for casual conversation (direct answer)."""
        queries = ["Who are you?", "What can you do?", "How are you?"]
        for q in queries:
            decision = main_agent_helper(q)
            self.assertEqual(decision.action, RouteAction.DIRECT_ANSWER)
            self.assertIsNone(decision.target_agent)
            self.assertTrue(decision.is_conversational)
            self.assertFalse(decision.is_coding_or_complex)
            self.assertIsNotNone(decision.direct_response)
            self.assertFalse(should_delegate_to_helpers(q))

    def test_main_agent_helper_for_api_task(self):
        """Test main_agent_helper routing decision for API coding tasks (delegate to helper)."""
        query = "Create a FastAPI REST API with endpoints for user CRUD"
        decision = main_agent_helper(query)
        self.assertEqual(decision.action, RouteAction.DELEGATE_TO_HELPERS)
        self.assertEqual(decision.target_agent, HelperAgentType.API_MANAGER.value)
        self.assertFalse(decision.is_conversational)
        self.assertTrue(decision.is_coding_or_complex)
        self.assertIsNone(decision.direct_response)
        self.assertIn("Execute technical engineering task", decision.task_description)
        self.assertTrue(should_delegate_to_helpers(query))

    def test_main_agent_helper_for_database_task(self):
        """Test main_agent_helper routing decision for Database coding tasks (delegate to helper)."""
        query = "Design a PostgreSQL schema for an order management system"
        decision = main_agent_helper(query)
        self.assertEqual(decision.action, RouteAction.DELEGATE_TO_HELPERS)
        self.assertEqual(decision.target_agent, HelperAgentType.DATABASE_MANAGER.value)
        self.assertFalse(decision.is_conversational)
        self.assertTrue(decision.is_coding_or_complex)
        self.assertTrue(should_delegate_to_helpers(query))

    def test_main_agent_helper_for_code_review_task(self):
        """Test main_agent_helper routing decision for Code Review tasks (delegate to helper)."""
        query = "Review this Python code snippet for SQL injection vulnerabilities"
        decision = main_agent_helper(query)
        self.assertEqual(decision.action, RouteAction.DELEGATE_TO_HELPERS)
        self.assertEqual(decision.target_agent, HelperAgentType.CODE_REVIEWER.value)
        self.assertFalse(decision.is_conversational)
        self.assertTrue(decision.is_coding_or_complex)
        self.assertTrue(should_delegate_to_helpers(query))

    def test_main_agent_helper_with_user_input_object(self):
        """Test main_agent_helper when input is a UserInput object with metadata."""
        user_input = UserInput(
            query="Build a CRUD service",
            framework="FastAPI",
            language="Python",
            database="PostgreSQL",
        )
        decision = main_agent_helper(user_input)
        self.assertEqual(decision.action, RouteAction.DELEGATE_TO_HELPERS)
        self.assertIn("Framework: FastAPI", decision.task_description)
        self.assertIn("Database: PostgreSQL", decision.task_description)

    def test_get_main_agent_action_convenience(self):
        """Test get_main_agent_action tuple helper."""
        action, agent, content = get_main_agent_action("Hello there!")
        self.assertEqual(action, RouteAction.DIRECT_ANSWER)
        self.assertIsNone(agent)
        self.assertIn("Main Agent", content)

        action, agent, content = get_main_agent_action("Build a GraphQL server in Node.js")
        self.assertEqual(action, RouteAction.DELEGATE_TO_HELPERS)
        self.assertEqual(agent, HelperAgentType.API_MANAGER.value)
        self.assertIn("Execute technical engineering task", content)

    def test_format_delegation_payload(self):
        """Test format_delegation_payload matches task tool contract."""
        payload = format_delegation_payload("API_Manager", "Build REST API")
        self.assertEqual(payload, {"subagent_type": "API_Manager", "description": "Build REST API"})

    def test_generate_conversational_response(self):
        """Test generation of conversational responses."""
        resp_greeting = generate_conversational_response("hi")
        self.assertIn("Main Agent", resp_greeting)

        resp_thanks = generate_conversational_response("Thank you!")
        self.assertIn("welcome", resp_thanks.lower())

        resp_bye = generate_conversational_response("Goodbye!")
        self.assertIn("goodbye", resp_bye.lower())


if __name__ == "__main__":
    unittest.main()
