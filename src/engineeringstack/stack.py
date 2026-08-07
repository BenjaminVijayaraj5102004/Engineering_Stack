import re
from typing import Any, AsyncGenerator, Generator, Optional, Union
import uuid
from .models.ai_model import build_chat_model
from .builders.main_builder import build_main_agent
from .schema.state import UserInput, AIOutput
from langchain_core.messages import AIMessage


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
    ):
        """Initialize the EngineeringStack instance.

        Args:
            model: Optional custom LLM model instance.
            backend: Optional backend provider/configuration.
            agent: Optional pre-built agent graph override.
        """
        self.model = build_chat_model(model=model)
        self.backend = backend
        if agent is not None:
            self.agent = agent
        else:
            self.agent = build_main_agent(model=self.model, backend=self.backend)

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
                first_msg = input_data["messages"][0]
                if isinstance(first_msg, dict):
                    content = first_msg.get("content", str(first_msg))
                else:
                    content = getattr(first_msg, "content", str(first_msg))
                user_input = UserInput(query=str(content))
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

        # Extract code block(s) if present
        code_blocks = re.findall(r"```(?:\w+)?\n(.*?)```", final_text, re.DOTALL)
        if code_blocks:
            code_content = "\n\n".join(cb.strip() for cb in code_blocks)
        else:
            code_content = final_text.strip()

        # Extract summary bullet points
        bullets: list[str] = []
        for line in final_text.splitlines():
            line_str = line.strip()
            if line_str.startswith(("-", "*", "•")) or (
                re.match(r"^\d+\.", line_str) and len(line_str) > 3
            ):
                cleaned = re.sub(r"^[\-\*\•\d\.]+\s*", "", line_str).strip()
                if cleaned and cleaned not in bullets:
                    bullets.append(cleaned)

        # Ensure exactly 5 concise summary bullet points
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
        if thread_id is None:
            thread_id = str(uuid.uuid4())

        user_input, payload = self._normalize_input(input_data)
        config = kwargs.pop("config", {})
        configurable = config.get("configurable", {})
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
        if thread_id is None:
            thread_id = str(uuid.uuid4())

        _, payload = self._normalize_input(input_data)
        config = kwargs.pop("config", {})
        configurable = config.get("configurable", {})
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
        if thread_id is None:
            thread_id = str(uuid.uuid4())

        _, payload = self._normalize_input(input_data)
        config = kwargs.pop("config", {})
        configurable = config.get("configurable", {})
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
) -> EngineeringStack:
    """Factory function to create an EngineeringStack instance."""
    return EngineeringStack(model=model, backend=backend, agent=agent)

