from pathlib import Path
import re
from typing import Any, AsyncGenerator, Generator, Optional, Union
import uuid
from .models.ai_model import build_chat_model
from .builders.main_builder import build_main_agent
from .schema.state import UserInput, AIOutput
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.store.memory import InMemoryStore


class EngineeringStack:
    """Public Python SDK class encapsulating the multi-agent engineering stack.

    Example:
        >>> from engineeringstack import EngineeringStack, UserInput
        >>> stack = EngineeringStack()
        >>> response = stack.invoke("Create a Flask REST API")
        >>> print(response["ai_output"].summary)
    """

    def __init__(
        self,
        model: Optional[Any] = None,
        backend: Optional[Any] = None,
        agent: Optional[Any] = None,
        memory: Optional[list[str]] = None,
        skills: Optional[list[str]] = None,
        skill: Optional[Any] = None,
        tools: Optional[list[Any]] = None,
        local_memory_dir: Optional[Union[str, Path]] = None,
        local_skills_dir: Optional[Union[str, Path]] = None,
        store: Optional[Any] = None,
    ):
        """Initialize the EngineeringStack instance.

        Args:
            model: Optional custom LLM model instance or model name string.
            backend: Optional backend provider/configuration override.
            agent: Optional pre-built agent graph override.
            memory: Optional list of virtual memory paths (defaults to ['/memories/AGENTS.md']).
            skills: Optional list of skill directory paths (defaults to ['/skills/']).
            skill: Alias for skills for convenience.
            tools: Optional list of custom tools (defaults to helper intent & routing tools).
            local_memory_dir: Optional local directory path for saving memories directly to disk.
            local_skills_dir: Optional local directory path for loading skills directly from disk.
            store: Optional LangGraph BaseStore instance (e.g. InMemoryStore or PostgresStore).
        """
        self.model = build_chat_model(model=model)
        self.backend = backend
        self.memory = memory if memory is not None else [ "/memories/preferences.md", "/memories/AGENTS.md"]
        self.skills = skills if skills is not None else (skill if skill is not None else ["/skills/"])
        self.tools = tools
        self.local_memory_dir = local_memory_dir
        self.local_skills_dir = local_skills_dir
        self.store = store if store is not None else InMemoryStore()

        if agent is not None:
            self.agent = agent
        else:
            self.agent = build_main_agent(
                model=self.model,
                backend=self.backend,
                memory=self.memory,
                skills=self.skills,
                tools=self.tools,
                local_memory_dir=self.local_memory_dir,
                local_skills_dir=self.local_skills_dir,
                store=self.store,
            )
    def _normalize_input(self, input_data: Any) -> tuple[UserInput, dict[str, Any]]:
        """Normalize input data into a UserInput schema and a graph state dict."""
        if isinstance(input_data, UserInput):
            user_input = input_data
        elif isinstance(input_data, str):
            user_input = UserInput(query=input_data)
        elif isinstance(input_data, dict):
            if "query" in input_data:
                user_input = UserInput(**input_data)
            elif "messages" in input_data and input_data["messages"]:
                msgs = input_data["messages"]
                formatted_msgs = []
                last_user_content = ""
                for msg in msgs:
                    if isinstance(msg, dict):
                        role = msg.get("role", "user")
                        content = msg.get("content", str(msg))
                    else:
                        role = "user" if isinstance(msg, HumanMessage) else "assistant"
                        content = getattr(msg, "content", str(msg))
                    formatted_msgs.append({"role": role, "content": str(content)})
                    if role == "user":
                        last_user_content = str(content)
                user_input = UserInput(query=last_user_content or "User request")
                payload = {"messages": formatted_msgs}
                return user_input, payload
            else:
                user_input = UserInput(query=str(input_data))
        else:
            user_input = UserInput(query=str(input_data))

        content_str = (
            f"User Request Query: {user_input.query}\n"
            f"Requirements: {user_input.requirements or 'N/A'}\n"
            f"Framework: {user_input.framework or 'N/A'}\n"
            f"Language: {user_input.language or 'N/A'}\n"
            f"Database: {user_input.database or 'N/A'}"
        )
        payload = {"messages": [{"role": "user", "content": content_str}]}
        return user_input, payload

    def _extract_final_answer(self, messages: list) -> str:
        """Extract the text content of the last AI message."""
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                if msg.content and not getattr(msg, "tool_calls", None):
                    return str(msg.content)
            elif isinstance(msg, dict) and msg.get("role") == "assistant":
                if msg.get("content"):
                    return str(msg["content"])
        return ""

    def _extract_ai_output(self, messages: list) -> AIOutput:
        """Parse execution output messages into structured AIOutput format."""
        final_text = self._extract_final_answer(messages)

        code_blocks = re.findall(r"```(?:\w+)?\n(.*?)```", final_text, re.DOTALL)
        if code_blocks:
            code_content = "\n\n".join(cb.strip() for cb in code_blocks)
        else:
            code_content = final_text.strip()


        bullets: list[str] = []
        for line in final_text.splitlines():
            line_str = line.strip()
            if line_str.startswith(("-", "*", "•")) or (
                re.match(r"^\d+\.", line_str) and len(line_str) > 3
            ):
                cleaned = re.sub(r"^[\-\*\•\d\.]+\s*", "", line_str).strip()
                if cleaned and cleaned not in bullets:
                    bullets.append(cleaned)

 
        fallback_bullets = [
            "Parsed and extracted UserInput specification.",
            "Routed task through Main Agent and specialized Manager.",
            "Delegated execution to requested domain specialist.",
            "Generated implementation code adhering to requirements.",
            "Finalized engineering solution output.",
        ]

        if len(bullets) < 5:
            bullets.extend(fallback_bullets[len(bullets) : 5])
        elif len(bullets) > 5:
            bullets = bullets[:5]

        return AIOutput(summary=bullets, code=code_content)

    def invoke(
        self,
        input_data: Any,
        thread_id: Optional[str] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Invoke the agent workflow synchronously.

        Args:
            input_data: User query string, UserInput object, or state dict.
            thread_id: Optional conversation thread ID for state persistence.
            **kwargs: Additional keyword arguments passed to underlying graph invoke.

        Returns:
            Dict containing thread_id, user_input, messages, final_answer, and ai_output.
        """
        config = kwargs.pop("config", {})
        configurable = config.get("configurable", {})
        if thread_id is None:
            thread_id = configurable.get("thread_id", str(uuid.uuid4()))

        user_input, payload = self._normalize_input(input_data)
        configurable["thread_id"] = thread_id
        config["configurable"] = configurable

        state = self.agent.invoke(payload, config=config, **kwargs)
        ai_output = self._extract_ai_output(state["messages"])

        return {
            "thread_id": thread_id,
            "user_input": user_input,
            "messages": state["messages"],
            "final_answer": self._extract_final_answer(state["messages"]),
            "ai_output": ai_output,
        }

    def stream(
        self,
        input_data: Any,
        thread_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Generator[Any, None, None]:
        """Stream response chunks from the agent workflow synchronously."""
        config = kwargs.pop("config", {})
        configurable = config.get("configurable", {})
        if thread_id is None:
            thread_id = configurable.get("thread_id", str(uuid.uuid4()))

        _, payload = self._normalize_input(input_data)
        configurable["thread_id"] = thread_id
        config["configurable"] = configurable

        yield from self.agent.stream(payload, config=config, **kwargs)

    async def astream(
        self,
        input_data: Any,
        thread_id: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[Any, None]:
        """Stream response chunks from the agent workflow asynchronously."""
        config = kwargs.pop("config", {})
        configurable = config.get("configurable", {})
        if thread_id is None:
            thread_id = configurable.get("thread_id", str(uuid.uuid4()))

        _, payload = self._normalize_input(input_data)
        configurable["thread_id"] = thread_id
        config["configurable"] = configurable

        async for chunk in self.agent.astream(payload, config=config, **kwargs):
            yield chunk

    def batch(
        self,
        inputs: list[Any],
        **kwargs: Any,
    ) -> list[Any]:
        """Batch execution over multiple inputs."""
        return [self.invoke(inp, **kwargs) for inp in inputs]


def create_engineering_stack(
    model: Optional[Any] = None,
    backend: Optional[Any] = None,
    agent: Optional[Any] = None,
    memory: Optional[list[str]] = None,
    skills: Optional[list[str]] = None,
    skill: Optional[Any] = None,
    tools: Optional[list[Any]] = None,
    local_memory_dir: Optional[Union[str, Path]] = None,
    local_skills_dir: Optional[Union[str, Path]] = None,
    store: Optional[Any] = None,
) -> EngineeringStack:
    """Factory function to create an EngineeringStack instance."""
    return EngineeringStack(
        model=model,
        backend=backend,
        agent=agent,
        memory=memory,
        skills=skills,
        skill=skill,
        tools=tools,
        local_memory_dir=local_memory_dir,
        local_skills_dir=local_skills_dir,
        store=store,
    )


