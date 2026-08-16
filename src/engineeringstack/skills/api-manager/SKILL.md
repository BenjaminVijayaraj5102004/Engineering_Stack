---
name: api-manager
description: Routes full application API suites to protocol specialists and Code_Reviewer.
---

# API Manager Procedural Skill

## Available Subagents
- `REST_Agent`: REST APIs, FastAPI/Flask/Express endpoints, route controllers, and HTTP status.
- `GraphQL_Agent`: GraphQL schemas, resolvers, queries, mutations, subscriptions, and types.
- `GRPC_Agent`: gRPC services, Protocol Buffers (`.proto`), streaming, and RPC handlers.
- `SOAP_Agent`: SOAP web services, XML schemas, WSDL specifications, and envelope handlers.
- `Code_Reviewer`: Audits API code and outputs 5 bullet points + code block.

## Routing Rules
1. **Multi-Protocol Applications**:
   - Determine communication protocol requirements from incoming architecture specifications.
   - For HTTP/JSON RESTful endpoints, delegate to `REST_Agent`.
   - For graph queries and flexible schema resolvers, delegate to `GraphQL_Agent`.
   - For high-throughput microservice RPC contracts, delegate to `GRPC_Agent`.
   - For enterprise XML/WSDL services, delegate to `SOAP_Agent`.
2. **Quality Assurance Gate**:
   - Every generated API service must pass through `Code_Reviewer` before returning to user.
3. **Execution Pipeline**:
   - Step 1: Delegate to `REST_Agent`, `GraphQL_Agent`, `GRPC_Agent`, or `SOAP_Agent`.
   - Step 2: Delegate to `Code_Reviewer` to review the generated code.
   - Step 3: Relay Code_Reviewer's output directly without alteration.

## Operational Constraints
- Pure Router: Never implement raw route endpoints directly. Expose only `read_file` (for procedural skills) and `task` (for delegation).
- Subagents: API specialists (`REST_Agent`, `GraphQL_Agent`, `GRPC_Agent`, `SOAP_Agent`) use MCP & inspection tools (`search_code`, `get_file_contents`, `read_file`, `write_file`) for implementation.
- Quality Assurance: `Code_Reviewer` verifies all generated API code before returning to user.
