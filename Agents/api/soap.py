import Agents.config  # Initialize environment and LangSmith tracing
from deepagents import create_deep_agent
from models.ai_model import small_tool_ollama
from tools.tools import search_code, get_file_contents
from util.checkpointer_memory import checkpointer

from prompts.api_prompt import SOAP_SYSTEM_PROMPT

print("Entered SOAP Agent")

soap_agent = create_deep_agent(
    model=small_tool_ollama,
    tools=[search_code, get_file_contents],
    system_prompt=SOAP_SYSTEM_PROMPT,
    checkpointer=checkpointer,
)

soap_subagent = {
    "name": "SOAP_Agent",
    "description": "Handles SOAP API requests, XML formatting, WSDL definitions, SOAP Envelope, SOAP Header, and SOAP Body.",
    "system_prompt": SOAP_SYSTEM_PROMPT,
    "runnable": soap_agent,
}