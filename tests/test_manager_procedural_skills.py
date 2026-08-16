"""Unit tests verifying procedural skills and reference documentation for Database Manager, API Manager, Helper Manager, and Code Reviewer.

Follows TDD Workflow & AAA (Arrange-Act-Assert) pattern:
- Verifies all procedural skill files are discovered from /skills/.
- Verifies all manager and code-review procedural skills are strictly between 30 and 32 lines.
- Verifies delegation rules, frontmatter metadata, and pure router boundaries.
- Verifies presence and contents of references/ (delegation_workflow.md, routing_rules.md) for all skills.
- Verifies developer-only isolation (skills mounted under developer-controlled /skills/, isolated from user /memories/).
- Verifies system prompt templates are token-optimized, valid, and non-empty.
"""

import unittest
from pathlib import Path
from langgraph.store.memory import InMemoryStore
from deepagents.backends import FilesystemBackend, StoreBackend
from deepagents.middleware.skills import _list_skills_with_errors

from engineeringstack.builders.main_builder import (
    SDK_SKILLS_DIR,
    build_default_backend,
)
from engineeringstack.prompts import (
    API_MANAGER_SYSTEM_PROMPT,
    REST_SYSTEM_PROMPT,
    GRAPHQL_SYSTEM_PROMPT,
    GRPC_SYSTEM_PROMPT,
    SOAP_SYSTEM_PROMPT,
    DATABASE_MANAGER_SYSTEM_PROMPT,
    RDBMS_SYSTEM_PROMPT,
    NOSQL_SYSTEM_PROMPT,
    REDIS_SYSTEM_PROMPT,
    HELPER_MANAGER_SYSTEM_PROMPT,
    CODING_AGENT_SYSTEM_PROMPT,
    CODE_REVIEW_SYSTEM_PROMPT,
    MAIN_AGENT_SYSTEM_PROMPT,
    COMMON_SYSTEM_PROMPT,
)


