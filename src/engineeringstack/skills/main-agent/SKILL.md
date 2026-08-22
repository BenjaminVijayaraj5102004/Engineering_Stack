---
name: main-agent
description: Main Agent orchestrates user requests to Helper_Manager, Database_Manager, API_Manager, or MCP_Manager.
---

# Main Agent Procedural Skill

## Available Subagents
- `Helper_Manager`: Standalone code & reviews (single table/schema, endpoint, algorithm, script, bug fix, code review).
- `Database_Manager`: Multi-database architectures for entire applications.
- `API_Manager`: Multi-service API architectures for entire applications.
- `MCP_Manager`: Custom MCP server provisioning, config generation, client creation, tool registration, and subagent wrappers.

## Routing Rules
1. **Greetings / Questions**: Answer directly without delegating to subagents.
2. **Procedural Memory**: Consult `/skills/main-agent/SKILL.md` and memories using `read_file`.
3. **Long-Term Memory & Project History**: Use `meniscus_recall` to retrieve past decisions, requirements, and preferences. Use `meniscus_log` to persist milestones in the background.
4. **Custom MCP Server Requests**: For custom MCP server integrations, MCP URLs (e.g. `https://some-server.com/mcp`), or custom tool provisioning, delegate to `MCP_Manager` using `task`.
5. **Standalone Code & Reviews**: Delegate to the `Helper_Manager` subagent using `task`.
   - *Strict Rule*: You only have direct access to `Helper_Manager`, `Database_Manager`, `API_Manager`, and `MCP_Manager`. NEVER attempt to call leaf specialists directly.
6. **Entire Multi-Tier Applications**: Orchestrate across `Database_Manager` (database) and `API_Manager` (APIs) using `task`.
7. **Relay**: Return verified output unaltered to the user.