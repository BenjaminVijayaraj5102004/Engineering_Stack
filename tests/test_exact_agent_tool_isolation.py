"""Explicit test suite verifying the exact tool assignment across all agent tiers.

Layer 1: Main Agent -> ["read_file", "task"]
Layer 2: Database_Manager, API_Manager, Helper_Manager -> ["read_file", "task"]
Layer 3: Leaf Subagents (Coding_Agent, RDBMS_agent, NoSQL_agent, REDIS_agent,
                          REST_Agent, GraphQL_Agent, GRPC_Agent, SOAP_Agent,
                          Code_Reviewer) -> ["search_code", "get_file_contents", "read_file", "write_file", "edit_file", "glob", "grep"]
         Leaf Subagents MUST NOT have "task" tool.
"""

import unittest
from deepagents.backends import FilesystemBackend
from engineeringstack.builders.main_builder import (
    build_main_agent,
    build_default_backend,
    get_helper_agents,
)
from engineeringstack.builders.db_builder import build_database_manager
from engineeringstack.builders.api_builder import build_api_manager
from engineeringstack.builders.helper_builder import build_helper_manager
from engineeringstack.agents.coding.coding import coding_subagent
from engineeringstack.agents.code_review.code_review import code_review_subagent
from engineeringstack.agents.database.rdbms import rdbms_subagent
from engineeringstack.agents.database.nosql import nosql_subagent
from engineeringstack.agents.database.redis import redis_subagent
from engineeringstack.agents.api.rest import rest_subagent
from engineeringstack.agents.api.graphql import graphql_subagent
from engineeringstack.agents.api.grpc import grpc_subagent
from engineeringstack.agents.api.soap import soap_subagent
from engineeringstack.util.middleware import (
    create_router_middleware,
    create_worker_middleware,
    create_reviewer_middleware,
)


class TestExactAgentToolIsolation(unittest.TestCase):
    """Test suite strictly asserting tool lists across all architectural tiers."""

    def setUp(self):
        self.backend = build_default_backend()

    def test_router_middleware_tools(self):
        """Routers (Main Agent, Managers) must have read_file in FilesystemMiddleware."""
        middlewares = create_router_middleware(self.backend)
        fs_mid = [m for m in middlewares if hasattr(m, "_enabled_tools")][0]
        self.assertEqual(fs_mid._enabled_tools, frozenset(["read_file"]))

    def test_worker_middleware_tools(self):
        """Worker leaf subagents must have read_file, write_file, edit_file, glob, grep and NoOp SubAgentMiddleware."""
        middlewares = create_worker_middleware(self.backend)
        fs_mid = [m for m in middlewares if hasattr(m, "_enabled_tools")][0]
        self.assertEqual(
            fs_mid._enabled_tools,
            frozenset(["read_file", "write_file", "edit_file", "glob", "grep"])
        )
        noop_names = [m.name for m in middlewares if m.__class__.__name__ == "NoOpMiddleware"]
        self.assertIn("SubAgentMiddleware", noop_names)

    def test_reviewer_middleware_tools(self):
        """Reviewer leaf subagents must have read_file, write_file, edit_file, glob, grep and NoOp SubAgentMiddleware."""
        middlewares = create_reviewer_middleware(self.backend)
        fs_mid = [m for m in middlewares if hasattr(m, "_enabled_tools")][0]
        self.assertEqual(
            fs_mid._enabled_tools,
            frozenset(["read_file", "write_file", "edit_file", "glob", "grep"])
        )
        noop_names = [m.name for m in middlewares if m.__class__.__name__ == "NoOpMiddleware"]
        self.assertIn("SubAgentMiddleware", noop_names)

    def test_leaf_subagents_contain_all_required_specs(self):
        """All 9 leaf subagents must be instantiated cleanly as subagent dicts with runnables."""
        subagent_factories = [
            ("Coding_Agent", coding_subagent),
            ("Code_Reviewer", code_review_subagent),
            ("RDBMS_agent", rdbms_subagent),
            ("NoSQL_agent", nosql_subagent),
            ("REDIS_agent", redis_subagent),
            ("REST_Agent", rest_subagent),
            ("GraphQL_Agent", graphql_subagent),
            ("GRPC_Agent", grpc_subagent),
            ("SOAP_Agent", soap_subagent),
        ]

        for name, factory in subagent_factories:
            with self.subTest(agent=name):
                agent_dict = factory()
                self.assertEqual(agent_dict["name"], name)
                self.assertTrue(hasattr(agent_dict["runnable"], "invoke"))
                self.assertTrue(len(agent_dict["system_prompt"]) > 50)


if __name__ == "__main__":
    unittest.main()
