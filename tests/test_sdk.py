import unittest
import engineeringstack


class TestEngineeringStackSDK(unittest.TestCase):

    def test_public_api_exports(self):
        """Ensure top level package exports strictly allowed symbols."""
        exported = set(engineeringstack.__all__)
        expected = {"EngineeringStack", "create_engineering_stack", "__version__"}
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

    def test_sdk_instantiation_mock(self):
        """Test SDK class and factory instantiation without triggering real LLM network calls."""
        class DummyAgent:
            def invoke(self, payload, config=None, **kwargs):
                return {"messages": [{"role": "assistant", "content": "mock response"}]}

            def stream(self, payload, config=None, **kwargs):
                yield {"messages": [{"role": "assistant", "content": "mock chunk"}]}

            async def astream(self, payload, config=None, **kwargs):
                yield {"messages": [{"role": "assistant", "content": "mock chunk"}]}

            def batch(self, payloads, **kwargs):
                return [{"messages": [{"role": "assistant", "content": "mock batch"}]} for _ in payloads]

        dummy_agent = DummyAgent()

        # Class-based usage
        stack = engineeringstack.EngineeringStack(agent=dummy_agent)
        res = stack.invoke("Hello test")
        self.assertEqual(res["messages"][-1]["content"], "mock response")

        # Factory function usage
        stack_factory = engineeringstack.create_engineering_stack(agent=dummy_agent)
        res_factory = stack_factory.invoke("Hello factory test")
        self.assertEqual(res_factory["messages"][-1]["content"], "mock response")

    def test_batch_execution_mock(self):
        """Test batch invocation."""
        class DummyAgent:
            def batch(self, payloads, **kwargs):
                return [{"messages": [{"role": "assistant", "content": f"res_{i}"}]} for i, _ in enumerate(payloads)]

        stack = engineeringstack.EngineeringStack(agent=DummyAgent())
        results = stack.batch(["q1", "q2"])
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["messages"][-1]["content"], "res_0")
        self.assertEqual(results[1]["messages"][-1]["content"], "res_1")


if __name__ == "__main__":
    unittest.main()
