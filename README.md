---
title: EngineeringStack SDK
description: Hierarchical multi-agent engineering framework with session memory, persistent disk memory, Model Context Protocol (MCP) tool discovery, and model-agnostic BYOM support
tags:
  - engineeringstack
  - langgraph
  - multi-agent
  - mcp
  - python
  - memory
  - byom
status: active
version: 0.1.7
---

# 🛠️ EngineeringStack SDK

[![Version](https://img.shields.io/badge/version-0.1.7-blue.svg)](https://test.pypi.org/project/engineeringstack/)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/framework-LangGraph%20%7C%20DeepAgents-orange.svg)](https://github.com/langchain-ai/langgraph)
[![Tests](https://img.shields.io/badge/tests-156%20passed-brightgreen.svg)](tests/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Contributing](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Code of Conduct](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](CODE_OF_CONDUCT.md)

**EngineeringStack** is a hierarchical multi-agent engineering framework built on top of LangGraph.

Instead of relying on a single prompt to handle database modeling, API architecture, algorithm implementation, and code quality all at once, EngineeringStack organizes specialized agents into a structured engineering team. A top-level supervisor delegates tasks to dedicated domain managers, who coordinate specialized leaf agents, discover external tools via Model Context Protocol (MCP), and enforce a code review quality gate before returning results.

---

## 🎯 What EngineeringStack Does

EngineeringStack coordinates a 3-tier hierarchy of AI agents designed to handle full-lifecycle software development tasks:

```mermaid
graph TD
    User([User Request]) --> Stack[EngineeringStack SDK]
    Stack --> MainAgent[Main Agent Supervisor]
    
    subgraph Manager Layer [Manager Routing Tier]
        MainAgent --> HelperMgr[Helper Manager]
        MainAgent --> DBMgr[Database Manager]
        MainAgent --> APIMgr[API Manager]
        MainAgent --> MCPMgr[MCP Manager]
    end
    
    subgraph Specialist Layer [Domain Specialist Tier]
        HelperMgr --> CodingAgent[Coding Agent]
        HelperMgr --> QA1[Code Reviewer]
        
        DBMgr --> RDBMS[RDBMS Agent - SQL / PostgreSQL]
        DBMgr --> NoSQL[NoSQL Agent - MongoDB]
        DBMgr --> Redis[Redis Agent - Cache]
        DBMgr --> QA2[Code Reviewer]
        
        APIMgr --> REST[REST Agent - FastAPI / Express]
        APIMgr --> GraphQL[GraphQL Agent - Schemas / Resolvers]
        APIMgr --> GRPC[gRPC Agent - Protobuf]
        APIMgr --> SOAP[SOAP Agent - XML / WSDL]
        APIMgr --> QA3[Code Reviewer]
        
        MCPMgr --> MCPTools[Dynamic Tool Discovery & Execution]
    end
    
    QA1 --> Result([Structured Result: 5-Point Summary + Clean Code])
    QA2 --> Result
    QA3 --> Result
    MCPTools --> Result
```

### Agent Hierarchy & Roles

| Tier | Agent | Responsibility |
| :--- | :--- | :--- |
| **Supervisor** | **Main Agent** | Classifies incoming intent, handles general discussions directly, and routes engineering tasks to the appropriate manager. |
| **Manager** | **Helper Manager** | Handles standalone single-file tasks, scripts, algorithms, utilities, and bug fixes. Coordinates `Coding_Agent`. |
| ↳ *Specialist* | `Coding_Agent` | Generates general software logic, scripts, algorithms, and bug fixes. |
| **Manager** | **Database Manager** | Coordinates database architecture across relational, document, and in-memory caching systems. |
| ↳ *Specialist* | `RDBMS_agent` | Relational database schemas (PostgreSQL, MySQL, SQLite, Supabase), migrations, tables, indexes, and queries. |
| ↳ *Specialist* | `NoSQL_agent` | Document stores (MongoDB, DynamoDB), schemas, collections, indexes, and aggregation pipelines. |
| ↳ *Specialist* | `REDIS_agent` | In-memory key-value caching, session storage, pub/sub configurations, and rate-limiting scripts. |
| **Manager** | **API Manager** | Coordinates API design and service communication across modern and enterprise protocols. |
| ↳ *Specialist* | `REST_Agent` | RESTful endpoints (FastAPI, Flask, Express), HTTP handlers, request validation, and status codes. |
| ↳ *Specialist* | `GraphQL_Agent` | GraphQL schema definitions (`.graphql`), queries, mutations, subscriptions, and resolvers. |
| ↳ *Specialist* | `GRPC_Agent` | Protocol Buffer contracts (`.proto`), gRPC server interfaces, and client stubs. |
| ↳ *Specialist* | `SOAP_Agent` | Enterprise XML schemas, WSDL contracts, and SOAP payload handlers. |
| **Manager** | **MCP Manager** | Integrates and manages Model Context Protocol (MCP) servers, dynamically discovering remote and local tools without code modifications. |
| **Quality Gate** | **Code Reviewer** | Audits all generated code for correctness, security, and best practices. Delivers a structured 5-bullet summary alongside clean code. |

---

## 📦 Installation & Setup

```bash
# Using uv (recommended)
uv add engineeringstack --index-url https://test.pypi.org/simple/

# Or using pip
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple engineeringstack
```

Set your model provider API key (e.g. Groq, OpenAI, Anthropic, Gemini):

```bash
export GROQ_API_KEY="gsk_..."
# or
export OPENAI_API_KEY="sk-..."
```

---

## 🔌 Model Context Protocol (MCP) & Tool Automation

EngineeringStack provides full, automated integration with the **Model Context Protocol (MCP)**, supporting `stdio`, `sse`, and `http` transports.

### 1. Zero-Code Tool Discovery & Automatic Domain Binding

Whenever an MCP server is configured in `mcp.json` or registered at runtime via `register_mcp_server`, EngineeringStack dynamically discovers exposed tools and binds them to the relevant domain subagents automatically:

```json
{
  "mcpServers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": {
        "Authorization": "Bearer ${GITHUB_ACCESS_TOKEN}"
      }
    },
    "meniscus": {
      "type": "stdio",
      "command": "men-mcp",
      "args": []
    },
    "postgres": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-postgres",
        "postgresql://postgres:password@localhost:5432/mydb"
      ]
    },
    "supabase": {
      "type": "http",
      "url": "https://mcp.supabase.com/mcp",
      "headers": {
        "Authorization": "Bearer ${SUPABASE_ACCESS_TOKEN}"
      }
    }
  }
}
```

### 2. Runtime MCP Tool Management

You can query, register, or remove MCP servers programmatically or through natural language:

```python
from engineeringstack import create_engineering_stack

stack = create_engineering_stack()

# Register a new MCP server dynamically
response = stack.invoke(
    "Connect to the Postgres MCP server via npx @modelcontextprotocol/server-postgres postgresql://localhost:5432/app"
)
print(response.text)
# Output confirms registration in mcp.json and lists all discovered tools.
```

---

## 🧠 Memory Systems

EngineeringStack provides two distinct memory mechanisms: **Session Memory** for active multi-turn conversations, and **Persistent Memory** for long-term project guidelines, preferences, and agent instructions.

### 1. Session Memory (Multi-Turn Conversations)

Session memory maintains conversation history and context within a thread. By passing a `thread_id`, the agent remembers requirements, earlier decisions, and prior code generated during earlier turns.

```python
from engineeringstack import create_engineering_stack

stack = create_engineering_stack()

# Turn 1: Introduce project context
stack.invoke(
    "We are building a payment gateway called PayNexus using FastAPI and PostgreSQL.",
    thread_id="session-paynexus-01"
)

# Turn 2: Follow-up request relying on context from Turn 1
response = stack.invoke(
    "Generate the database schema for transaction records.",
    thread_id="session-paynexus-01"
)

print(response.code)
# Output includes PostgreSQL tables specifically tailored to PayNexus transactions.
```

### 2. Persistent Memory & Stores

Persistent memory stores long-term instructions, coding guidelines, and project specifications in `/memories/` files (such as `preferences.md` and `AGENTS.md`). Agents can read from and write to these memory files across different sessions:

```python
from langgraph.store.memory import InMemoryStore
from engineeringstack import create_engineering_stack

custom_store = InMemoryStore()

stack = create_engineering_stack(
    memory=["/memories/preferences.md", "/memories/coding_standards.md"],
    store=custom_store,
)

# Any memory updates (e.g., project coding rules) are saved to the store
response = stack.invoke("Remember that all database timestamps must use UTC timezone.")
```

---

## 🔌 Bring Your Own Model (BYOM)

EngineeringStack is model-agnostic. You can use any major LLM provider by passing a model string or a pre-configured LangChain `BaseChatModel` instance.

### Using Provider Strings

```python
from engineeringstack import create_engineering_stack

# 1. Groq (High-speed inference)
stack = create_engineering_stack(model="groq:llama-3.3-70b-versatile")

# 2. Local Ollama (Private & offline)
stack = create_engineering_stack(model="ollama:qwen2.5-coder:7b")

# 3. OpenAI
stack = create_engineering_stack(model="openai:gpt-4o")

# 4. Google Gemini
stack = create_engineering_stack(model="gemini:gemini-2.0-flash")

# 5. Anthropic Claude
stack = create_engineering_stack(model="anthropic:claude-3-5-sonnet-20241022")
```

### Using Custom LangChain ChatModel Instances

```python
from langchain_openai import ChatOpenAI
from engineeringstack import create_engineering_stack

custom_model = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.1,
    max_tokens=4096
)

stack = create_engineering_stack(model=custom_model)
```

---

## ⚡ Execution Modes

EngineeringStack supports synchronous invocation, streaming, asynchronous streaming, and batch execution:

### 1. Synchronous Invocation (`invoke`)

```python
from engineeringstack import create_engineering_stack

stack = create_engineering_stack()

result = stack.invoke("Create a Redis token-bucket rate limiter in Python.")

print("--- SUMMARY ---")
for point in result.summary:
    print(f"- {point}")

print("\n--- CODE ---")
print(result.code)
```

### 2. Streaming (`stream`)

```python
for chunk in stack.stream("Write a Python decorator for caching function results."):
    print(chunk, end="", flush=True)
```

### 3. Asynchronous Streaming (`astream`)

```python
import asyncio
from engineeringstack import create_engineering_stack

async def main():
    stack = create_engineering_stack()
    async for chunk in stack.astream("Design a REST API endpoint for user registration."):
        print(chunk, end="", flush=True)

asyncio.run(main())
```

### 4. Batch Processing (`batch`)

```python
tasks = [
    "Write a SQL migration adding an index to the orders table.",
    "Create a FastAPI route to fetch an order by ID.",
    "Build a Redis helper to cache order details."
]

results = stack.batch(tasks)

for task_name, res in zip(tasks, results):
    print(f"Task: {task_name}")
    print(f"Summary points: {len(res.summary)} | Code lines: {len(res.code.splitlines())}\n")
```

---

## 📋 Structured Output (`AIOutput`)

Every call returns a typed `AIOutput` object:

```python
class AIOutput:
    summary: list[str]  # 5 concise bullet points summarizing the implementation
    code: str           # Pure, executable code extracted from the solution
    text: str           # Full raw response text including explanations
```

---

## 🎛️ Logging & Diagnostics

EngineeringStack uses `logging.NullHandler` by default for zero-noise production environments. To enable verbose logging:

```python
from engineeringstack import enable_logging, disable_logging

# Enable verbose console logging
enable_logging(to_console=True)

# Run queries with full routing visibility...
stack.invoke("Design a MongoDB collection for audit logs.")

# Disable logging when done
disable_logging()
```

---

## 🧪 Testing

Run the full automated test suite covering routing, memory persistence, MCP tools, and dynamic adapters:

```bash
uv run pytest
```

```text
============================= 156 passed in 32.15s =============================
```

---

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) and [Code of Conduct](CODE_OF_CONDUCT.md) before submitting pull requests.

---

## 📄 License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for details.
