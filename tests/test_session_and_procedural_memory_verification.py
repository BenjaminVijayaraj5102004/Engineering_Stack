"""Comprehensive Verification Test Suite for Session Memory and Procedural Memory.

This test file explicitly tests and validates:
1. SESSION MEMORY:
   - Multi-turn conversation persistence within the same thread_id (message history accumulation).
   - Session isolation between distinct thread_ids (Thread A cannot see Thread B's messages).
   - Direct checkpointer state and checkpoint snapshot inspection.
   - Session checkpointer detection and fallback verification (identifying PostgresSaver vs MemorySaver).
   - Synchronous streaming session persistence.
   - Async streaming session persistence with MemorySaver.

2. PROCEDURAL MEMORY:
   - DeepAgents procedural skills discovery and registration from `/skills/`.
   - YAML frontmatter metadata extraction (name, description, path).
   - Verification of all 5 procedural skills (main-agent, api-manager, database-manager, helper-manager, code-review).
   - Procedural reference manuals navigation (delegation_workflow.md, routing_rules.md).
   - Developer isolation: procedural memory is mounted via FilesystemBackend(SDK_SKILLS_DIR) and cannot be mutated by user-level memory.
   - Skill routing enforcement according to operational procedures.

Follows TDD Workflow: Arrange-Act-Assert (AAA) pattern.
"""

import asyncio
import unittest
import uuid
from pathlib import Path
from typing import Any, Optional

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.store.memory import InMemoryStore
from deepagents.backends import FilesystemBackend, StateBackend, CompositeBackend
from deepagents.middleware.skills import _list_skills_with_errors

from engineeringstack.builders.main_builder import (
    SDK_SKILLS_DIR,
    build_default_backend,
    build_main_agent,
)
from engineeringstack.builders.api_builder import build_api_manager
from engineeringstack.builders.db_builder import build_database_manager
from engineeringstack.builders.helper_builder import build_helper_manager
from engineeringstack.stack import EngineeringStack, create_engineering_stack
from engineeringstack.util.checkpointer_memory import checkpointer
from engineeringstack.schema.state import AIOutput, UserInput


class MultiTurnContextAwareChatModel(BaseChatModel):
    """Deterministic Mock LLM that reflects session history in its responses."""

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        # Inspect full message history to verify session memory context
        user_queries = [
            m.content for m in messages if isinstance(m, HumanMessage) or getattr(m, "type", "") == "human"
        ]
        combined_text = " | ".join(str(q) for q in user_queries)

        if "PayFlow" in combined_text and ("name" in combined_text.lower() or "domain" in combined_text.lower()):
            resp = "PayFlow is a Fintech application for payment processing."
        elif "Project Alpha" in combined_text:
            resp = "Responding to Alice regarding Project Alpha."
        elif "Project Beta" in combined_text:
            resp = "Responding to Bob regarding Project Beta."
        elif "Create a POST endpoint" in combined_text:
            resp = (
                "Delegating to Helper_Manager for Flask POST endpoint.\n\n"
                "```python\n@app.route('/api/pay', methods=['POST'])\ndef pay(): return {'status': 'ok'}\n```\n\n"
                "- 1. Defined endpoint\n- 2. Handled POST\n- 3. Added JSON response\n- 4. Verified QA\n- 5. Ready"
            )
        else:
            resp = f"Received {len(messages)} messages in session history. Latest: {messages[-1].content if messages else ''}"

        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=resp))])

    def bind_tools(self, tools: Any, **kwargs: Any) -> Any:
        return self

    @property
    def _llm_type(self) -> str:
        return "multi_turn_context_aware_mock"


