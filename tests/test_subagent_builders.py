"""Unit tests for subagent builder factories and manager dictionaries.

Follows TDD Workflow:
- Arrange-Act-Assert (AAA) pattern
- Verifies subagent contracts, routing descriptions, skills forwarding, and schema integrity
"""

import unittest
from engineeringstack.agents.managers.databasemanager import database_manager_subagent
from engineeringstack.agents.managers.apimanager import api_manager_subagent
from engineeringstack.agents.managers.helper_manager import helper_manager_subagent
from engineeringstack.agents.coding.coding import coding_subagent
from engineeringstack.agents.code_review.code_review import code_review_subagent
from engineeringstack.agents.database.rdbms import rdbms_subagent
from engineeringstack.agents.database.nosql import nosql_subagent
from engineeringstack.agents.database.redis import redis_subagent
from engineeringstack.agents.api.rest import rest_subagent
from engineeringstack.agents.api.graphql import graphql_subagent
from engineeringstack.agents.api.grpc import grpc_subagent
from engineeringstack.agents.api.soap import soap_subagent

from engineeringstack.builders.db_builder import build_database_manager
from engineeringstack.builders.api_builder import build_api_manager
from engineeringstack.builders.helper_builder import build_helper_manager
from engineeringstack.builders.main_builder import (
    build_main_agent,
    get_helper_agents,
)
from engineeringstack.prompts.main_agent_prompt import MAIN_AGENT_SYSTEM_PROMPT


class TestSubAgentBuilders(unittest.TestCase):
    """Test suite for domain specialist and manager subagent definitions."""

    def test_database_manager_contract(self):
        """Arrange-Act-Assert: Database Manager returns compliant subagent dict with skills."""
        # Act
        subagent = database_manager_subagent()

        # Assert
        self.assertEqual(subagent["name"], "Database_Manager")
        self.assertIn("Router only", subagent["description"])
        self.assertIn("system_prompt", subagent)
        self.assertTrue(hasattr(subagent["runnable"], "invoke"))

    def test_api_manager_contract(self):
        """Arrange-Act-Assert: API Manager returns compliant subagent dict with skills."""
        # Act
        subagent = api_manager_subagent()

        # Assert
        self.assertEqual(subagent["name"], "API_Manager")
        self.assertIn("Router only", subagent["description"])
        self.assertIn("system_prompt", subagent)
        self.assertTrue(hasattr(subagent["runnable"], "invoke"))

    def test_helper_manager_contract(self):
        """Arrange-Act-Assert: Helper Manager returns compliant subagent dict with skills."""
        # Act
        subagent = helper_manager_subagent()

        # Assert
        self.assertEqual(subagent["name"], "Helper_Manager")
        self.assertIn("Router only", subagent["description"])
        self.assertIn("system_prompt", subagent)
        self.assertTrue(hasattr(subagent["runnable"], "invoke"))

    def test_manager_builder_skills_forwarding(self):
        """Arrange-Act-Assert: Manager builders accept custom skills parameter."""
        custom_skills = ["/skills/custom/"]
        db_mgr = build_database_manager(skills=custom_skills)
        api_mgr = build_api_manager(skills=custom_skills)
        helper_mgr = build_helper_manager(skills=custom_skills)

        self.assertTrue(hasattr(db_mgr, "invoke"))
        self.assertTrue(hasattr(api_mgr, "invoke"))
        self.assertTrue(hasattr(helper_mgr, "invoke"))

    def test_coding_subagent_contract(self):
        """Arrange-Act-Assert: Coding Agent returns compliant subagent dict."""
        # Act
        subagent = coding_subagent()

        # Assert
        self.assertEqual(subagent["name"], "Coding_Agent")
        self.assertIn("Implements generic software code", subagent["description"])
        self.assertTrue(hasattr(subagent["runnable"], "invoke"))

    def test_code_review_subagent_contract(self):
        """Arrange-Act-Assert: Code Reviewer returns compliant subagent dict."""
        # Act
        subagent = code_review_subagent()

        # Assert
        self.assertEqual(subagent["name"], "Code_Reviewer")
        self.assertIn("Reviews existing code only", subagent["description"])
        self.assertTrue(hasattr(subagent["runnable"], "invoke"))

    def test_build_managers_return_runnable_graphs(self):
        """Arrange-Act-Assert: build_database_manager, build_api_manager, build_helper_manager return runnable graphs."""
        db_mgr = build_database_manager()
        api_mgr = build_api_manager()
        helper_mgr = build_helper_manager()

        self.assertTrue(hasattr(db_mgr, "invoke"))
        self.assertTrue(hasattr(api_mgr, "invoke"))
        self.assertTrue(hasattr(helper_mgr, "invoke"))

    def test_database_domain_specialists_contracts(self):
        """Arrange-Act-Assert: RDBMS, NoSQL, and Redis specialist subagents have valid contracts."""
        # Act & Assert
        rdbms = rdbms_subagent()
        self.assertEqual(rdbms["name"], "RDBMS_agent")
        self.assertTrue(hasattr(rdbms["runnable"], "invoke"))

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
        """Arrange-Act-Assert: get_helper_agents returns all 3 top-level managers."""
        helpers = get_helper_agents()
        self.assertEqual(len(helpers), 3)
        names = {h["name"] for h in helpers}
        self.assertEqual(names, {"Database_Manager", "API_Manager", "Helper_Manager"})

    def test_reframed_main_agent_prompt_content(self):
        """Ensure MAIN_AGENT_SYSTEM_PROMPT specifies identity, managers, and skill references."""
        self.assertIn("Main Agent", MAIN_AGENT_SYSTEM_PROMPT)
        self.assertIn("API_Manager", MAIN_AGENT_SYSTEM_PROMPT)
        self.assertIn("Database_Manager", MAIN_AGENT_SYSTEM_PROMPT)
        self.assertIn("Helper_Manager", MAIN_AGENT_SYSTEM_PROMPT)
        self.assertIn("loaded skills", MAIN_AGENT_SYSTEM_PROMPT)


if __name__ == "__main__":
    unittest.main()
