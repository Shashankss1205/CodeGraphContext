# CLI Reference

The CodeGraphContext CLI provides a comprehensive command-line interface to manage the server, index your code, search, analyzing and interact with the code graph.

## 1. Project Management
Use these commands to manage the repositories in your code graph.

| Command | Arguments | Description |
| :--- | :--- | :--- |
| **`cgc index`** | `[path]` <br> `--force` | Adds a repository to the graph. Default path is current directory. Use `--force` to re-index from scratch. <br> *(Alias: `cgc i`)* |
| **`cgc list`** | None | Lists all repositories currently indexed in the database. <br> *(Alias: `cgc ls`)* |
| **`cgc delete`** | `[path]` <br> `--all` | Removes a repository from the graph. Use `--all` to wipe everything. <br> *(Alias: `cgc rm`)* |
| **`cgc stats`** | `[path]` | Shows indexing statistics (node counts) for the DB or a specific repo. |
| **`cgc clean`** | None | Removes orphaned nodes and cleans up the database. |
| **`cgc add-package`** | `<name> <lang>` | Manually adds an external package node (e.g., `cgc add-package requests python`). |

## 2. Code Analysis
Understand the structure, quality, and relationships of your code.

| Command | Arguments | Description |
| :--- | :--- | :--- |
| **`cgc analyze calls`** | `<func_name>` <br> `--file` | Shows **outgoing** calls: what functions does this function call? |
| **`cgc analyze callers`** | `<func_name>` <br> `--file` | Shows **incoming** calls: who calls this function? |
| **`cgc analyze chain`** | `<start> <end>` <br> `--depth` | Finds the call path between two functions. Default depth is 5. |
| **`cgc analyze deps`** | `<module>` <br> `--no-external` | Inspects dependencies (imports and importers) for a module. |
| **`cgc analyze tree`** | `<class_name>` <br> `--file` | Visualizes the Class Inheritance hierarchy for a given class. |
| **`cgc analyze complexity`**| `[path]` <br> `--threshold` <br> `--limit` | Lists functions with high Cyclomatic Complexity. Default threshold: 10. |
| **`cgc analyze dead-code`** | `--exclude` | Finds potentially unused functions (0 callers). Use `--exclude` for decorators. |

## 3. Discovery & Search
Find code elements when you don't know the exact structure.

| Command | Arguments | Description |
| :--- | :--- | :--- |
| **`cgc find name`** | `<name>` <br> `--type` | Finds code elements (Class, Function) by their **exact** name. |
| **`cgc find pattern`** | `<pattern>` <br> `--case-sensitive` | Finds elements using fuzzy substring matching (e.g. "User" finds "UserHelper"). |
| **`cgc find type`** | `<type>` <br> `--limit` | Lists all nodes of a specific type (e.g. `function`, `class`, `module`). |

## 4. Configuration & Setup
Manage your environment and database connections.

| Command | Arguments | Description |
| :--- | :--- | :--- |
| **`cgc mcp setup`** | None | Configures your IDE/MCP Client. Creates `mcp.json`. <br> *(Alias: `cgc m`)* |
| **`cgc neo4j setup`** | None | Wizard to configure a Neo4j connection. <br> *(Alias: `cgc n`)* |
| **`cgc config show`** | None | Displays current configuration values. |
| **`cgc config set`** | `<key> <value>` | Sets a config value (e.g. `DEFAULT_DATABASE`). |
| **`cgc config reset`** | None | Resets configuration to defaults. |
| **`cgc config db`** | `<backend>` | Quick switch between `neo4j` and `falkordb`. |

## 5. Utilities & Runtime
Helper commands for developers and the MCP server.

| Command | Arguments | Description |
| :--- | :--- | :--- |
| **`cgc doctor`** | None | Runs system diagnostics (DB connection, dependencies, permissions). |
| **`cgc visualize`** | `[query]` | Generates a link to open the Neo4j Browser. <br> *(Alias: `cgc v`)* |
| **`cgc query`** | `<query>` | Executes a raw Cypher query directly against the DB. |
| **`cgc mcp start`** | None | Starts the MCP Server (used by IDEs). |
| **`cgc mcp tools`** | None | Lists all available MCP tools supported by the server. |
| **`cgc start`** | None | **Deprecated**. Use `cgc mcp start` instead. |