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



if __name__ == "__main__":
    unittest.main()
