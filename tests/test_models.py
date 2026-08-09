"""Unit tests for the model factory and wrapper.

Follows TDD Workflow:
- Arrange-Act-Assert (AAA) pattern
- Verifies model caching, passthrough, and initialization
"""

import unittest
from unittest.mock import MagicMock, patch
from langchain_core.language_models.chat_models import BaseChatModel
from engineeringstack.models.ai_model import build_chat_model, DEFAULT_MODEL_NAME


class TestModelFactory(unittest.TestCase):
    """Test suite for build_chat_model factory function."""

    def test_build_chat_model_passthrough_if_already_instance(self):
        """Arrange-Act-Assert: Pre-instantiated BaseChatModel is returned directly without re-init."""
        # Arrange
        mock_model = MagicMock(spec=BaseChatModel)

        # Act
        result = build_chat_model(model=mock_model)

        # Assert
        self.assertIs(result, mock_model)

    @patch("engineeringstack.models.ai_model.init_chat_model")
    def test_build_chat_model_default_name(self, mock_init):
        """Arrange-Act-Assert: If model is None, uses DEFAULT_MODEL_NAME."""
        # Arrange
        mock_init.return_value = MagicMock(spec=BaseChatModel)

        # Act
        result = build_chat_model(model=None)

        # Assert
        mock_init.assert_called_once_with(model=DEFAULT_MODEL_NAME)
        self.assertIsNotNone(result)

    @patch("engineeringstack.models.ai_model.init_chat_model")
    def test_build_chat_model_custom_string(self, mock_init):
        """Arrange-Act-Assert: Custom model string and kwargs passed to init_chat_model."""
        # Arrange
        mock_init.return_value = MagicMock(spec=BaseChatModel)
        custom_model = "openai:gpt-4o"

        # Act
        result = build_chat_model(model=custom_model, temperature=0.7)

        # Assert
        mock_init.assert_called_once_with(model=custom_model, temperature=0.7)
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
