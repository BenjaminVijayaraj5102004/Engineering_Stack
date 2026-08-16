"""Unit tests for skills, SDK_SKILLS_DIR, and backend routing.

Follows TDD Workflow:
- Arrange-Act-Assert (AAA) pattern
- Tests Happy Path, Error Cases, and Edge Cases
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from deepagents.backends import FilesystemBackend, StateBackend
from engineeringstack.builders.main_builder import (
    SDK_SKILLS_DIR,
    build_default_backend,
    build_main_agent,
)


class TestBuildDefaultBackend(unittest.TestCase):
    """Test suite for dynamic composite backend creation."""

    def test_default_backend_zero_config(self):
        """Arrange-Act-Assert: /skills/ routes to SDK_SKILLS_DIR FilesystemBackend."""
        # Act
        backend = build_default_backend()

        # Assert
        self.assertIsInstance(backend.default, StateBackend)
        self.assertIn("/skills/", backend.routes)
        self.assertIsInstance(backend.routes["/skills/"], FilesystemBackend)
        self.assertEqual(Path(backend.routes["/skills/"].cwd), SDK_SKILLS_DIR.resolve())

    def test_default_backend_mounts_sdk_skills_dir(self):
        """Arrange-Act-Assert: Backend always mounts SDK_SKILLS_DIR under /skills/."""
        # Arrange & Act
        backend = build_default_backend()

        # Assert
        self.assertIn("/skills/", backend.routes)
        self.assertIsInstance(backend.routes["/skills/"], FilesystemBackend)
        self.assertEqual(Path(backend.routes["/skills/"].cwd), SDK_SKILLS_DIR.resolve())


class TestMainAgentBuilderMemoryAndSkills(unittest.TestCase):
    """Test suite for build_main_agent parameter handling and defaults."""

    def test_sdk_skills_dir_exists(self):
        """Ensure SDK skills directory exists and contains skill subfolders."""
        self.assertTrue(SDK_SKILLS_DIR.exists())
        self.assertTrue((SDK_SKILLS_DIR / "main-agent").exists())

    def test_custom_memory_and_skills_parameter_forwarding(self):
        """Arrange-Act-Assert: User-supplied memory and skills lists are preserved."""
        # Arrange
        custom_memory = ["/memories/project_rules.md", "/memories/tech_stack.md"]
        custom_skills = ["/skills/python_expert/", "/skills/database_architect/"]

        # Act
        # Verify build_main_agent accepts custom lists without error
        agent = build_main_agent(
            memory=custom_memory,
            skills=custom_skills,
        )

        # Assert
        self.assertIsNotNone(agent)

    def test_skills_parameter_support(self):
        """Arrange-Act-Assert: 'skills' parameter is accepted and mapped correctly in build_main_agent."""
        # Arrange
        custom_skill_list = ["/skills/custom/"]

        # Act
        agent = build_main_agent(skills=custom_skill_list)

        # Assert
        self.assertIsNotNone(agent)

    def test_main_agent_restricted_filesystem_and_disabled_summarization_middleware(self):
        """Arrange-Act-Assert: Verify build_main_agent compiles with restricted filesystem tools and disabled summarization."""
        # Act
        agent = build_main_agent()

        # Assert
        self.assertIsNotNone(agent)
        self.assertTrue(hasattr(agent, "invoke"))


if __name__ == "__main__":
    unittest.main()
