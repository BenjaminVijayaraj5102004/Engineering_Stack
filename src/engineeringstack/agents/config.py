import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
AGENT_ROOT = Path(__file__).parent.parent.resolve()
env_path = AGENT_ROOT / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# Retrieve LangSmith API Key
langsmith_key = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")

if langsmith_key:
    os.environ["LANGSMITH_API_KEY"] = langsmith_key
    os.environ["LANGCHAIN_API_KEY"] = langsmith_key

# Set LangSmith Tracing Environment Variables
os.environ["LANGCHAIN_TRACING_V2"] = "true"
if not os.getenv("LANGCHAIN_ENDPOINT"):
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
if not os.getenv("LANGCHAIN_PROJECT"):
    os.environ["LANGCHAIN_PROJECT"] = "engineeringstack-sdk"
os.environ["LANGSMITH_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "engineeringstack-sdk")


def init_tracing():
    """Explicit initializer for LangSmith tracing."""
    return {
        "tracing_v2": os.getenv("LANGCHAIN_TRACING_V2"),
        "project": os.getenv("LANGCHAIN_PROJECT"),
        "endpoint": os.getenv("LANGCHAIN_ENDPOINT"),
        "has_key": bool(langsmith_key),
    }


# Run on import
init_tracing()
