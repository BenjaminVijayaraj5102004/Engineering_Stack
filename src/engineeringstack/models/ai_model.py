from typing import Optional, Union
from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel

DEFAULT_MODEL_NAME = "ollama:qwen3-coder:30b"


def build_chat_model(
    model: Optional[Union[str, BaseChatModel]] = None,
    temperature: Optional[float] = None,
    **kwargs,
) -> BaseChatModel:
    """
    Build a LangChain chat model.

    Args:
        model: Optional model string (e.g. "ollama:qwen3-coder:30b", "openai:gpt-4o"),
               or a pre-configured BaseChatModel instance. If None, uses DEFAULT_MODEL_NAME.
        temperature: Optional sampling temperature.
        **kwargs: Additional parameters passed to init_chat_model.

    Examples:
        build_chat_model()
        build_chat_model("ollama:qwen3-coder:30b")
        build_chat_model("openai:gpt-4o")
        build_chat_model(ChatOpenAI(...))
    """
    if model is None:
        model = DEFAULT_MODEL_NAME

    if isinstance(model, BaseChatModel):
        return model

    if temperature is not None:
        kwargs["temperature"] = temperature

    return init_chat_model(model=model, **kwargs)


# Pre-defined default models for backwards compatibility and easy reference
qwen_tool_ollama = build_chat_model(DEFAULT_MODEL_NAME)
small_tool_ollama = qwen_tool_ollama
general_model = qwen_tool_ollama


