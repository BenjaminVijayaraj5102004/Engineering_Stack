# EngineeringStack SDK

[![Version](https://img.shields.io/badge/version-0.1.3-blue.svg)](https://github.com/BenjaminVijayaraj5102004/Engineering_Stack)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/framework-LangGraph%20%7C%20DeepAgents-orange.svg)](https://github.com/langchain-ai/langgraph)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

EngineeringStack is a Python SDK designed for building hierarchical multi-agent engineering workflows. Built on top of LangGraph and DeepAgents, it coordinates specialized subagents for software architecture, API design, database schemas, and automated code review with configurable model providers and persistent memory backends.

---

## What is in v0.1.3

- **Cross-Thread Long-Term Memory**: Support for persistent memory routes (`/memories/AGENTS.md`) using virtual stores or physical local disk directories (`local_memory_dir`).
- **Dynamic Model Injection**: Plug in any model provider through standard strings (`ollama:qwen2.5-coder:32b`, `openai:gpt-4o`, `google_genai:gemini-2.5-flash`) or initialized LangChain chat model instances.
- **Hierarchical Specialist Routing**: A main supervisor agent delegates tasks to specialized Manager agents (API Manager, Database Manager) and domain experts (REST, GraphQL, gRPC, SOAP, RDBMS, NoSQL, Redis, and Code Review).
- **Structured Schema Normalization**: Automatic conversion of raw strings or dictionaries into validated `UserInput` objects and structured `AIOutput` (with formatted summaries and extracted code).
- **Synchronous, Asynchronous, and Streaming APIs**: Support for `invoke`, `stream`, `astream`, and `batch` operations.
- **Type Hinting**: Complete PEP 561 compliance with bundled `py.typed` marker.

---

## Agent and Capability Matrix

| Category | Component | Status | Description |
| :--- | :--- | :---: | :--- |
| **Core** | Hierarchical Multi-Agent Graph | Available | Supervisor graph coordinating specialized subagent execution |
| | Cross-Thread Memory | Available | Virtual store (`StoreBackend`) and local disk (`FilesystemBackend`) memory |
| | Custom LLM Injection | Available | Support for Ollama, Groq, OpenAI, Google Gemini, Anthropic, etc. |
| | Normalization Pipeline | Available | Automated parsing for `UserInput` and `AIOutput` structures |
| **API Management** | API Manager | Available | Routes API architecture tasks to specific protocol specialists |
| | REST Agent | Available | Generates FastAPI, Flask, Express, and Django REST controllers |
| | GraphQL Agent | Available | Generates schemas, queries, mutations, and resolvers |
| | gRPC Agent | Available | Generates Protocol Buffer (`.proto`) definitions and service stubs |
| | SOAP Agent | Available | Generates WSDL definitions and SOAP XML handlers |
| **Database Management** | Database Manager | Available | Routes database queries to specialized storage workers |
| | RDBMS Agent | Available | Generates SQL schemas, migrations, indices, and ORM models |
| | NoSQL Agent | Available | Generates document schemas and aggregation pipelines |
| | Redis Agent | Available | Generates key-value models, caching strategies, and pub/sub patterns |
| **Code Quality** | Code Reviewer Agent | Available | Audits code for security vulnerabilities, performance, and best practices |
| **Execution Modes** | Synchronous Invocation | Available | `stack.invoke(query)` returning structured output |
| | Synchronous Streaming | Available | `stack.stream(query)` yielding graph execution chunks |
| | Asynchronous Streaming | Available | `stack.astream(query)` for async web frameworks |
| | Batch Execution | Available | `stack.batch([queries])` for parallel processing |

---

## Installation

Using `uv`:

```bash
uv add engineeringstack
```

Or using standard `pip`:

```bash
pip install engineeringstack
```

---

## Quickstart

### 1. Basic Usage

```python
from engineeringstack import EngineeringStack

# Initialize default stack
stack = EngineeringStack()

# Execute a query
response = stack.invoke("Create a FastAPI endpoint for user authentication with JWT")

# Access structured output
print("=== Executive Summary ===")
for step in response["ai_output"].summary:
    print(f"- {step}")

print("\n=== Generated Code ===")
print(response["ai_output"].code)
```

### 2. Using Cross-Thread Memory

#### Local Disk Storage
Save preferences and guidelines directly to a physical directory on your local machine:

```python
import uuid
from engineeringstack import EngineeringStack

# Point stack to a local directory
stack = EngineeringStack(local_memory_dir="./project_memory")

# Thread 1: Teach the agent project conventions
thread_1 = str(uuid.uuid4())
stack.invoke(
    "Save to /memory/AGENTS.md: Always use SQLAlchemy with PostgreSQL for database models.",
    thread_id=thread_1,
)

# Thread 2: A new conversation automatically reads AGENTS.md
thread_2 = str(uuid.uuid4())
response = stack.invoke(
    "Design the user model schema.",
    thread_id=thread_2,
)
print(response["ai_output"].code)
```

### 3. Custom Model Providers

```python
from engineeringstack import EngineeringStack

# Option A: Local Ollama Model
stack = EngineeringStack(model="ollama:qwen2.5-coder:32b")

# Option B: Cloud Provider String
stack = EngineeringStack(model="google_genai:gemini-2.5-flash")

# Option C: Pre-configured LangChain Chat Model
from langchain_groq import ChatGroq

custom_llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
)
stack = EngineeringStack(model=custom_llm)
```

### 4. Streaming Responses

```python
from engineeringstack import EngineeringStack

stack = EngineeringStack()

# Synchronous streaming
for chunk in stack.stream("Create a gRPC service for real-time messaging"):
    print(chunk, end="", flush=True)

# Asynchronous streaming
async def main():
    async for chunk in stack.astream("Design a MongoDB collection for audit logs"):
        print(chunk, end="", flush=True)
```

---

## Architecture

```mermaid
graph TD
    User([User Request / UserInput]) --> SDK[EngineeringStack SDK]
    SDK --> Normalizer[Input Normalizer]
    Normalizer --> MainAgent[Main Agent Supervisor]
    
    MainAgent --> APIMgr[API Manager Subagent]
    MainAgent --> DBMgr[Database Manager Subagent]
    MainAgent --> Reviewer[Code Reviewer Subagent]
    
    APIMgr --> REST[REST Agent]
    APIMgr --> GraphQL[GraphQL Agent]
    APIMgr --> gRPC[gRPC Agent]
    APIMgr --> SOAP[SOAP Agent]
    
    DBMgr --> RDBMS[RDBMS Agent]
    DBMgr --> NoSQL[NoSQL Agent]
    DBMgr --> Redis[Redis Agent]
    
    REST --> Output[AIOutput Normalizer]
    GraphQL --> Output
    gRPC --> Output
    SOAP --> Output
    RDBMS --> Output
    NoSQL --> Output
    Redis --> Output
    Reviewer --> Output
    
    Output --> FinalResponse([Response: summary + code])
```

---

## Roadmap & Upcoming Features

The following initiatives are planned for upcoming releases:

- [ ] **Retrieval-Augmented Generation (RAG)**
  - [ ] Codebase semantic indexing using AST parsers and embeddings
  - [ ] External API documentation ingestion (OpenAPI, GraphQL schemas, Protobuf)
  - [ ] Hybrid vector and lexical search for context augmentation
- [ ] **Custom Model Context Protocol (MCP) Integration**
  - [ ] Native MCP server discovery and connection pooling
  - [ ] Custom tool execution via MCP client adapters
  - [ ] Sandboxed filesystem and terminal execution over MCP
- [ ] **Advanced Memory & Storage**
  - [ ] Persistent PostgreSQL checkpointer and vector store integration
  - [ ] Automatic memory summarization and eviction policies
  - [ ] Workspace-wide multi-tenant scoping
- [ ] **Automated Testing & Feedback Loops**
  - [ ] Auto-generation of unit tests for implemented code
  - [ ] In-loop code execution and self-healing error correction
- [ ] **Distributed Execution**
  - [ ] Async background task dispatching via Celery / Temporal

---

## Configuration & Security

- **Environment Variables**: Configure API keys in your `.env` file or environment:
  ```env
  GROQ_API_KEY="your_groq_key"
  GOOGLE_API_KEY="your_google_gemini_key"
  OPENAI_API_KEY="your_openai_key"
  DATABASE_URL="postgresql://user:pass@localhost:5432/dbname"
  ```
- **Privacy Safeguards**: Local trace logs, credentials, and build caches are strictly ignored by `.gitignore` to prevent accidental credential leaks.

---

## Development & Testing

Run the automated test suite:

```bash
uv run pytest -v
```

Build the distribution package:

```bash
uv build
```

---

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.
