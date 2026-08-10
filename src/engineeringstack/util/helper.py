"""Helper utility for Main Agent intent detection, routing, and conversation management.

This module provides helper functions for the Main Agent to determine whether an incoming
user query is a greeting / normal conversation (which the Main Agent answers directly)
or a coding / complex engineering task (which the Main Agent delegates to specialized
helper subagents such as API_Manager, Database_Manager, or Code_Reviewer).
"""

from enum import Enum
import re
from typing import Any, Optional, Union
from pydantic import BaseModel, Field
from ..schema.state import UserInput
from .logger import get_logger

logger = get_logger(__name__)


class IntentType(str, Enum):
    """Categorized user intent types."""

    GREETING = "greeting"
    CONVERSATION = "conversation"
    API_TASK = "api_task"
    DATABASE_TASK = "database_task"
    CODE_REVIEW_TASK = "code_review_task"
    GENERAL_CODING_TASK = "general_coding_task"
    COMPLEX_TASK = "complex_task"


class RouteAction(str, Enum):
    """Action decision for the Main Agent."""

    DIRECT_ANSWER = "direct_answer"
    DELEGATE_TO_HELPERS = "delegate_to_helpers"


class HelperAgentType(str, Enum):
    """Available helper subagents for delegation."""

    API_MANAGER = "API_Manager"
    DATABASE_MANAGER = "Database_Manager"
    CODE_REVIEWER = "Code_Reviewer"


class RoutingDecision(BaseModel):
    """Structured decision returned by the Main Agent helper."""

    intent: IntentType = Field(
        ...,
        description="The classified intent type of the user request.",
    )
    action: RouteAction = Field(
        ...,
        description="Whether the Main Agent should answer directly or delegate to helper agents.",
    )
    target_agent: Optional[str] = Field(
        default=None,
        description="Name of the helper subagent to delegate to, or None if answering directly.",
    )
    is_conversational: bool = Field(
        default=False,
        description="True if the request is a greeting or general conversational query.",
    )
    is_coding_or_complex: bool = Field(
        default=False,
        description="True if the request involves coding, databases, APIs, or complex engineering tasks.",
    )
    confidence: float = Field(
        default=1.0,
        description="Confidence score for the routing decision (0.0 to 1.0).",
    )
    reasoning: str = Field(
        default="",
        description="Brief explanation of the classification and routing decision.",
    )
    direct_response: Optional[str] = Field(
        default=None,
        description="Pre-composed or suggested response when Main Agent answers directly.",
    )
    task_description: Optional[str] = Field(
        default=None,
        description="Formatted task instructions when delegating to a helper subagent.",
    )


# ---------------------------------------------------------------------------
# Heuristic Pattern Definitions
# ---------------------------------------------------------------------------

_GREETING_PATTERNS = [
    r"^\s*(?:hi|hello|hey|heya|howdy|hola|greetings|good\s+(?:morning|afternoon|evening|day)|sup|yo|what\'?s\s+up)\b",
    r"^\s*(?:welcome|how\s+do\s+you\s+do)\b",
]

_CONVERSATION_PATTERNS = [
    r"\b(?:who\s+are\s+you|what\s+are\s+you|tell\s+me\s+about\s+yourself|introduce\s+yourself)\b",
    r"\b(?:what\s+can\s+you\s+do|how\s+can\s+you\s+help|what\s+are\s+your\s+capabilities|what\s+services\s+do\s+you\s+provide)\b",
    r"\b(?:how\s+are\s+you|how\'?s\s+it\s+going|how\s+are\s+things|how\s+do\s+you\s+feel)\b",
    r"\b(?:thanks|thank\s+you|thanks\s+a\s+lot|much\s+appreciated|cheers|bye|goodbye|see\s+you|take\s+care)\b",
    r"^\s*(?:ok|okay|cool|awesome|great|got\s+it|understood|sure|nice|perfect|sounds\s+good|all\s+good)(?:[\s,]+(?:ok|okay|cool|awesome|great|got\s+it|understood|sure|nice|perfect|sounds\s+good|thanks|thank\s+you|cheers))*\s*[\.\!\?]?\s*$",
    r"\b(?:nice\s+to\s+meet\s+you|pleasure\s+to\s+meet\s+you|good\s+to\s+see\s+you)\b",
]

