"""Unit tests for subagent builder factories and manager dictionaries.

Follows TDD Workflow:
- Arrange-Act-Assert (AAA) pattern
- Verifies subagent contracts, routing descriptions, and schema integrity
"""

import unittest
from engineeringstack.agents.managers.databasemanager import database_manager_subagent
from engineeringstack.agents.managers.apimanager import api_manager_subagent
from engineeringstack.agents.code_review.code_review import code_review_subagent
from engineeringstack.agents.database.rdms import rdms_subagent
from engineeringstack.agents.database.nosql import nosql_subagent
from engineeringstack.agents.database.redis import redis_subagent
from engineeringstack.agents.api.rest import rest_subagent
from engineeringstack.agents.api.graphql import graphql_subagent
from engineeringstack.agents.api.grpc import grpc_subagent
from engineeringstack.agents.api.soap import soap_subagent


from engineeringstack.builders.main_builder import (
    build_main_agent,
    evaluate_main_agent_input,
    get_helper_agents,
)
from engineeringstack.prompts.main_agent_prompt import MAIN_AGENT_SYSTEM_PROMPT
from engineeringstack.util.helper import RouteAction, IntentType


class TestSubAgentBuilders(unittest.TestCase):
    """Test suite for domain specialist and manager subagent definitions."""

    def test_database_manager_contract(self):
        """Arrange-Act-Assert: Database Manager returns compliant subagent dict."""
        # Act
        subagent = database_manager_subagent()

        # Assert
        self.assertEqual(subagent["name"], "Database_Manager")
        self.assertIn("Router only", subagent["description"])
        self.assertIn("system_prompt", subagent)
        self.assertTrue(hasattr(subagent["runnable"], "invoke"))

    def test_api_manager_contract(self):
        """Arrange-Act-Assert: API Manager returns compliant subagent dict."""
        # Act
        subagent = api_manager_subagent()

        # Assert
        self.assertEqual(subagent["name"], "API_Manager")
        self.assertIn("Router only", subagent["description"])
        self.assertIn("system_prompt", subagent)
        self.assertTrue(hasattr(subagent["runnable"], "invoke"))

    def test_code_review_subagent_contract(self):
        """Arrange-Act-Assert: Code Reviewer returns compliant subagent dict."""
        # Act
        subagent = code_review_subagent()

        # Assert
        self.assertEqual(subagent["name"], "Code_Reviewer")
        self.assertIn("Reviews existing code only", subagent["description"])
        self.assertTrue(hasattr(subagent["runnable"], "invoke"))

    def test_database_domain_specialists_contracts(self):
        """Arrange-Act-Assert: RDMS, NoSQL, and Redis specialist subagents have valid contracts."""
        # Act & Assert
        rdms = rdms_subagent()
        self.assertEqual(rdms["name"], "RDMS_agent")
        self.assertTrue(hasattr(rdms["runnable"], "invoke"))

        nosql = nosql_subagent()
        self.assertEqual(nosql["name"], "NoSQL_agent")
        self.assertTrue(hasattr(nosql["runnable"], "invoke"))

        redis = redis_subagent()
        self.assertEqual(redis["name"], "REDIS_agent")
        self.assertTrue(hasattr(redis["runnable"], "invoke"))

    def test_api_domain_specialists_contracts(self):
        """Arrange-Act-Assert: REST, GraphQL, gRPC, and SOAP specialist subagents have valid contracts."""
        # Act & Assert
        rest = rest_subagent()
        self.assertEqual(rest["name"], "REST_Agent")
        self.assertTrue(hasattr(rest["runnable"], "invoke"))

        graphql = graphql_subagent()
        self.assertEqual(graphql["name"], "GraphQL_Agent")
        self.assertTrue(hasattr(graphql["runnable"], "invoke"))

        grpc = grpc_subagent()
        self.assertEqual(grpc["name"], "GRPC_Agent")
        self.assertTrue(hasattr(grpc["runnable"], "invoke"))

        soap = soap_subagent()
        self.assertEqual(soap["name"], "SOAP_Agent")
        self.assertTrue(hasattr(soap["runnable"], "invoke"))

    def test_get_helper_agents(self):
        """Arrange-Act-Assert: get_helper_agents returns all 3 helper subagents."""
        helpers = get_helper_agents()
        self.assertEqual(len(helpers), 3)
        names = {h["name"] for h in helpers}
        self.assertEqual(names, {"Database_Manager", "API_Manager", "Code_Reviewer"})

    def test_evaluate_main_agent_input_greeting(self):
        """Arrange-Act-Assert: evaluate_main_agent_input routes greeting to DIRECT_ANSWER."""
        decision = evaluate_main_agent_input("Hello! How can you help me?")
        self.assertEqual(decision.action, RouteAction.DIRECT_ANSWER)
        self.assertIsNone(decision.target_agent)
        self.assertTrue(decision.is_conversational)
        self.assertIsNotNone(decision.direct_response)

    def test_evaluate_main_agent_input_coding(self):
        """Arrange-Act-Assert: evaluate_main_agent_input routes coding to DELEGATE_TO_HELPERS."""
        decision = evaluate_main_agent_input("Build a FastAPI REST API with PostgreSQL")
        self.assertEqual(decision.action, RouteAction.DELEGATE_TO_HELPERS)
        self.assertIsNotNone(decision.target_agent)
        self.assertTrue(decision.is_coding_or_complex)
        self.assertIsNotNone(decision.task_description)

    def test_reframed_main_agent_prompt_content(self):
        """Ensure MAIN_AGENT_SYSTEM_PROMPT explicitly specifies greetings vs technical delegation."""
        self.assertIn("GREETINGS & NORMAL CONVERSATIONS (ANSWER DIRECTLY)", MAIN_AGENT_SYSTEM_PROMPT)
        self.assertIn("CODING & COMPLEX ENGINEERING TASKS (USE HELPER AGENTS)", MAIN_AGENT_SYSTEM_PROMPT)
        self.assertIn("API_Manager", MAIN_AGENT_SYSTEM_PROMPT)
        self.assertIn("Database_Manager", MAIN_AGENT_SYSTEM_PROMPT)
        self.assertIn("Code_Reviewer", MAIN_AGENT_SYSTEM_PROMPT)
        self.assertIn("Do NOT invoke helper subagents for simple greetings", MAIN_AGENT_SYSTEM_PROMPT)


if __name__ == "__main__":
    unittest.main()

