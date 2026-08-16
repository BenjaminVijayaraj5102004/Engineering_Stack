# Routing Rules

| Category | Indicators | Target Subagent |
| :--- | :--- | :--- |
| **Greeting / Question** | `hi`, `hello`, `who are you` | None (Direct Answer) |
| **Standalone Code / Single Component** | `create a table`, `mongoDB table`, `schema`, `POST route`, `algorithm`, `function`, `script`, `fix bug` | `Helper_Manager` |
| **Code Review / Audit** | `review this`, `audit`, `security check` | `Helper_Manager` |
| **Entire Application / Full System** | `e-commerce site`, `full todo app with db & api`, `entire product backend` | `Database_Manager` + `API_Manager` |