_API_KEYWORDS = [
    r"\b(?:fastapi|flask|express|django|nest(?:\.?js)?|spring\s+boot|gin|echo|koa)\b",
    r"\b(?:rest|restful|graphql|grpc|soap|webhook|webhooks)\b",
    r"\b(?:api|apis|endpoint|endpoints|route|routes|router|controller)\b",
    r"\b(?:http|get|post|put|patch|delete)\s+(?:request|requests|method|methods|handler|endpoint)\b",
    r"\b(?:crud\s+(?:api|endpoint|routes?)|swagger|openapi|jwt\s+auth)\b",
]

_DATABASE_KEYWORDS = [
    r"\b(?:postgres|postgresql|mysql|sqlite|mariadb|oracle)\b",
    r"\b(?:mongodb|mongo|redis|dynamodb|cassandra|couchdb|neo4j)\b",
    r"\b(?:sql|nosql|rdbms|database|databases|schema|table|tables|index|indexes)\b",
    r"\b(?:migration|migrations|alembic|prisma|sqlalchemy|mongoose|orm)\b",
    r"\b(?:query|queries|crud\s+operations?|cache|caching|redis\s+key)\b",
]

_CODE_REVIEW_KEYWORDS = [
    r"\b(?:review|audit|lint|inspect|analyze)\s+(?:code|this|my|the\s+code|script|implementation|pr|pull\s+request)\b",
    r"\b(?:code\s+review|security\s+audit|vulnerability\s+check|code\s+quality|performance\s+audit)\b",
    r"\b(?:check\s+for\s+bugs|find\s+bugs|spot\s+issues|refactor\s+review)\b",
]

_CODING_KEYWORDS = [
    r"\b(?:write|code|create|build|implement|develop|generate|script|program)\b",
    r"\b(?:function|class|module|algorithm|data\s+structure|debug|fix\s+bug|refactor)\b",
    r"\b(?:python|typescript|javascript|golang|go|rust|java|c\+\+|c\#|ruby|php|kotlin|swift|scala)\b",
    r"\b(?:docker|dockerfile|docker-compose|kubernetes|k8s|ci\/cd|pipeline|unit\s+test|pytest)\b",
]


def extract_query_text(input_data: Any) -> str:
    """Extract clean string query text from diverse input formats.

    Supports string, UserInput model, dictionary, and message payload structures.
    """
    if input_data is None:
        return ""
    if isinstance(input_data, str):
        return input_data.strip()
    if isinstance(input_data, UserInput):
        return input_data.query.strip() if input_data.query else ""
    if isinstance(input_data, dict):
        if "query" in input_data and input_data["query"]:
            return str(input_data["query"]).strip()
        if "messages" in input_data and isinstance(input_data["messages"], list):
            for msg in reversed(input_data["messages"]):
                if isinstance(msg, dict) and msg.get("role") == "user":
                    return str(msg.get("content", "")).strip()
                elif hasattr(msg, "content") and getattr(msg, "type", "") in ("human", "user"):
                    return str(msg.content).strip()
            if input_data["messages"]:
                last = input_data["messages"][-1]
                return str(getattr(last, "content", last.get("content", ""))) if isinstance(last, dict) or hasattr(last, "content") else str(last)
        if "content" in input_data:
            return str(input_data["content"]).strip()
    return str(input_data).strip()


def is_greeting(query: Any) -> bool:
    """Check if the given query is a greeting."""
    text = extract_query_text(query).lower()
    if not text:
        return False
    return any(bool(re.search(pattern, text, re.IGNORECASE)) for pattern in _GREETING_PATTERNS)


