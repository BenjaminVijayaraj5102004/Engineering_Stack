"""EngineeringStack Public SDK Entry Point."""

from typing import Any, AsyncGenerator, Generator, Optional
import uuid

from .builders.main_builder import build_main_agent


class EngineeringStack:
    """Public Python SDK class encapsulating the multi-agent engineering stack.

    Example:
        >>> from engineeringstack import EngineeringStack
        >>> stack = EngineeringStack()
        >>> response = stack.invoke("Create a Flask REST API")
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
        self.model = model
        self.backend = backend
        if agent is not None:
            self.agent = agent
        else:
            self.agent = build_main_agent(model=model, backend=backend)

    def _normalize_input(self, input_data: Any) -> dict[str, Any]:
        """Normalize various input formats into graph state format."""
        if isinstance(input_data, str):
            messages = [{"role": "user", "content": input_data}]
        elif isinstance(input_data, dict) and "messages" in input_data:
            return input_data
        elif isinstance(input_data, list):
            messages = input_data
        else:
            messages = [{"role": "user", "content": str(input_data)}]
        return {"messages": messages}

    def invoke(
        self,
        input_data: Any,
        thread_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        """Invoke the agent workflow synchronously.

        Args:
            input_data: User query string, list of messages, or state dict.
            thread_id: Optional conversation thread ID for state persistence.
            **kwargs: Additional keyword arguments passed to the underlying graph invoke.

        Returns:
            The execution output from the agent workflow.
        """
        if thread_id is None:
            thread_id = str(uuid.uuid4())

        payload = self._normalize_input(input_data)
        config = kwargs.pop("config", {})
        configurable = config.get("configurable", {})
        configurable["thread_id"] = thread_id
        config["configurable"] = configurable

        return self.agent.invoke(payload, config=config, **kwargs)

    def stream(
        self,
        input_data: Any,
        thread_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Generator[Any, None, None]:
        """Stream response chunks from the agent workflow synchronously.

        Args:
            input_data: User query string, list of messages, or state dict.
            thread_id: Optional conversation thread ID.
            **kwargs: Additional keyword arguments passed to stream.

        Yields:
            Streamed response events or chunks.
        """
        if thread_id is None:
            thread_id = str(uuid.uuid4())

        payload = self._normalize_input(input_data)
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
        """Stream response chunks from the agent workflow asynchronously.

        Args:
            input_data: User query string, list of messages, or state dict.
            thread_id: Optional conversation thread ID.
            **kwargs: Additional keyword arguments passed to astream.

        Yields:
            Asynchronous streamed response events or chunks.
        """
        if thread_id is None:
            thread_id = str(uuid.uuid4())

        payload = self._normalize_input(input_data)
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
        """Batch execution over multiple inputs.

        Args:
            inputs: List of queries or state payloads.
            **kwargs: Additional keyword arguments passed to batch.

        Returns:
            List of responses.
        """
        payloads = [self._normalize_input(inp) for inp in inputs]
        return self.agent.batch(payloads, **kwargs)


def create_engineering_stack(
    model: Optional[Any] = None,
    backend: Optional[Any] = None,
    agent: Optional[Any] = None,
) -> EngineeringStack:
    """Factory function to create an EngineeringStack instance.

    Example:
        >>> from engineeringstack import create_engineering_stack
        >>> agent = create_engineering_stack()
        >>> response = agent.invoke("Create a Flask REST API")
    """
    return EngineeringStack(model=model, backend=backend, agent=agent)