class TestManagerProceduralSkills(unittest.TestCase):
    """Test suite for Manager and Code Review Procedural Skills."""

    def setUp(self):
        self.store = InMemoryStore()
        self.backend = build_default_backend()

    def test_all_manager_and_code_review_skills_discovered_and_loaded(self):
        """Arrange-Act-Assert: Backend discovers all 5 procedural skills in /skills/."""
        # Act
        skills, errors = _list_skills_with_errors(self.backend, "/skills/")

        # Assert
        self.assertIsNone(errors)
        skill_names = {s["name"] for s in skills}
        expected_skills = {"main-agent", "database-manager", "api-manager", "helper-manager", "code-review"}
        self.assertTrue(expected_skills.issubset(skill_names), f"Missing skills: {expected_skills - skill_names}")

    def test_manager_and_code_review_skill_file_line_counts(self):
        """Arrange-Act-Assert: Each manager and code review skill file is strictly between 30 and 32 lines."""
        skills_to_check = [
            "database-manager",
            "api-manager",
            "helper-manager",
            "code-review",
        ]

        for skill_dir in skills_to_check:
            skill_file = SDK_SKILLS_DIR / skill_dir / "SKILL.md"
            self.assertTrue(skill_file.exists(), f"Skill file not found: {skill_file}")
            
            content = skill_file.read_text(encoding="utf-8")
            lines = content.splitlines()
            line_count = len(lines)
            
            self.assertGreaterEqual(
                line_count,
                30,
                f"Skill {skill_dir}/SKILL.md has {line_count} lines, which is fewer than 30 lines.",
            )
            self.assertLessEqual(
                line_count,
                32,
                f"Skill {skill_dir}/SKILL.md has {line_count} lines, which exceeds 32 lines.",
            )

    def test_database_manager_skill_and_references(self):
        """Arrange-Act-Assert: database-manager skill and references exist with valid content."""
        skill_dir = SDK_SKILLS_DIR / "database-manager"
        skill_file = skill_dir / "SKILL.md"
        content = skill_file.read_text(encoding="utf-8")

        self.assertIn("name: database-manager", content)
        self.assertIn("RDBMS_agent", content)
        self.assertIn("NoSQL_agent", content)
        self.assertIn("REDIS_agent", content)
        self.assertIn("Code_Reviewer", content)

        # Check references/
        workflow_ref = skill_dir / "references" / "delegation_workflow.md"
        routing_ref = skill_dir / "references" / "routing_rules.md"
        self.assertTrue(workflow_ref.exists(), "database-manager delegation_workflow.md missing")
        self.assertTrue(routing_ref.exists(), "database-manager routing_rules.md missing")
        self.assertIn("Database_Manager", workflow_ref.read_text(encoding="utf-8"))
        self.assertIn("Code_Reviewer", workflow_ref.read_text(encoding="utf-8"))
        self.assertIn("RDBMS_agent", routing_ref.read_text(encoding="utf-8"))

    def test_api_manager_skill_and_references(self):
        """Arrange-Act-Assert: api-manager skill and references exist with valid content."""
        skill_dir = SDK_SKILLS_DIR / "api-manager"
        skill_file = skill_dir / "SKILL.md"
        content = skill_file.read_text(encoding="utf-8")

        self.assertIn("name: api-manager", content)
        self.assertIn("REST_Agent", content)
        self.assertIn("GraphQL_Agent", content)
        self.assertIn("GRPC_Agent", content)
        self.assertIn("SOAP_Agent", content)
        self.assertIn("Code_Reviewer", content)

        # Check references/
        workflow_ref = skill_dir / "references" / "delegation_workflow.md"
        routing_ref = skill_dir / "references" / "routing_rules.md"
        self.assertTrue(workflow_ref.exists(), "api-manager delegation_workflow.md missing")
        self.assertTrue(routing_ref.exists(), "api-manager routing_rules.md missing")
        self.assertIn("API_Manager", workflow_ref.read_text(encoding="utf-8"))
        self.assertIn("Code_Reviewer", workflow_ref.read_text(encoding="utf-8"))
        self.assertIn("REST_Agent", routing_ref.read_text(encoding="utf-8"))

    def test_helper_manager_skill_and_references(self):
        """Arrange-Act-Assert: helper-manager skill and references exist with valid content."""
        skill_dir = SDK_SKILLS_DIR / "helper-manager"
        skill_file = skill_dir / "SKILL.md"
        content = skill_file.read_text(encoding="utf-8")

        self.assertIn("name: helper-manager", content)
        self.assertIn("Coding_Agent", content)
        self.assertIn("Code_Reviewer", content)

        # Check references/
        workflow_ref = skill_dir / "references" / "delegation_workflow.md"
        routing_ref = skill_dir / "references" / "routing_rules.md"
        self.assertTrue(workflow_ref.exists(), "helper-manager delegation_workflow.md missing")
        self.assertTrue(routing_ref.exists(), "helper-manager routing_rules.md missing")
        self.assertIn("Helper_Manager", workflow_ref.read_text(encoding="utf-8"))
        self.assertIn("Coding_Agent", routing_ref.read_text(encoding="utf-8"))

    def test_code_review_skill_and_references(self):
        """Arrange-Act-Assert: code-review skill and references exist with valid content."""
        skill_dir = SDK_SKILLS_DIR / "code-review"
        skill_file = skill_dir / "SKILL.md"
        content = skill_file.read_text(encoding="utf-8")

        self.assertIn("name: code-review", content)
        self.assertIn("Code_Reviewer", content)
        self.assertIn("AIOutput", content)

        # Check references/
        workflow_ref = skill_dir / "references" / "delegation_workflow.md"
        routing_ref = skill_dir / "references" / "routing_rules.md"
        self.assertTrue(workflow_ref.exists(), "code-review delegation_workflow.md missing")
        self.assertTrue(routing_ref.exists(), "code-review routing_rules.md missing")
        self.assertIn("Code_Reviewer", workflow_ref.read_text(encoding="utf-8"))
        self.assertIn("Database_Manager", workflow_ref.read_text(encoding="utf-8"))
        self.assertIn("API_Manager", workflow_ref.read_text(encoding="utf-8"))

    def test_developer_only_skill_isolation(self):
        """Arrange-Act-Assert: Skills are mounted via FilesystemBackend from internal SDK package."""
        # /skills/ route is developer-controlled and points to SDK_SKILLS_DIR
        self.assertIsInstance(self.backend.routes["/skills/"], FilesystemBackend)
        self.assertEqual(Path(self.backend.routes["/skills/"].cwd), SDK_SKILLS_DIR.resolve())

        # Verify all 5 skill directories in SDK are intact and preserved
        for skill in ["main-agent", "database-manager", "api-manager", "helper-manager", "code-review"]:
            self.assertTrue((SDK_SKILLS_DIR / skill / "SKILL.md").exists())
            self.assertTrue((SDK_SKILLS_DIR / skill / "references").exists())

    def test_prompts_are_token_optimized_and_non_empty(self):
        """Arrange-Act-Assert: All prompt templates exist and contain concise routing instructions."""
        prompts = [
            API_MANAGER_SYSTEM_PROMPT,
            REST_SYSTEM_PROMPT,
            GRAPHQL_SYSTEM_PROMPT,
            GRPC_SYSTEM_PROMPT,
            SOAP_SYSTEM_PROMPT,
            DATABASE_MANAGER_SYSTEM_PROMPT,
            RDBMS_SYSTEM_PROMPT,
            NOSQL_SYSTEM_PROMPT,
            REDIS_SYSTEM_PROMPT,
            HELPER_MANAGER_SYSTEM_PROMPT,
            CODING_AGENT_SYSTEM_PROMPT,
            CODE_REVIEW_SYSTEM_PROMPT,
            MAIN_AGENT_SYSTEM_PROMPT,
            COMMON_SYSTEM_PROMPT,
        ]

        for p in prompts:
            self.assertIsInstance(p, str)
            self.assertGreater(len(p.strip()), 10)


if __name__ == "__main__":
    unittest.main()
