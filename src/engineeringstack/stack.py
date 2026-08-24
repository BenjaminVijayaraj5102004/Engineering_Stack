from pathlib import Path
import re
from typing import Any, Optional
import uuid
from .models.ai_model import build_chat_model
from .builders.backend import SDK_SKILLS_DIR
from .builders.main_builder import build_main_agent
from .builders.store import build_default_store
from .schema.state import UserInput, AIOutput
from langchain_core.messages import AIMessage, HumanMessage


class EngineeringStack:
    """Public Python SDK class encapsulating the multi-agent engineering stack.

    Example:
        >>> from engineeringstack import EngineeringStack, UserInput
        >>> stack = EngineeringStack()
        >>> response = stack.invoke("Create a Flask REST API")
        >>> print(response["ai_output"].summary)
    """

    skills_dir: Path = SDK_SKILLS_DIR

    def __init__(
        self,
        model: Optional[Any] = None,
        backend: Optional[Any] = None,
        agent: Optional[Any] = None,
        memory: Optional[list[str]] = None,
        tools: Optional[list[Any]] = None,
        store: Optional[Any] = None,
        middleware: Optional[list[Any]] = None,
        verbose: bool = False,
        enable_logging: bool = False,
    ):
        """Initialize the EngineeringStack instance.

        Args:
            model: Optional custom LLM model instance or model name string.
            backend: Optional backend provider/configuration override.
            agent: Optional pre-built agent graph override.
            memory: Optional list of virtual memory paths.
            tools: Optional list of custom tools.
            store: Optional LangGraph BaseStore instance (e.g. InMemoryStore or PostgresStore).
            middleware: Optional list of custom middlewares.
            verbose: If True, enables console debug logging.
            enable_logging: Alias for verbose.
        """
        if verbose or enable_logging:
            from .util.logger import enable_logging as _enable_logging
            _enable_logging(to_console=True)

        self.model = build_chat_model(model=model)
        self.backend = backend
        self.memory = memory
        self.skills = ["/skills/"]
        self.tools = tools
        self.skills_dir = SDK_SKILLS_DIR
        self.store = store if store is not None else build_default_store()
        self.middleware = middleware

        if agent is not None:
            self.agent = agent
        else:
            self.agent = build_main_agent(
                model=self.model,
                backend=self.backend,
                memory=self.memory,
                skills=self.skills,
                tools=self.tools,
                store=self.store,
                middleware=self.middleware,
            )

    def _normalize_input(self, input_data: Any) -> tuple[UserInput, dict[str, Any]]:
        """Normalize input data into a UserInput schema and a graph state dict using schema methods."""
        user_input = UserInput.from_input(input_data)
        if isinstance(input_data, dict) and "messages" in input_data and input_data["messages"]:
            formatted_msgs = []
            for msg in input_data["messages"]:
                if isinstance(msg, dict):
                    formatted_msgs.append({"role": msg.get("role", "user"), "content": str(msg.get("content", str(msg)))})
                else:
                    role = "user" if isinstance(msg, HumanMessage) else "assistant"
                    formatted_msgs.append({"role": role, "content": str(getattr(msg, "content", str(msg)))})
            return user_input, {"messages": formatted_msgs}
        return user_input, user_input.to_payload()

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
        """Parse execution output messages into structured AIOutput schema format."""
        return AIOutput.from_messages(messages)

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
    ) -> Any:
        """Developer/Debug method: Stream state chunks from the agent workflow."""
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
    ) -> Any:
        """Developer/Debug method: Stream state chunks asynchronously from the agent workflow."""
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
    tools: Optional[list[Any]] = None,
    store: Optional[Any] = None,
    middleware: Optional[list[Any]] = None,
    verbose: bool = False,
    enable_logging: bool = False,
) -> EngineeringStack:
    """Factory function to create an EngineeringStack instance."""
    return EngineeringStack(
        model=model,
        backend=backend,
        agent=agent,
        memory=memory,
        tools=tools,
        store=store,
        middleware=middleware,
        verbose=verbose,
        enable_logging=enable_logging,
    )



