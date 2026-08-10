---
title: EngineeringStack SDK
description: Hierarchical multi-agent engineering framework built on LangGraph and DeepAgents
version: 0.1.3
tags:
  - langgraph
  - deepagents
  - multi-agent
  - ai-engineering
  - python-sdk
status: active
license: MIT
---

# 🚀 EngineeringStack SDK

[![Version](https://img.shields.io/badge/version-0.1.3-blue.svg)](https://github.com/BenjaminVijayaraj5102004/Engineering_Stack)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/framework-LangGraph%20%7C%20DeepAgents-orange.svg)](https://github.com/langchain-ai/langgraph)
[![Tests](https://img.shields.io/badge/tests-96%20passed-brightgreen.svg)](tests/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**EngineeringStack** is a developer-first Python SDK designed to orchestrate hierarchical, specialized AI agents for real-world software engineering workflows. Built on top of **LangGraph** and **DeepAgents**, it coordinates a supervisor agent with domain-specific subagents (API architects, database designers, and code reviewers) while preserving long-term cross-thread memory.

> [!tip] Why EngineeringStack?
> Instead of relying on a single monolithic prompt to handle full-stack design, database migrations, protocol specs, and security audits, EngineeringStack routes tasks to dedicated subagents that specialize in single domains with isolated context and tailored toolsets.

---

## ⚡ Key Highlights

* 🧠 **Cross-Thread Memory**: Retain user preferences and project guidelines across distinct conversation threads using virtual in-memory stores or local disk directories (`/memories/AGENTS.md`).
* 🔀 **Hierarchical Delegation**: A central supervisor coordinates manager agents (**API Manager**, **Database Manager**) and deep specialists (**REST**, **GraphQL**, **gRPC**, **SOAP**, **RDBMS**, **NoSQL**, **Redis**, and **Code Reviewer**).
* 🔌 **Any Model, Anywhere**: Drop in models from **Groq**, **Ollama**, **OpenAI**, **Google Gemini**, or **Anthropic** via standard connection strings or native LangChain chat instances.
* 📦 **Structured Output Normalization**: Automatically receives raw text or JSON and yields clean `UserInput` representations and structured `AIOutput` (5-point executive summaries + extracted executable code blocks).
* 🔄 **Sync, Async & Streaming**: Native support for `.invoke()`, `.stream()`, `.astream()`, and `.batch()` for integration with terminal CLIs, FastAPI backends, and background workers.

---

## 🏗️ Architecture

```mermaid
graph TD
    User([User Request]) --> SDK[EngineeringStack SDK]
    SDK --> InputNorm[Input Normalizer]
    InputNorm --> MainAgent[Supervisor Agent]
    
    subgraph Manager Layer
        MainAgent --> APIMgr[API Manager]
        MainAgent --> DBMgr[Database Manager]
        MainAgent --> Reviewer[Code Reviewer Agent]
    end
    
    subgraph Specialist Layer
        APIMgr --> REST[REST Specialist]
        APIMgr --> GraphQL[GraphQL Specialist]
        APIMgr --> gRPC[gRPC Specialist]
        APIMgr --> SOAP[SOAP Specialist]
        
        DBMgr --> RDBMS[RDBMS Specialist]
        DBMgr --> NoSQL[NoSQL Specialist]
        DBMgr --> Redis[Redis Specialist]
    end
    
    REST --> OutputNorm[AIOutput Normalizer]
    GraphQL --> OutputNorm
    gRPC --> OutputNorm
    SOAP --> OutputNorm
    RDBMS --> OutputNorm
    NoSQL --> OutputNorm
    Redis --> OutputNorm
    Reviewer --> OutputNorm
    
    OutputNorm --> Response([Response: 5-Point Summary + Code])
```

---

## 🤖 Agent Matrix

| Agent | Scope & Role | Tools & Capabilities |
| :--- | :--- | :--- |
| **Supervisor (Main Agent)** | Intent classification, memory persistence & task routing | `classify_user_intent`, `get_routing_advice`, `generate_greeting_response` |
| **API Manager** | Coordinates API design and routes protocol queries | Protocol selection & subagent delegation |
| ↳ **REST Specialist** | Builds FastAPI, Express, Django REST endpoints & controllers | `search_code`, `get_file_contents` |
| ↳ **GraphQL Specialist** | Generates GraphQL schemas, resolvers, mutations & queries | `search_code`, `get_file_contents` |
| ↳ **gRPC Specialist** | Designs Protocol Buffers (`.proto`) and RPC services | `search_code`, `get_file_contents` |
| ↳ **SOAP Specialist** | Generates XML payloads, WSDL schemas & SOAP handlers | `search_code`, `get_file_contents` |
| **Database Manager** | Coordinates data modeling and storage strategies | Schema optimization & storage delegation |
| ↳ **RDBMS Specialist** | PostgreSQL, MySQL, SQLite schemas, migrations & SQLAlchemy ORM | `search_code`, `get_file_contents` |
| ↳ **NoSQL Specialist** | MongoDB, DynamoDB, document schemas & aggregation pipelines | `search_code`, `get_file_contents` |
| ↳ **Redis Specialist** | In-memory key-value data structures, caching layers & pub/sub | `search_code`, `get_file_contents` |
| **Code Reviewer** | Audits code for security flaws, bugs & performance bottlenecks | Code analysis & non-destructive review |

---

## 📦 Installation

Install via `uv` (recommended):

```bash
uv add engineeringstack
```

Or via standard `pip`:

```bash
pip install engineeringstack
```

---

## 🚀 Quickstart Guide

### 1. Basic Invocation

Get started in just a few lines of code:

```python
from engineeringstack import EngineeringStack

# Initialize default stack
stack = EngineeringStack()

# Execute a query
response = stack.invoke("Create a FastAPI endpoint for user registration with bcrypt password hashing")

# Access structured response
print("📋 Executive Summary:")
for bullet in response["ai_output"].summary:
    print(f"  • {bullet}")

print("\n💻 Generated Code:")
print(response["ai_output"].code)
```

---

### 2. Cross-Thread Memory Persistence

EngineeringStack allows agents to remember project rules, schemas, and user preferences across independent conversation threads.

```python
import uuid
from engineeringstack import EngineeringStack

# Point stack to a persistent directory on disk
stack = EngineeringStack(local_memory_dir="./project_memory")

# Conversation Thread 1: Define architecture guidelines
thread_1 = str(uuid.uuid4())
stack.invoke(
    "Save to /memory/AGENTS.md: Always use PostgreSQL with async SQLAlchemy and UUID primary keys.",
    thread_id=thread_1,
)

# Conversation Thread 2: Fresh thread automatically loads AGENTS.md
thread_2 = str(uuid.uuid4())
response = stack.invoke(
    "Generate the User account database model.",
    thread_id=thread_2,
)

print(response["ai_output"].code)
```

> [!note] Memory Storage Options
> * **Virtual Store**: Pass `store=InMemoryStore()` for fast, in-memory testing.
> * **Disk Store**: Pass `local_memory_dir="./memories"` for persistent local files.

---

### 3. Bring Your Own Model (BYOM)

Easily switch between local open-source models and cloud providers:

```python
import os
from dotenv import load_dotenv
from engineeringstack import EngineeringStack
from langchain_groq import ChatGroq

load_dotenv()

# Option A: Fast Cloud LLM via Groq
llm = ChatGroq(
    model_name="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
)
stack = EngineeringStack(model=llm)

# Option B: Local Ollama Model
# stack = EngineeringStack(model="ollama:qwen2.5-coder:32b")

# Option C: Google Gemini
# stack = EngineeringStack(model="google_genai:gemini-2.5-flash")
```

---

### 4. Streaming & Async Execution

Stream tokens in real time to your terminal or web application:

```python
import asyncio
from engineeringstack import EngineeringStack

stack = EngineeringStack()

# Synchronous Streaming
for chunk in stack.stream("Design a Redis caching strategy for user session tokens"):
    print(chunk, end="", flush=True)

# Asynchronous Streaming (FastAPI / WebSockets)
async def stream_response():
    async for chunk in stack.astream("Create a GraphQL mutation for updating user profile"):
        print(chunk, end="", flush=True)

asyncio.run(stream_response())
```

---

## ⚙️ Environment Configuration

Create a `.env` file in your project root:

```env
# LLM Providers
GROQ_API_KEY="your_groq_api_key"
OPENAI_API_KEY="your_openai_api_key"
GOOGLE_API_KEY="your_google_gemini_api_key"

# Optional Database Checkpointer
DATABASE_URL="postgresql://postgres:password@localhost:5432/langgraph_db"

# Observability (Optional)
LANGSMITH_TRACING="true"
LANGSMITH_API_KEY="your_langsmith_key"
LANGSMITH_PROJECT="engineering-stack"
```

---

## 🧪 Testing & Verification

Run the comprehensive test suite (96 tests covering unit logic, edge cases, cross-thread memory, and live Groq API integration):

```bash
# Run complete test suite
uv run pytest -v

# Run specific integration tests
uv run pytest tests/test_main_agent_workflow.py -v
```

---

## 🗺️ Roadmap

- [x] **v0.1.3**: Hierarchical routing, cross-thread memory, structured output extraction.
- [ ] **RAG & Semantic Code Search**: AST-based codebase indexing and vector search over local repositories.
- [ ] **Expanded MCP Client**: Discovery and tool calling over Model Context Protocol servers.
- [ ] **Automated Self-Correction**: In-loop test execution and automated syntax correction before returning results.
- [ ] **Postgres Checkpointing**: Native asynchronous PostgreSQL checkpointer for distributed multi-agent state.

---

## 📄 License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for more information.