def is_conversation(query: Any) -> bool:
    """Check if the given query is general/normal casual conversation."""
    text = extract_query_text(query).lower()
    if not text:
        return False
    return any(bool(re.search(pattern, text, re.IGNORECASE)) for pattern in _CONVERSATION_PATTERNS)


def is_greeting_or_conversation(query: Any) -> bool:
    """Check if query is a greeting or general conversational inquiry.

    If True, the Main Agent itself should handle and answer directly without
    delegating to helper agents.
    """
    text = extract_query_text(query).lower()
    if not text:
        return False

    # Check for explicit coding / database / API indicators first to avoid false positives
    if is_coding_or_complex_task(query):
        return False

    return is_greeting(query) or is_conversation(query)


def is_coding_or_complex_task(query: Any) -> bool:
    """Check if query is a coding or complex engineering task.

    If True, the Main Agent must delegate to specialized helper agents to finish the task.
    """
    text = extract_query_text(query).lower()
    if not text:
        return False

    all_coding_patterns = (
        _API_KEYWORDS + _DATABASE_KEYWORDS + _CODE_REVIEW_KEYWORDS + _CODING_KEYWORDS
    )
    return any(bool(re.search(pat, text, re.IGNORECASE)) for pat in all_coding_patterns)


def classify_intent(query: Any) -> IntentType:
    """Classify the user query into a specific IntentType category."""
    text = extract_query_text(query).lower()
    if not text:
        return IntentType.CONVERSATION

    # 1. Check Code Review tasks
    if any(bool(re.search(p, text, re.IGNORECASE)) for p in _CODE_REVIEW_KEYWORDS):
        return IntentType.CODE_REVIEW_TASK

    # 2. Check API tasks
    if any(bool(re.search(p, text, re.IGNORECASE)) for p in _API_KEYWORDS):
        # If it also heavily mentions databases or fullstack, classify as complex
        if any(bool(re.search(p, text, re.IGNORECASE)) for p in _DATABASE_KEYWORDS):
            return IntentType.COMPLEX_TASK
        return IntentType.API_TASK

    # 3. Check Database tasks
    if any(bool(re.search(p, text, re.IGNORECASE)) for p in _DATABASE_KEYWORDS):
        return IntentType.DATABASE_TASK

    # 4. Check General Coding tasks
    if any(bool(re.search(p, text, re.IGNORECASE)) for p in _CODING_KEYWORDS):
        return IntentType.GENERAL_CODING_TASK

    # 5. Check Greetings
    if is_greeting(text):
        return IntentType.GREETING

    # 6. Check Conversational queries
    if is_conversation(text):
        return IntentType.CONVERSATION

    # Fallback: if query is short and non-technical, consider conversation; else complex task
    if len(text.split()) <= 4:
        return IntentType.CONVERSATION
    return IntentType.COMPLEX_TASK


def determine_helper_agent(intent: IntentType, query: str = "") -> Optional[str]:
    """Determine the optimal helper subagent based on intent and query content."""
    text = query.lower()

    if intent == IntentType.CODE_REVIEW_TASK:
        return HelperAgentType.CODE_REVIEWER.value

    if intent == IntentType.DATABASE_TASK:
        return HelperAgentType.DATABASE_MANAGER.value

    if intent == IntentType.API_TASK:
        return HelperAgentType.API_MANAGER.value

    if intent in (IntentType.GENERAL_CODING_TASK, IntentType.COMPLEX_TASK):
        # Inspect text to route to best manager
        if any(bool(re.search(p, text, re.IGNORECASE)) for p in _DATABASE_KEYWORDS):
            return HelperAgentType.DATABASE_MANAGER.value
        # Default coding and API tasks to API_Manager
        return HelperAgentType.API_MANAGER.value

    return None


