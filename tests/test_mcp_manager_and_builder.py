import unittest
from pathlib import Path
from typing import Any, Optional
from unittest.mock import MagicMock, patch
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langgraph.graph.state import CompiledStateGraph

from engineeringstack.builders.mcp_builder import (
    build_mcp_manager,
    mcp_manager,
    mcp_subagent,
    graph,
)
from engineeringstack.agents.managers.mcpmanager import (
    mcp_manager_subagent,
)
from engineeringstack.prompts.mcp_prompt import (
    MCP_MANAGER_SYSTEM_PROMPT,
    MCP_SUBAGENT_SYSTEM_PROMPT,
)
from engineeringstack.builders.backend import SDK_SKILLS_DIR
from engineeringstack.stack import EngineeringStack


class MockMCPRoutingChatModel(BaseChatModel):
    """Deterministic Mock LLM for MCP routing and subagent provisioning verification."""

    def _generate(
        self,
        messages: Any,
        stop: Optional[Any] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        user_query = ""
        for msg in reversed(messages):
            content = getattr(msg, "content", str(msg))
            if content:
                user_query = str(content).lower()
                break

        if "mcp-postgres-server" in user_query or "postgres" in user_query:
            resp = (
                "Delegating to MCP_Manager -> Configured in-memory client for npx mcp-postgres-server. "
                "Exposing postgres query and schema inspection tools directly to RDBMS_agent (no disk JSON saved)."
            )
        elif "some-server.com" in user_query or "figma" in user_query:
            resp = (
                "Delegating to MCP_Manager -> Created dedicated Figma_Design_Agent subagent with MCP tools "
                "from https://some-server.com/mcp (in-memory config)."
            )
        else:
            resp = "Delegating to MCP_Manager for custom MCP server provisioning."

        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content=resp))]
        )

    def bind_tools(self, tools: Any, **kwargs: Any) -> Any:
        return self

    @property
    def _llm_type(self) -> str:
        return "mock_mcp_routing_chat_model"


class TestMCPManagerAndBuilder(unittest.TestCase):
    """Test suite for MCP Manager builder, skill file, prompts, subagent specs, and routing."""

    def test_mcp_skill_file_exists_and_contains_references(self):
        """Verify SKILL.md for mcp-manager exists and contains code references."""
        skill_file = SDK_SKILLS_DIR / "mcp-manager" / "SKILL.md"
        self.assertTrue(skill_file.exists(), f"Skill file not found at {skill_file}")
        content = skill_file.read_text(encoding="utf-8")

        # Verify YAML frontmatter
        self.assertIn("name: mcp-manager", content)
        self.assertIn("description:", content)

        # Verify code reference sections
        self.assertIn("mcpServers", content)
        self.assertIn("MultiServerMCPClient", content)
        self.assertIn("get_tools", content)
        self.assertIn("create_deep_agent", content)
        self.assertIn("dynamic_mcp_subagent", content)

    def test_mcp_prompts_defined(self):
        """Verify MCP prompt templates are non-empty and specify role constraints."""
        self.assertIn("MCP_Manager", MCP_MANAGER_SYSTEM_PROMPT)
        self.assertIn("/skills/mcp-manager/SKILL.md", MCP_MANAGER_SYSTEM_PROMPT)
        self.assertIn("Dedicated Custom MCP Tool Specialist", MCP_SUBAGENT_SYSTEM_PROMPT)

    def test_build_mcp_manager(self):
        """Verify build_mcp_manager constructs a valid CompiledStateGraph."""
        agent = build_mcp_manager()
        self.assertIsInstance(agent, CompiledStateGraph)
        self.assertTrue(hasattr(agent, "invoke"))

    def test_mcp_manager_subagent_spec(self):
        """Verify mcp_manager_subagent returns expected dictionary specification."""
        spec = mcp_manager_subagent()
        self.assertEqual(spec["name"], "MCP_Manager")
        self.assertIn("description", spec)
        self.assertEqual(spec["system_prompt"], MCP_MANAGER_SYSTEM_PROMPT)
        self.assertIsInstance(spec["runnable"], CompiledStateGraph)

    def test_mcp_graph_exports(self):
        """Verify exported graph variables match."""
        self.assertIsInstance(mcp_manager, CompiledStateGraph)
        self.assertIsInstance(mcp_subagent, CompiledStateGraph)
        self.assertIsInstance(graph, CompiledStateGraph)
        self.assertIs(mcp_manager, mcp_subagent)
        self.assertIs(mcp_manager, graph)

    def test_mcp_postgres_server_routing_and_tool_exposure(self):
        """Verify 'npx mcp-postgres-server' routes to MCP_Manager and exposes tools to RDBMS_agent."""
        model = MockMCPRoutingChatModel()
        stack = EngineeringStack(model=model)

        query = "Connect to custom MCP server using npx mcp-postgres-server and expose tools to respective agent"
        response = stack.invoke(query)

        final_answer = response.get("final_answer", "")
        self.assertIn("MCP_Manager", final_answer)
        self.assertIn("RDBMS_agent", final_answer)
        self.assertIn("npx mcp-postgres-server", final_answer)

    def test_mcp_new_domain_creates_dedicated_subagent(self):
        """Verify new domain URL 'https://some-server.com/mcp' creates dedicated subagent."""
        model = MockMCPRoutingChatModel()
        stack = EngineeringStack(model=model)

        query = "Connect to custom MCP server at https://some-server.com/mcp for figma design"
        response = stack.invoke(query)

        final_answer = response.get("final_answer", "")
        self.assertIn("MCP_Manager", final_answer)
        self.assertIn("Figma_Design_Agent", final_answer)


if __name__ == "__main__":
    unittest.main()
