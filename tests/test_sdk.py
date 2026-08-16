"""Unit tests for the EngineeringStack public Python SDK.

Follows TDD Workflow:
- Tests public exports and boundary isolation
- Tests synchronous invoke, streaming, async streaming, and batch execution using AAA pattern
"""

import asyncio
import unittest
import engineeringstack
from engineeringstack.schema.state import UserInput, AIOutput


class MockAgent:
    """Test double implementing LangGraph-like agent interface for fast unit tests."""

    def invoke(self, payload, config=None, **kwargs):
        thread_id = config.get("configurable", {}).get("thread_id", "default_thread")
        return {
            "messages": [
                {"role": "user", "content": payload["messages"][0]["content"]},
                {
                    "role": "assistant",
                    "content": (
                        "Generated implementation:\n\n"
                        "```python\ndef handler():\n    return {'status': 'ok'}\n```\n\n"
                        "- 1. Validated user requirements\n"
                        "- 2. Initialized database schema\n"
                        "- 3. Built REST router\n"
                        "- 4. Applied security middleware\n"
                        "- 5. Verified with unit tests\n"
                    ),
                },
            ]
        }

    def stream(self, payload, config=None, **kwargs):
        yield {"chunk": 1, "messages": [{"role": "assistant", "content": "chunk 1"}]}
        yield {"chunk": 2, "messages": [{"role": "assistant", "content": "chunk 2"}]}

    async def astream(self, payload, config=None, **kwargs):
        yield {"chunk": 1, "messages": [{"role": "assistant", "content": "async chunk 1"}]}
        yield {"chunk": 2, "messages": [{"role": "assistant", "content": "async chunk 2"}]}


class TestEngineeringStackSDK(unittest.TestCase):
    """Test suite for EngineeringStack SDK entrypoint."""

    def test_public_api_exports(self):
        """Ensure top level package exports strictly allowed symbols."""
        exported = set(engineeringstack.__all__)
        expected = {
            "EngineeringStack",
            "create_engineering_stack",
            "SDK_SKILLS_DIR",
            "UserInput",
            "MainAgentOutput",
            "AIOutput",
            "__version__",
            "enable_logging",
            "disable_logging",
            "get_logger",
        }
        self.assertEqual(exported, expected, f"Unexpected exports in __all__: {exported}")

    def test_private_modules_not_in_all(self):
        """Ensure internal modules are not exposed in __all__."""
        forbidden = [
            "builders",
            "agents",
            "prompts",
            "middleware",
            "backend",
            "services",
            "tools",
            "util",
            "models",
            "mcp",
            "internal",
        ]
        for module in forbidden:
            self.assertNotIn(module, engineeringstack.__all__, f"{module} leaked into __all__!")

    def test_sdk_instantiation_and_invoke_happy_path(self):
        """Arrange-Act-Assert: Invoke returns complete structured payload."""
        # Arrange
        mock_agent = MockAgent()
        stack = engineeringstack.EngineeringStack(agent=mock_agent)

        # Act
        result = stack.invoke("Build a payment API")

        # Assert
        self.assertIn("thread_id", result)
        self.assertIsInstance(result["user_input"], UserInput)
        self.assertEqual(result["user_input"].query, "Build a payment API")
        self.assertEqual(len(result["messages"]), 2)
        self.assertIn("def handler():", result["final_answer"])
        self.assertIsInstance(result["ai_output"], AIOutput)
        self.assertEqual(len(result["ai_output"].summary), 5)
        self.assertIn("def handler():", result["ai_output"].code)

    def test_factory_function_instantiation(self):
        """Arrange-Act-Assert: create_engineering_stack factory produces functional instance."""
        # Arrange
        mock_agent = MockAgent()
        stack = engineeringstack.create_engineering_stack(agent=mock_agent)

        # Act
        result = stack.invoke("Build user service")

        # Assert
        self.assertIsInstance(stack, engineeringstack.EngineeringStack)
        self.assertEqual(result["user_input"].query, "Build user service")

    def test_custom_thread_id_persistence(self):
        """Arrange-Act-Assert: Custom thread_id is respected and returned."""
        # Arrange
        custom_id = "test-thread-uuid-1234"
        stack = engineeringstack.EngineeringStack(agent=MockAgent())

        # Act
        result = stack.invoke("Test query", thread_id=custom_id)

        # Assert
        self.assertEqual(result["thread_id"], custom_id)

    def test_batch_execution_mock(self):
        """Arrange-Act-Assert: Batch processes list of inputs into list of results."""
        # Arrange
        stack = engineeringstack.EngineeringStack(agent=MockAgent())
        queries = ["Create Auth API", "Create Billing API"]

        # Act
        results = stack.batch(queries)

        # Assert
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["user_input"].query, "Create Auth API")
        self.assertEqual(results[1]["user_input"].query, "Create Billing API")

    def test_stream_generator(self):
        """Arrange-Act-Assert: Stream yields chunks from underlying agent."""
        # Arrange
        stack = engineeringstack.EngineeringStack(agent=MockAgent())

        # Act
        chunks = list(stack.stream("Stream test query"))

        # Assert
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0]["chunk"], 1)
        self.assertEqual(chunks[1]["chunk"], 2)

    def test_astream_async_generator(self):
        """Arrange-Act-Assert: astream yields chunks asynchronously."""
        # Arrange
        stack = engineeringstack.EngineeringStack(agent=MockAgent())

        # Act
        async def collect_chunks():
            results = []
            async for chunk in stack.astream("Async test query"):
                results.append(chunk)
            return results

        chunks = asyncio.run(collect_chunks())

        # Assert
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0]["messages"][0]["content"], "async chunk 1")

    def test_sdk_init_with_memory_and_developer_skills(self):
        """Arrange-Act-Assert: Memory, internal developer skills, skills_dir, and store are configured on instance."""
        # Arrange & Act
        stack = engineeringstack.EngineeringStack(
            agent=MockAgent(),
            memory=["/memories/custom.md"],
            store="dummy_store",
        )

        # Assert
        self.assertEqual(stack.memory, ["/memories/custom.md"])
        self.assertEqual(stack.skills, ["/skills/"])
        self.assertEqual(stack.skills_dir, engineeringstack.SDK_SKILLS_DIR)
        self.assertEqual(stack.store, "dummy_store")

    def test_factory_with_memory_and_store(self):
        """Arrange-Act-Assert: create_engineering_stack forwards memory and store configuration."""
        # Arrange & Act
        stack = engineeringstack.create_engineering_stack(
            agent=MockAgent(),
            memory=["/memories/custom.md"],
            store="custom_store",
        )

        # Assert
        self.assertEqual(stack.memory, ["/memories/custom.md"])
        self.assertEqual(stack.skills, ["/skills/"])
        self.assertEqual(stack.store, "custom_store")

    def test_sdk_invoke_exception_propagates(self):
        """Arrange-Act-Assert: Agent execution errors propagate with clear stacktrace."""
        # Arrange
        class FailingAgent:
            def invoke(self, *args, **kwargs):
                raise RuntimeError("Graph execution failed unexpectedly")

        stack = engineeringstack.EngineeringStack(agent=FailingAgent())

        # Act & Assert
        with self.assertRaises(RuntimeError) as ctx:
            stack.invoke("Trigger failure")
        self.assertIn("Graph execution failed unexpectedly", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

