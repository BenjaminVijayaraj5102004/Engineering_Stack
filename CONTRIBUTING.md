# Contributing to EngineeringStack

Thank you for your interest in contributing to **EngineeringStack**! We welcome contributions from developers, researchers, and open-source enthusiasts.

This guide provides guidelines and instructions for setting up your environment, making changes, running tests, and submitting pull requests.

---

## 📜 Table of Contents

- [Code of Conduct](#-code-of-conduct)
- [Development Setup](#-development-setup)
- [Architecture Overview](#-architecture-overview)
- [Workflow & Pull Requests](#-workflow--pull-requests)
- [Coding Standards](#-coding-standards)
- [Testing Guidelines](#-testing-guidelines)
- [Reporting Issues & Feature Requests](#-reporting-issues--feature-requests)

---

## 🤝 Code of Conduct

All contributors are expected to adhere to our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it before participating in our discussions, issues, or pull requests.

---

## 🛠️ Development Setup

### Prerequisites

- **Python 3.12+**
- **uv** (recommended package and environment manager) or `pip`
- **Git**

### Installation

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/engineering-stack/engineeringstack.git
   cd engineeringstack
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # Using uv (fastest)
   uv venv
   # On Windows:
   .venv\Scripts\activate
   # On Linux/macOS:
   source .venv/bin/activate
   ```

3. **Install dependencies in development mode:**
   ```bash
   uv sync
   # Or with pip:
   pip install -e ".[dev]"
   ```

4. **Configure environment variables:**
   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
   Provide your API keys (e.g. `GROQ_API_KEY`, `OPENAI_API_KEY`, or local `OLLAMA` endpoints).

---

## 🏛️ Architecture Overview

EngineeringStack is a hierarchical multi-agent engineering framework built on **LangGraph** and **DeepAgents**:

- **Supervisor Tier (`Main_Agent`)**: Classifies intent, answers general discussions directly, and delegates tasks to domain managers.
- **Manager Tier**:
  - `Helper_Manager`: Single-file scripts, general code, algorithms, utilities.
  - `Database_Manager`: Multi-database persistence architecture (RDBMS, NoSQL, Redis).
  - `API_Manager`: Protocol architectures (REST, GraphQL, gRPC, SOAP).
  - `MCP_Manager`: Model Context Protocol integration, dynamic tool discovery, and `mcp.json` registry management.
- **Specialist Tier (Leaf Subagents)**:
  - `Coding_Agent`, `RDBMS_agent`, `NoSQL_agent`, `REDIS_agent`, `REST_Agent`, `GraphQL_Agent`, `GRPC_Agent`, `SOAP_Agent`.
- **Quality Gate**:
  - `Code_Reviewer`: Audits all generated code for security and performance, delivering a structured 5-bullet summary alongside clean code.

---

## 🔄 Workflow & Pull Requests

1. **Create a topic branch:**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Follow TDD (Test-Driven Development):**
   - Write tests in the `tests/` directory following the Arrange-Act-Assert (AAA) pattern.
   - Implement your changes.
   - Ensure all existing and new tests pass.

3. **Run the test suite:**
   ```bash
   uv run pytest
   ```

4. **Commit your changes:**
   Use clear, conventional commit messages:
   ```bash
   git commit -m "feat(mcp): add dynamic discovery for custom transports"
   ```

5. **Push and open a Pull Request (PR):**
   - Provide a clear PR title and detailed description of the changes.
   - Reference any related issue numbers (e.g., `Fixes #12`).

---

## 📐 Coding Standards

- **Type Annotations**: Use Python standard type hints (`typing`, `Optional`, `Union`, `list`, `dict`).
- **Clean Architecture**: Never hardcode tool configurations or static arrays; use dynamic registries and domain resolution.
- **Error Handling**: Use defensive timeout and exception handling around network, MCP client, and LLM calls.
- **Docstrings**: Document public classes, methods, and functions with clear docstrings explaining arguments and return types.
- **Logging**: Use `get_logger(__name__)` from `engineeringstack.util.logger`. Avoid unprompted `print()` calls in library code.

---

## 🧪 Testing Guidelines

- Tests are located in `tests/`.
- We use `pytest` and Python `unittest`.
- Ensure mock LLMs and mock MCP clients are used for fast, deterministic unit test runs without requiring live API keys.
- Run tests with:
  ```bash
  uv run pytest -v
  ```

---

## 📬 Reporting Issues & Feature Requests

- **Bug Reports**: Open an issue describing the bug, reproduction steps, expected vs. actual behavior, and Python environment details.
- **Feature Requests**: Open an issue detailing the use case, proposed API design, and why it benefits the EngineeringStack community.

Thank you for helping make EngineeringStack better!
