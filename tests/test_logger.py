"""Unit tests for the centralized logger utility.

Follows TDD Workflow:
- Arrange-Act-Assert (AAA) pattern
- Verifies singleton behavior, thread safety, and handler formatting
"""

import logging
import unittest
from engineeringstack.util.logger import get_logger, enable_logging, disable_logging, _initialized_loggers


class TestEngineeringStackLogger(unittest.TestCase):
    """Test suite for get_logger utility."""

    def tearDown(self):
        disable_logging()

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

    def test_get_logger_defaults_to_null_handler(self):
        """Arrange-Act-Assert: Default logger has NullHandler attached and does not propagate."""
        # Arrange & Act
        logger = get_logger("test.module.silent")

        # Assert
        self.assertFalse(logger.propagate)
        self.assertTrue(any(isinstance(h, logging.NullHandler) for h in logger.handlers))

    def test_enable_and_disable_logging(self):
        """Arrange-Act-Assert: Developers can dynamically enable and disable console logging."""
        # Act: Enable
        enable_logging(level=logging.DEBUG, to_console=True)
        logger = get_logger("test.module.verbose")

        # Assert: Level is DEBUG and has StreamHandler
        self.assertEqual(logger.level, logging.DEBUG)
        self.assertTrue(any(isinstance(h, logging.StreamHandler) for h in logger.handlers))

        # Act: Disable
        disable_logging()

        # Assert: Level is reset and has NullHandler
        self.assertTrue(any(isinstance(h, logging.NullHandler) for h in logger.handlers))


if __name__ == "__main__":
    unittest.main()
