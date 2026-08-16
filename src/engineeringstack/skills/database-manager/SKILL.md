---
name: database-manager
description: Routes full application database architectures to database specialists and Code_Reviewer.
---

# Database Manager Procedural Skill

## Available Subagents
- `RDBMS_agent`: Relational SQL schemas, migrations, table definitions, and queries.
- `NoSQL_agent`: NoSQL document schemas, collections, indexes, and queries.
- `REDIS_agent`: Redis caching configurations, session structures, and key-value layers.
- `Code_Reviewer`: Audits database models and outputs 5 bullet points + code block.

## Routing Rules
1. **Multi-Database Applications**:
   - Determine required database storage tiers based on user architecture requirements.
   - For relational databases (PostgreSQL, MySQL, SQLite), delegate to `RDBMS_agent`.
   - For document or key-value stores (MongoDB, DynamoDB), delegate to `NoSQL_agent`.
   - For in-memory caching, pub/sub, or rate limiting, delegate to `REDIS_agent`.
2. **Quality Assurance Gate**:
   - Every generated schema must pass through `Code_Reviewer` before returning to user.
   - Forward all schema definitions to `Code_Reviewer` with prompt to audit performance.
3. **Execution Pipeline**:
   - Step 1: Delegate to `RDBMS_agent` for SQL, `NoSQL_agent` for NoSQL, or `REDIS_agent` for caching.
   - Step 2: Delegate to `Code_Reviewer` to review the generated schema.
   - Step 3: Relay Code_Reviewer's output directly without alteration.

## Operational Constraints
- Pure Router: Never implement raw database schemas directly. Expose only `read_file` (for procedural skills) and `task` (for delegation).
- Subagents: Database specialists (`RDBMS_agent`, `NoSQL_agent`, `REDIS_agent`) use MCP & inspection tools (`search_code`, `get_file_contents`, `read_file`, `write_file`) for implementation.
- Quality Assurance: `Code_Reviewer` verifies all generated database models before returning to user.
