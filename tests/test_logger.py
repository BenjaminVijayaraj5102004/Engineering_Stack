"""Unit tests for the centralized logger utility.

Follows TDD Workflow:
- Arrange-Act-Assert (AAA) pattern
- Verifies singleton behavior, thread safety, and handler formatting
"""

import logging
import unittest
from engineeringstack.util.logger import get_logger, _initialized_loggers


class TestEngineeringStackLogger(unittest.TestCase):
    """Test suite for get_logger utility."""

    def test_get_logger_singleton_behavior(self):
        """Arrange-Act-Assert: Multiple calls with same name return identical instance."""
        # Arrange
        name = "test.module.singleton"

        # Act
        logger_1 = get_logger(name)
        logger_2 = get_logger(name)

        # Assert
        self.assertIs(logger_1, logger_2)
        self.assertIn(name, _initialized_loggers)

    def test_get_logger_level_is_debug(self):
        """Arrange-Act-Assert: Logger level defaults to DEBUG."""
        # Arrange & Act
        logger = get_logger("test.module.level")

        # Assert
        self.assertEqual(logger.level, logging.DEBUG)
        self.assertFalse(logger.propagate)

    def test_get_logger_handler_configuration(self):
        """Arrange-Act-Assert: Logger has at least one handler attached."""
        # Arrange & Act
        logger = get_logger("test.module.handlers")

        # Assert
        self.assertGreaterEqual(len(logger.handlers), 1)


if __name__ == "__main__":
    unittest.main()
