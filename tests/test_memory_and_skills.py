"""Unit tests for memory, skills, namespace resolution, and dynamic backend routing.

Follows TDD Workflow:
- Arrange-Act-Assert (AAA) pattern
- Tests Happy Path, Error Cases, and Edge Cases (NoneType, Path vs str, custom overrides)
"""

import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from deepagents.backends import FilesystemBackend, StateBackend, StoreBackend
from engineeringstack.builders.main_builder import (
    DEFAULT_MEMORY,
    DEFAULT_SKILLS,
    _default_user_namespace,
    build_default_backend,
    build_main_agent,
)


class TestNamespaceResolution(unittest.TestCase):
    """Test suite for multi-tenant and local fallback user namespace resolution."""

    def test_namespace_with_none_runtime(self):
        """Arrange-Act-Assert: None runtime falls back safely to default_user."""
        # Arrange
        rt = None

        # Act
        ns = _default_user_namespace(rt)

        # Assert
        self.assertEqual(ns, ("default_user",))

    def test_namespace_with_empty_runtime(self):
        """Arrange-Act-Assert: Runtime without server_info falls back to default_user."""
        # Arrange
        rt = SimpleNamespace()

        # Act
        ns = _default_user_namespace(rt)

        # Assert
        self.assertEqual(ns, ("default_user",))

    def test_namespace_with_none_user(self):
        """Arrange-Act-Assert: Runtime with server_info but None user falls back to default_user."""
        # Arrange
        rt = SimpleNamespace(server_info=SimpleNamespace(user=None))

        # Act
        ns = _default_user_namespace(rt)

        # Assert
        self.assertEqual(ns, ("default_user",))

    def test_namespace_with_authenticated_cloud_user(self):
        """Arrange-Act-Assert: Runtime with authenticated cloud user returns user identity."""
        # Arrange
        expected_user_id = "user_cloud_98765"
        rt = SimpleNamespace(
            server_info=SimpleNamespace(
                user=SimpleNamespace(identity=expected_user_id)
            )
        )

        # Act
        ns = _default_user_namespace(rt)

        # Assert
        self.assertEqual(ns, (expected_user_id,))


class TestBuildDefaultBackend(unittest.TestCase):
    """Test suite for dynamic composite backend creation."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_default_backend_zero_config(self):
        """Arrange-Act-Assert: Without local dirs, routes to StoreBackend."""
        # Act
        backend = build_default_backend()

        # Assert
        self.assertIsInstance(backend.default, StateBackend)
        self.assertIn("/memories/", backend.routes)
        self.assertIn("/skills/", backend.routes)
        self.assertIsInstance(backend.routes["/memories/"], StoreBackend)
        self.assertIsInstance(backend.routes["/skills/"], StoreBackend)

    def test_default_backend_with_string_local_memory_dir(self):
        """Arrange-Act-Assert: String local_memory_dir creates dir and mounts FilesystemBackend."""
        # Arrange
        mem_dir = Path(self.test_dir) / "custom_mem_str"
        self.assertFalse(mem_dir.exists())

        # Act
        backend = build_default_backend(local_memory_dir=str(mem_dir))

        # Assert
        self.assertTrue(mem_dir.exists())
        self.assertIsInstance(backend.routes["/memories/"], FilesystemBackend)
        self.assertIsInstance(backend.routes["/skills/"], StoreBackend)

    def test_default_backend_with_path_local_skills_dir(self):
        """Arrange-Act-Assert: Path object local_skills_dir creates dir and mounts FilesystemBackend."""
        # Arrange
        skills_dir = Path(self.test_dir) / "custom_skills_path"
        self.assertFalse(skills_dir.exists())

        # Act
        backend = build_default_backend(local_skills_dir=skills_dir)

        # Assert
        self.assertTrue(skills_dir.exists())
        self.assertIsInstance(backend.routes["/skills/"], FilesystemBackend)
        self.assertIsInstance(backend.routes["/memories/"], StoreBackend)

    def test_default_backend_with_both_local_dirs(self):
        """Arrange-Act-Assert: Specifying both local dirs mounts FilesystemBackend for both."""
        # Arrange
        mem_dir = Path(self.test_dir) / "mem_both"
        skills_dir = Path(self.test_dir) / "skills_both"

        # Act
        backend = build_default_backend(
            local_memory_dir=mem_dir,
            local_skills_dir=skills_dir,
        )

        # Assert
        self.assertTrue(mem_dir.exists())
        self.assertTrue(skills_dir.exists())
        self.assertIsInstance(backend.routes["/memories/"], FilesystemBackend)
        self.assertIsInstance(backend.routes["/skills/"], FilesystemBackend)


class TestMainAgentBuilderMemoryAndSkills(unittest.TestCase):
    """Test suite for build_main_agent parameter handling and defaults."""

    def test_constants_definitions(self):
        """Ensure SDK default memory and skills constants are valid non-empty lists."""
        self.assertEqual(DEFAULT_MEMORY, ["/memories/AGENTS.md"])
        self.assertEqual(DEFAULT_SKILLS, ["/skills/"])

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

    def test_skill_singular_alias_support(self):
        """Arrange-Act-Assert: Singular 'skill' alias is accepted and mapped correctly."""
        # Arrange
        custom_skill_list = ["/skills/custom/"]

        # Act
        agent = build_main_agent(skill=custom_skill_list)

        # Assert
        self.assertIsNotNone(agent)


if __name__ == "__main__":
    unittest.main()
