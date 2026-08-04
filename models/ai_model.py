import Agents.config  # Initialize environment variables and LangSmith tracing
from langchain_ollama import ChatOllama


class Models:
    def __init__(self,model,temperature):
            self.model = model
            self.temperature = temperature

models = Models("qwen3-coder:30b", 0)
models1 = Models("qwen2.5-coder:7b", 0.7)
models2 = Models("llama3.1:8b", 0.7)

general_model = ChatOllama(
    model=models2.model,
    temperature=models2.temperature,
)

qwen_tool_ollama = ChatOllama(
    model=models1.model,
    temperature=models1.temperature,
)

small_tool_ollama = ChatOllama(
    model=models.model,
    temperature=models.temperature,
    num_ctx=32768,
)