def generate_conversational_response(query: Any) -> str:
    """Generate a friendly, helpful conversational response for greetings and chit-chat."""
    text = extract_query_text(query).lower()

    if is_greeting(text):
        return (
            "Hello! I am the Main Agent for the Engineering Stack. "
            "I can help you build APIs (REST, GraphQL, gRPC, SOAP), design databases "
            "(PostgreSQL, MySQL, SQLite, MongoDB, Redis), review and audit code, or solve "
            "complex engineering problems. How can I assist you with your project today?"
        )

    if any(phrase in text for phrase in ["who are you", "what are you", "tell me about yourself", "introduce"]):
        return (
            "I am the Main Agent — the central orchestrator of the Engineering Stack. "
            "I coordinate a team of specialized helper agents including API Managers, "
            "Database Managers, and Code Reviewers to design, build, and verify high-quality software."
        )

    if any(phrase in text for phrase in ["what can you do", "capabilities", "help me", "services"]):
        return (
            "I can assist you with full-lifecycle software engineering:\n"
            "• **API Development**: Fast, robust REST, GraphQL, gRPC, and SOAP services.\n"
            "• **Database Engineering**: Schema design, migrations, queries for SQL (PostgreSQL, MySQL, SQLite) & NoSQL (MongoDB, Redis).\n"
            "• **Code Review & Quality**: Security audits, bug detection, and architectural reviews.\n"
            "• **Custom Code & Scripts**: Python, TypeScript, Go, Rust, and more.\n\n"
            "Tell me what you would like to build!"
        )

    if any(phrase in text for phrase in ["how are you", "how's it going"]):
        return (
            "I'm operating at peak performance and ready to help you engineer great software! "
            "What technical task or project are you working on today?"
        )

    if any(phrase in text for phrase in ["thank", "thanks"]):
        return "You're very welcome! If you have more coding, API, or database questions, feel free to ask anytime."

    if any(phrase in text for phrase in ["bye", "goodbye", "see you"]):
        return "Goodbye! Have a productive coding session. Reach out whenever you need engineering assistance."

    return (
        "Hello! I'm the Main Agent for the Engineering Stack. "
        "Feel free to ask any question about software design, API creation, databases, or code review."
    )


def format_delegation_payload(target_agent: str, description: str) -> dict[str, str]:
    """Format parameter dictionary for the task delegation tool.

    Args:
        target_agent: The name of the subagent (e.g. 'API_Manager', 'Database_Manager', 'Code_Reviewer').
        description: Instructions for the subagent to execute.

    Returns:
        Dict with 'subagent_type' and 'description' keys matching task tool interface.
    """
    return {
        "subagent_type": target_agent,
        "description": description,
    }