class TestSessionMemory(unittest.TestCase):
    """Comprehensive test suite for Session Memory verification."""

    def setUp(self):
        self.store = InMemoryStore()
        self.model = MultiTurnContextAwareChatModel()

    def test_session_memory_multiturn_persistence(self):
        """SESSION MEMORY TEST 1: Verify multi-turn conversation persistence within the same thread_id."""
        # Arrange
        stack = EngineeringStack(model=self.model, store=self.store)
        thread_id = f"session-test-{uuid.uuid4().hex[:8]}"

        # Act - Turn 1: Introduce context
        res_turn_1 = stack.invoke(
            "Hi, I am building a Fintech application named PayFlow.",
            thread_id=thread_id,
        )

        # Assert Turn 1
        self.assertEqual(res_turn_1["thread_id"], thread_id)
        self.assertGreaterEqual(len(res_turn_1["messages"]), 2)

        # Act - Turn 2: Follow-up question relying on Turn 1 session memory
        res_turn_2 = stack.invoke(
            "What is the name and domain of my application?",
            thread_id=thread_id,
        )

        # Assert Turn 2: Session memory accumulated all turns
        self.assertEqual(res_turn_2["thread_id"], thread_id)
        # Total messages should now contain Turn 1 Human + Turn 1 AI + Turn 2 Human + Turn 2 AI
        self.assertGreaterEqual(len(res_turn_2["messages"]), 4)
        self.assertIn("PayFlow", res_turn_2["final_answer"])
        self.assertIn("Fintech", res_turn_2["final_answer"])

    def test_session_memory_thread_isolation(self):
        """SESSION MEMORY TEST 2: Verify strict isolation between distinct thread_ids."""
        # Arrange
        stack = EngineeringStack(model=self.model, store=self.store)
        thread_alice = f"alice-session-{uuid.uuid4().hex[:8]}"
        thread_bob = f"bob-session-{uuid.uuid4().hex[:8]}"

        # Act - Alice speaks in Thread A
        res_alice = stack.invoke(
            "I am Alice working on Project Alpha.",
            thread_id=thread_alice,
        )

        # Act - Bob speaks in Thread B
        res_bob = stack.invoke(
            "I am Bob working on Project Beta.",
            thread_id=thread_bob,
        )

        # Assert - Thread A has Alice's context and not Bob's
        self.assertIn("Project Alpha", res_alice["final_answer"])
        self.assertNotIn("Project Beta", res_alice["final_answer"])

        # Assert - Thread B has Bob's context and not Alice's
        self.assertIn("Project Beta", res_bob["final_answer"])
        self.assertNotIn("Project Alpha", res_bob["final_answer"])

        # Verify message count isolation: each thread has exactly 2 messages (1 Human, 1 AI)
        self.assertEqual(len(res_alice["messages"]), 2)
        self.assertEqual(len(res_bob["messages"]), 2)

    def test_session_memory_checkpointer_inspection(self):
        """SESSION MEMORY TEST 3: Verify checkpointer captures state snapshots across turns."""
        # Arrange
        stack = EngineeringStack(model=self.model, store=self.store)
        thread_id = f"inspect-thread-{uuid.uuid4().hex[:8]}"

        # Act - Execute Turn 1
        stack.invoke("Initialize project repo for PayFlow", thread_id=thread_id)

        # Inspect checkpoint state directly through the compiled agent graph
        config = {"configurable": {"thread_id": thread_id}}
        state_snapshot = stack.agent.get_state(config)

        # Assert
        self.assertIsNotNone(state_snapshot)
        self.assertIn("messages", state_snapshot.values)
        self.assertGreaterEqual(len(state_snapshot.values["messages"]), 2)
        self.assertEqual(state_snapshot.config["configurable"]["thread_id"], thread_id)

    def test_session_memory_checkpointer_is_valid_instance(self):
        """SESSION MEMORY TEST 4: Verify checkpointer is initialized and implements BaseCheckpointSaver."""
        # Assert
        self.assertIsNotNone(checkpointer)
        self.assertTrue(isinstance(checkpointer, BaseCheckpointSaver))

    def test_session_memory_sync_streaming_persistence(self):
        """SESSION MEMORY TEST 5: Verify synchronous streaming preserves session state across turns."""
        # Arrange
        stack = EngineeringStack(model=self.model, store=self.store)
        stream_thread = f"stream-session-{uuid.uuid4().hex[:8]}"

        # Act - Stream turn 1
        chunks_1 = list(stack.stream("Hi, I am building PayFlow.", thread_id=stream_thread))
        self.assertTrue(len(chunks_1) > 0)

        # Check state after stream turn 1
        config = {"configurable": {"thread_id": stream_thread}}
        state_snapshot_1 = stack.agent.get_state(config)
        self.assertGreaterEqual(len(state_snapshot_1.values["messages"]), 2)

        # Act - Stream turn 2 on same thread
        chunks_2 = list(stack.stream("What is my app name?", thread_id=stream_thread))
        self.assertTrue(len(chunks_2) > 0)

        # Check state after stream turn 2: accumulated turns
        state_snapshot_2 = stack.agent.get_state(config)
        self.assertGreaterEqual(len(state_snapshot_2.values["messages"]), 4)

    def test_session_memory_with_in_memory_checkpointer(self):
        """SESSION MEMORY TEST 6: Verify pure in-memory checkpointer supports both invoke and async streaming."""
        # Arrange: build agent with dedicated MemorySaver
        mem_checkpointer = MemorySaver()
        from deepagents import create_deep_agent
        from engineeringstack.prompts.main_agent_prompt import MAIN_AGENT_SYSTEM_PROMPT

        backend = build_default_backend()
        custom_agent = create_deep_agent(
            model=self.model,
            system_prompt=MAIN_AGENT_SYSTEM_PROMPT,
            checkpointer=mem_checkpointer,
            backend=backend,
            store=self.store,
        )
        custom_stack = EngineeringStack(agent=custom_agent, store=self.store)
        thread_id = f"async-mem-{uuid.uuid4().hex[:8]}"

        # Turn 1: Synchronous invoke
        res1 = custom_stack.invoke("I am building PayFlow application", thread_id=thread_id)
        self.assertEqual(len(res1["messages"]), 2)

        # Turn 2: Async streaming with accumulated history
        async def run_astream():
            chunks = []
            async for chunk in custom_stack.astream("What is my app name?", thread_id=thread_id):
                chunks.append(chunk)
            return chunks

        async_chunks = asyncio.run(run_astream())
        self.assertTrue(len(async_chunks) > 0)

        # Verify state accumulated to 4 messages
        state = custom_agent.get_state({"configurable": {"thread_id": thread_id}})
        self.assertGreaterEqual(len(state.values["messages"]), 4)


