from deepagents import create_deep_agent
from ...models.ai_model import small_tool_ollama
from ...util.checkpointer_memory import checkpointer
from ...util.logger import get_logger
from ...prompts.code_review_prompt import CODE_REVIEW_SYSTEM_PROMPT

logger = get_logger(__name__)

logger.info("Initializing Code Reviewer Agent")

code_review_agent = create_deep_agent(
    model=small_tool_ollama,
    system_prompt=CODE_REVIEW_SYSTEM_PROMPT,
    checkpointer=checkpointer,
)

code_review_subagent = {
    "name": "Code_Reviewer",
    "description": "Reviews existing code only. Never implements features, creates files, or delegates tasks.",
    "system_prompt": CODE_REVIEW_SYSTEM_PROMPT,
    "runnable": code_review_agent,
}
