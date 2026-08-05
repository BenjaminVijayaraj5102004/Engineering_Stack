from langsmith import traceable
from .main.main_agent import main_agent
from ..util.logger import get_logger

logger = get_logger(__name__)


@traceable(name="format_prompt", run_type="prompt")
def format_prompt(user_query: str, system_override: str = None) -> dict:
    """Format user query into agent state input messages."""
    messages = [{"role": "user", "content": user_query}]
    if system_override:
        messages.insert(0, {"role": "system", "content": system_override})
    return {"messages": messages}


@traceable(name="invoke_llm_agent", run_type="chain")
def invoke_agent_workflow(messages_payload: dict) -> dict:
    """Invoke the hierarchical multi-agent graph."""
    return main_agent.invoke(messages_payload)


@traceable(name="parse_output", run_type="parser")
def parse_output(response: dict) -> str:
    """Parse and extract final response text from the graph state."""
    if not response or "messages" not in response:
        return "No response returned from agent workflow."

    messages = response["messages"]
    if not messages:
        return "Empty response messages list."

    last_message = messages[-1]
    if hasattr(last_message, "content"):
        return last_message.content
    elif isinstance(last_message, dict) and "content" in last_message:
        return last_message["content"]

    return str(last_message)


@traceable(name="run_pipeline", run_type="chain")
def run_pipeline(user_query: str) -> str:
    """End-to-end traced pipeline for agent workflow execution."""
    formatted_payload = format_prompt(user_query)
    raw_response = invoke_agent_workflow(formatted_payload)
    final_solution = parse_output(raw_response)
    return final_solution
