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

## 2. Watching & Monitoring
Automatically track changes and keep your code graph up-to-date.

| Command | Arguments | Description |
| :--- | :--- | :--- |
| **`cgc watch`** | `[path]` | Watches a directory for file changes and automatically re-indexes. Runs in foreground. Default path is current directory. <br> *(Alias: `cgc w`)* |
| **`cgc unwatch`** | `<path>` | Stops watching a previously watched directory. (Primarily for MCP mode) |
| **`cgc watching`** | None | Lists all directories currently being watched for changes. (Primarily for MCP mode) |

## 3. Code Analysis
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
| **`cgc analyze overrides`** | `<class>` <br> `--file` | Shows methods that override parent class methods. |
| **`cgc analyze variable`** | `<var_name>` <br> `--file` | Analyzes variable usage and assignments. |

## 4. Discovery & Search
Find code elements when you don't know the exact structure.

| Command | Arguments | Description |
| :--- | :--- | :--- |
| **`cgc find name`** | `<name>` <br> `--type` | Finds code elements (Class, Function) by their **exact** name. |
| **`cgc find pattern`** | `<pattern>` <br> `--case-sensitive` | Finds elements using fuzzy substring matching (e.g. "User" finds "UserHelper"). |
| **`cgc find type`** | `<type>` <br> `--limit` | Lists all nodes of a specific type (e.g. `function`, `class`, `module`). |
| **`cgc find variable`** | `<name>` <br> `--file` | Finds variables by name across the codebase. |
| **`cgc find content`** | `<text>` <br> `--case-sensitive` | Searches for text content within code (docstrings, comments). |
| **`cgc find decorator`** | `<name>` | Finds all functions/classes with a specific decorator. |
| **`cgc find argument`** | `<name>` | Finds all functions that have a specific argument name. |

## 5. Configuration & Setup
Manage your environment and database connections.

| Command | Arguments | Description |
| :--- | :--- | :--- |
| **`cgc mcp setup`** | None | Configures your IDE/MCP Client. Creates `mcp.json`. <br> *(Alias: `cgc m`)* |
| **`cgc neo4j setup`** | None | Wizard to configure a Neo4j connection. <br> *(Alias: `cgc n`)* |
| **`cgc config show`** | None | Displays current configuration values. |
| **`cgc config set`** | `<key> <value>` | Sets a config value (e.g. `DEFAULT_DATABASE`). |
| **`cgc config reset`** | None | Resets configuration to defaults. |
| **`cgc config db`** | `<backend>` | Quick switch between `neo4j` and `falkordb`. |

## 6. Bundle Management
Create, load, and share pre-indexed graph snapshots.

| Command | Arguments | Description |
| :--- | :--- | :--- |
| **`cgc bundle export`** | `<output.cgc>` <br> `--repo` <br> `--no-stats` | Exports the current graph to a portable .cgc bundle file. Use `--repo` to export a specific repository. <br> *(Alias: `cgc export`)* |
| **`cgc bundle import`** | `<bundle.cgc>` <br> `--clear` | Imports a .cgc bundle into the current database. Use `--clear` to wipe existing data first. |
| **`cgc bundle load`** | `<name>` <br> `--clear` | Loads a bundle (downloads from registry if not found locally, then imports). <br> *(Alias: `cgc load`)* |

## 7. Bundle Registry
Browse, search, and download pre-indexed bundles.

| Command | Arguments | Description |
| :--- | :--- | :--- |
| **`cgc registry list`** | `--verbose` | Lists all available bundles in the registry (weekly + on-demand). Use `-v` for download URLs. |
| **`cgc registry search`** | `<query>` | Searches for bundles by name, repository, or description. |
| **`cgc registry download`** | `<name>` <br> `--output` <br> `--load` | Downloads a bundle from the registry. Use `-o` for custom directory, `-l` to auto-load. |
| **`cgc registry request`** | `<github-url>` <br> `--wait` | Requests on-demand generation of a bundle for any GitHub repository. |

## 8. Utilities & Runtime
Helper commands for developers and the MCP server.

| Command | Arguments | Description |
| :--- | :--- | :--- |
| **`cgc doctor`** | None | Runs system diagnostics (DB connection, dependencies, permissions). |
| **`cgc visualize`** | `[query]` | Generates a link to open the Neo4j Browser. <br> *(Alias: `cgc v`)* |
| **`cgc query`** | `<query>` | Executes a raw Cypher query directly against the DB. |
| **`cgc mcp start`** | None | Starts the MCP Server (used by IDEs). |
| **`cgc mcp tools`** | None | Lists all available MCP tools supported by the server. |
| **`cgc start`** | None | **Deprecated**. Use `cgc mcp start` instead. |
| **`cgc help`** | None | Shows the main help message with all commands. |
| **`cgc version`** | None | Shows the application version. |

## Global Options

These options work with any command:

| Option | Short | Description |
| :--- | :--- | :--- |
| `--database` | `-db` | Temporarily override database backend (`falkordb` or `neo4j`) for any command. |
| `--visual` / `--viz` | `-V` | Show results as interactive graph visualization in browser (for analyze/find commands). |
| `--help` | `-h` | Show help for any command. |
| `--version` | `-v` | Show version (root level only). |

## Shortcuts

Quick aliases for common commands:

| Shortcut | Equivalent | Description |
| :--- | :--- | :--- |
| `cgc m` | `cgc mcp setup` | MCP client setup |
| `cgc n` | `cgc neo4j setup` | Neo4j database setup |
| `cgc i` | `cgc index` | Index repository |
| `cgc ls` | `cgc list` | List repositories |
| `cgc rm` | `cgc delete` | Delete repository |
| `cgc v` | `cgc visualize` | Visualize graph |
| `cgc w` | `cgc watch` | Watch directory |

## Examples

### Basic Workflow
```bash
# Index your project
cgc index .

# List what's indexed
cgc list

# Find a function
cgc find name MyFunction

# Analyze who calls it
cgc analyze callers MyFunction
```

### Bundle Workflow
```bash
# Export your indexed graph
cgc bundle export my-project.cgc --repo .

# List available bundles
cgc registry list

# Download and load a bundle
cgc load flask

# Search for bundles
cgc registry search web
```

### Advanced Analysis
```bash
# Find complex functions
cgc analyze complexity --threshold 15

# Find call chain between functions
cgc analyze chain start_func end_func --depth 10

# Visualize results in browser
cgc analyze tree MyClass --visual
```