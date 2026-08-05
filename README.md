# EngineeringStack SDK

`engineeringstack` is a Python SDK providing a hierarchical multi-agent engineering stack powered by LangGraph and DeepAgents.

## Installation

Install using `uv`:

```bash
uv add engineeringstack
```

Or using `pip`:

```bash
pip install engineeringstack
```

## Quickstart

### Option 1: Class-based Usage

```python
from engineeringstack import EngineeringStack

stack = EngineeringStack()

response = stack.invoke("Create a Flask REST API")
print(response)
```

### Option 2: Factory Function Usage

```python
from engineeringstack import create_engineering_stack

agent = create_engineering_stack()

response = agent.invoke("Create a PostgreSQL database schema")
print(response)
```

### Custom Model or Backend Injection

```python
from engineeringstack import EngineeringStack

stack = EngineeringStack(
    model=model,
    backend=backend,
)

response = stack.invoke("Create a gRPC service for user authentication")
```

## Available SDK Methods

- `stack.invoke(input_data, thread_id=None)`: Synchronous graph execution.
- `stack.stream(input_data, thread_id=None)`: Synchronous event streaming.
- `stack.astream(input_data, thread_id=None)`: Asynchronous event streaming.
- `stack.batch(inputs)`: Batch processing over multiple inputs.

## Public API

`engineeringstack` exports **ONLY**:
- `EngineeringStack`
- `create_engineering_stack`

All internal builders, subagents, tools, prompts, checkpointers, and middleware are encapsulated within the SDK.

## License

MIT