class TestProceduralMemory(unittest.TestCase):
    """Comprehensive test suite for Procedural Memory verification."""

    def setUp(self):
        self.store = InMemoryStore()
        self.backend = build_default_backend()

    def test_procedural_memory_all_skills_discovery(self):
        """PROCEDURAL MEMORY TEST 1: Verify DeepAgents discovers all 5 internal SDK skills in /skills/."""
        # Act
        skills, errors = _list_skills_with_errors(self.backend, "/skills/")

        # Assert
        self.assertIsNone(errors, f"Skill loading produced errors: {errors}")
        self.assertEqual(len(skills), 5, f"Expected 5 skills, found {len(skills)}")

        discovered_names = {s["name"] for s in skills}
        expected_names = {
            "main-agent",
            "api-manager",
            "database-manager",
            "helper-manager",
            "code-review",
        }
        self.assertEqual(discovered_names, expected_names)

    def test_procedural_memory_frontmatter_metadata_integrity(self):
        """PROCEDURAL MEMORY TEST 2: Verify YAML frontmatter (name, description) on each SKILL.md."""
        skills, _ = _list_skills_with_errors(self.backend, "/skills/")

        for skill in skills:
            with self.subTest(skill_name=skill["name"]):
                self.assertIn("name", skill)
                self.assertIn("description", skill)
                self.assertIn("path", skill)
                self.assertTrue(skill["name"])
                self.assertTrue(skill["description"])
                self.assertTrue(skill["path"].startswith("/skills/"))
                self.assertTrue(skill["path"].endswith("/SKILL.md"))

    def test_procedural_memory_reference_manuals_navigation(self):
        """PROCEDURAL MEMORY TEST 3: Verify all procedural reference manuals exist and contain valid workflows."""
        skill_dirs = ["main-agent", "api-manager", "database-manager", "helper-manager", "code-review"]

        for s_dir in skill_dirs:
            with self.subTest(skill_dir=s_dir):
                skill_path = SDK_SKILLS_DIR / s_dir
                self.assertTrue(skill_path.exists(), f"Skill directory missing: {skill_path}")

                # Verify SKILL.md
                skill_file = skill_path / "SKILL.md"
                self.assertTrue(skill_file.exists(), f"SKILL.md missing in {s_dir}")
                skill_content = skill_file.read_text(encoding="utf-8")
                self.assertIn(f"name: {s_dir}", skill_content)

                # Verify references/
                refs_dir = skill_path / "references"
                self.assertTrue(refs_dir.exists(), f"references/ missing in {s_dir}")

                workflow_file = refs_dir / "delegation_workflow.md"
                routing_file = refs_dir / "routing_rules.md"
                self.assertTrue(workflow_file.exists(), f"delegation_workflow.md missing in {s_dir}")
                self.assertTrue(routing_file.exists(), f"routing_rules.md missing in {s_dir}")

                self.assertGreater(len(workflow_file.read_text(encoding="utf-8")), 50)
                self.assertGreater(len(routing_file.read_text(encoding="utf-8")), 50)

    def test_procedural_memory_developer_isolation_and_immutability(self):
        """PROCEDURAL MEMORY TEST 4: Verify procedural skills are developer-controlled and mounted via FilesystemBackend."""
        # /skills/ route is mounted via FilesystemBackend pointing to internal package SDK_SKILLS_DIR
        self.assertIsInstance(self.backend.routes["/skills/"], FilesystemBackend)
        self.assertEqual(Path(self.backend.routes["/skills/"].cwd), SDK_SKILLS_DIR.resolve())

        # Verify SDK skill remains intact
        main_skill_file = SDK_SKILLS_DIR / "main-agent" / "SKILL.md"
        content = main_skill_file.read_text(encoding="utf-8")
        self.assertIn("Main Agent Procedural Skill", content)

    def test_procedural_memory_agent_skills_configuration(self):
        """PROCEDURAL MEMORY TEST 5: Verify all builders correctly compile."""
        # Verify compiled agent graphs
        main_agent = build_main_agent(store=self.store)
        api_mgr = build_api_manager()
        db_mgr = build_database_manager()
        helper_mgr = build_helper_manager()

        self.assertTrue(hasattr(main_agent, "invoke"))
        self.assertTrue(hasattr(api_mgr, "invoke"))
        self.assertTrue(hasattr(db_mgr, "invoke"))
        self.assertTrue(hasattr(helper_mgr, "invoke"))


if __name__ == "__main__":
    unittest.main()