def main_agent_helper(input_data: Any) -> RoutingDecision:
    """Primary helping function for the Main Agent.

    Analyzes the user input and determines:
    1. If it is a greeting or normal conversation:
       -> Action: DIRECT_ANSWER. The Main Agent itself answers directly without calling helper agents.
    2. If it is a coding, API, database, code review, or complex engineering task:
       -> Action: DELEGATE_TO_HELPERS. The Main Agent delegates the task to the appropriate helper subagent
          (API_Manager, Database_Manager, or Code_Reviewer).

    Args:
        input_data: String query, UserInput object, dictionary, or message state payload.

    Returns:
        RoutingDecision containing the intent, action, target_agent, and suggested responses or task instructions.
    """
    query_text = extract_query_text(input_data)
    logger.debug("Main Agent Helper evaluating query: '%s'", query_text)

    # Step 1: Check if input is a greeting or normal conversation
    if is_greeting_or_conversation(query_text):
        intent = classify_intent(query_text)
        direct_resp = generate_conversational_response(query_text)
        logger.info("Classified query as conversational (%s). Direct response selected.", intent.value)
        return RoutingDecision(
            intent=intent,
            action=RouteAction.DIRECT_ANSWER,
            target_agent=None,
            is_conversational=True,
            is_coding_or_complex=False,
            confidence=0.95,
            reasoning="User query is a greeting or casual conversation. Main Agent responds directly.",
            direct_response=direct_resp,
            task_description=None,
        )

    # Step 2: Input is a coding or complex engineering task
    intent = classify_intent(query_text)
    target_agent = determine_helper_agent(intent, query_text)

    # Construct clean task instructions for helper agent delegation
    task_desc = f"Execute technical engineering task for user query: {query_text}"
    if isinstance(input_data, UserInput):
        details = []
        if input_data.requirements:
            details.append(f"Requirements: {input_data.requirements}")
        if input_data.framework:
            details.append(f"Framework: {input_data.framework}")
        if input_data.language:
            details.append(f"Language: {input_data.language}")
        if input_data.database:
            details.append(f"Database: {input_data.database}")
        if details:
            task_desc += f" [{' | '.join(details)}]"

    logger.info(
        "Classified query as technical task (%s). Delegating to helper agent: %s",
        intent.value,
        target_agent,
    )

    return RoutingDecision(
        intent=intent,
        action=RouteAction.DELEGATE_TO_HELPERS,
        target_agent=target_agent,
        is_conversational=False,
        is_coding_or_complex=True,
        confidence=0.95,
        reasoning=f"User query requires technical execution ({intent.value}). Delegated to {target_agent}.",
        direct_response=None,
        task_description=task_desc,
    )


def should_delegate_to_helpers(input_data: Any) -> bool:
    """Convenience boolean helper for Main Agent: True if delegation is needed."""
    decision = main_agent_helper(input_data)
    return decision.action == RouteAction.DELEGATE_TO_HELPERS


def get_main_agent_action(input_data: Any) -> tuple[RouteAction, Optional[str], Optional[str]]:
    """Convenience tuple return for Main Agent routing.

    Returns:
        (action, target_agent, direct_response_or_task_desc)
    """
    decision = main_agent_helper(input_data)
    content = (
        decision.direct_response
        if decision.action == RouteAction.DIRECT_ANSWER
        else decision.task_description
    )
    return decision.action, decision.target_agent, content


# ---------------------------------------------------------------------------
# LangChain Tool Interfaces for Main Agent & Builders
# ---------------------------------------------------------------------------
try:
    from langchain_core.tools import tool

    @tool
    def classify_user_intent_tool(query: str) -> str:
        """Classify the user query into intent category (greeting, conversation, api_task, database_task, code_review_task, general_coding_task, complex_task)."""
        intent = classify_intent(query)
        return intent.value

    @tool
    def get_routing_advice_tool(query: str) -> str:
        """Evaluate routing for user query: returns whether to answer directly (greetings/conversation) or delegate to helper subagents (API_Manager, Database_Manager, Code_Reviewer)."""
        decision = main_agent_helper(query)
        if decision.action == RouteAction.DIRECT_ANSWER:
            return (
                f"ACTION: DIRECT_ANSWER\n"
                f"REASONING: {decision.reasoning}\n"
                f"SUGGESTED_RESPONSE: {decision.direct_response}"
            )
        return (
            f"ACTION: DELEGATE_TO_HELPERS\n"
            f"TARGET_AGENT: {decision.target_agent}\n"
            f"TASK_DESCRIPTION: {decision.task_description}\n"
            f"REASONING: {decision.reasoning}"
        )

    @tool
    def generate_greeting_response_tool(query: str) -> str:
        """Generate a polite, professional conversational response introducing the Engineering Stack capabilities."""
        return generate_conversational_response(query)

    DEFAULT_MAIN_TOOLS: list[Any] = [
        classify_user_intent_tool,
        get_routing_advice_tool,
        generate_greeting_response_tool,
    ]

except ImportError:
    DEFAULT_MAIN_TOOLS = []

