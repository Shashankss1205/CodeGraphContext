# Comprehensive Guide to CodeGraphContext CLI


Here is the **complete list** of all CLI commands available in `CodeGraphContext`, categorized by workflow scenario.

## Global Flags

These flags can be used with any command:

| Flag | Aliases | Description |
| :--- | :--- | :--- |
| **`--visual`** | `--viz`, `-V` | Shows results as an interactive graph visualization in your browser. Works with analyze, find, and query commands. |
| **`--database`** | `-d` | Temporarily override the database backend (`falkordb` or `neo4j`) for any command. |
| **`--version`** | `-v` | Show version and exit. |
| **`--help`** | `-h` | Show help and exit. |

> **Note:** The visual flag uses uppercase `-V` to avoid conflict with `-v` which is reserved for `--version`.

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
Automatically track changes and keep your code graph up-to-date when you code.

| Command | Arguments | Description |
| :--- | :--- | :--- |
| **`cgc watch`** | `[path]` | Watches a directory for file changes and automatically re-indexes. Runs in foreground. Default path is current directory. <br> *(Alias: `cgc w`)* |
| **`cgc unwatch`** | `<path>` | Stops watching a previously watched directory. (Primarily for MCP mode) |
| **`cgc watching`** | None | Lists all directories currently being watched for changes. (Primarily for MCP mode) |

## 3. Code Analysis
Understand the structure, quality, and relationships of your code.

| Command | Arguments | Description |
| :--- | :--- | :--- |
| **`cgc analyze calls`** | `<func_name>` <br> `--file` <br> `--visual` | Shows **outgoing** calls: what functions does this function call? Use `--visual` or `-V` for graph view. |
| **`cgc analyze callers`** | `<func_name>` <br> `--file` <br> `--visual` | Shows **incoming** calls: who calls this function? Use `--visual` or `-V` for graph view. |
| **`cgc analyze chain`** | `<start> <end>` <br> `--depth` <br> `--visual` | Finds the call path between two functions. Default depth is 5. Use `--visual` or `-V` for graph view. |
| **`cgc analyze deps`** | `<module>` <br> `--no-external` <br> `--visual` | Inspects dependencies (imports and importers) for a module. Use `--visual` or `-V` for graph view. |
| **`cgc analyze tree`** | `<class_name>` <br> `--file` <br> `--visual` | Visualizes the Class Inheritance hierarchy for a given class. Use `--visual` or `-V` for graph view. |
| **`cgc analyze complexity`**| `[path]` <br> `--threshold` <br> `--limit` | Lists functions with high Cyclomatic Complexity. Default threshold: 10. |
| **`cgc analyze dead-code`** | `--exclude` | Finds potentially unused functions (0 callers). Use `--exclude` for decorators. |
| **`cgc analyze overrides`** | `<func_name>` <br> `--visual` | Finds all implementations of a function across different classes. Use `--visual` or `-V` for graph view. |

## 4. Discovery & Search
Find code elements when you don't know the exact structure.

| Command | Arguments | Description |
| :--- | :--- | :--- |
| **`cgc find name`** | `<name>` <br> `--type` <br> `--visual` | Finds code elements (Class, Function) by their **exact** name. Use `--visual` or `-V` for graph view. |
| **`cgc find pattern`** | `<pattern>` <br> `--case-sensitive` <br> `--visual` | Finds elements using fuzzy substring matching (e.g. "User" finds "UserHelper"). Use `--visual` or `-V` for graph view. |
| **`cgc find type`** | `<type>` <br> `--limit` <br> `--visual` | Lists all nodes of a specific type (e.g. `function`, `class`, `module`). Use `--visual` or `-V` for graph view. |

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
Create and load pre-indexed graph snapshots for instant context.

| Command | Arguments | Description |
| :--- | :--- | :--- |
| **`cgc bundle export`** | `<output>` <br> `--repo` <br> `--no-stats` | Exports the graph to a portable .cgc bundle file. Use `--repo` to export a specific repository. <br> *(Alias: `cgc export`)* |
| **`cgc bundle import`** | `<bundle>` <br> `--clear` | Imports a .cgc bundle into the database. Use `--clear` to replace existing data. |
| **`cgc bundle load`** | `<bundle>` <br> `--clear` | Loads a bundle (downloads if needed). <br> *(Alias: `cgc load`)* |

## 7. Utilities & Runtime
Helper commands for developers and the MCP server.

| Command | Arguments | Description |
| :--- | :--- | :--- |
| **`cgc doctor`** | None | Runs system diagnostics (DB connection, dependencies, permissions). |
| **`cgc visualize`** | `[query]` | Generates a link to open the Neo4j Browser. <br> *(Alias: `cgc v`)* |
| **`cgc query`** | `<query>` <br> `--visual` | Executes a raw Cypher query directly against the DB. Use `--visual` or `-V` for graph view. |
| **`cgc mcp start`** | None | Starts the MCP Server (used by IDEs). |
| **`cgc mcp tools`** | None | Lists all available MCP tools supported by the server. |
| **`cgc start`** | None | **Deprecated**. Use `cgc mcp start` instead. |

---

## Common Scenarios & Combinations

### Scenario A: Onboarding a New Repository
1.  **Index the code:**
    ```bash
    cgc index .
    ```
2.  **Verify status:**
    ```bash
    cgc doctor
    ```
3.  **Check stats:**
    ```bash
    cgc stats
    ```

### Scenario B: Refactoring Legacy Code
1.  **Find complex functions:**
    ```bash
    cgc analyze complexity --threshold 15
    ```
2.  **Find unused code:**
    ```bash
    cgc analyze dead-code --exclude "route,task"
    ```
3.  **Check dependencies:**
    ```bash
    cgc analyze deps target_module --no-external
    ```

### Scenario C: Bug Hunting
1.  **Search for relevant code:**
    ```bash
    cgc find pattern "AuthValidator"
    ```
2.  **Trace execution:**
    ```bash
    cgc analyze callers validate_auth
    ```
3.  **Find full path:**
    ```bash
    cgc analyze chain "main" "validate_auth" --depth 10
    ```

### Scenario D: Database Switching
1.  **Switch to Neo4j:**
    ```bash
    cgc config db neo4j
    ```
2.  **Configure credentials:**
    ```bash
    cgc neo4j setup
    ```
3.  **Verify connection:**
    ```bash
    cgc doctor
    ```

### Scenario E: Setting Up on Different Operating Systems

**Unix/Linux/macOS (Python 3.12+):**
```bash
# FalkorDB Lite is already configured as default
pip install codegraphcontext
cgc mcp setup  # Configure your IDE
cgc index .    # Start indexing
```

**Windows:**
```bash
# Option 1: Use WSL (Recommended)
wsl --install
# Then follow Unix instructions above

# Option 2: Use Neo4j with Docker
pip install codegraphcontext
cgc neo4j setup  # Choose Docker option
cgc mcp setup    # Configure your IDE
cgc index .      # Start indexing

# Option 3: Use Neo4j native installation
pip install codegraphcontext
cgc neo4j setup  # Choose native installation
cgc mcp setup    # Configure your IDE
cgc index .      # Start indexing
```

### Scenario F: Live Development with Auto-Update
1.  **Start watching your project:**
    ```bash
    cgc watch .
    ```
2.  **Open a new terminal and continue coding**
    - The watcher runs in the foreground
    - Changes are automatically indexed as you save files
3.  **Stop watching when done:**
    - Press `Ctrl+C` in the watch terminal
    
**💡 Tip:** This is perfect for active development sessions where you want your AI assistant to always have the latest code context!

### Scenario G: Visual Graph Exploration
Use the `--visual` flag (or `-V`) to see results as interactive graphs in your browser.

1.  **Visualize function calls:**
    ```bash
    cgc analyze calls process_data --visual
    # or use the short form
    cgc analyze calls process_data -V
    ```

2.  **Visualize call chain between functions:**
    ```bash
    cgc analyze chain main handle_request --visual
    ```

3.  **Visualize class inheritance:**
    ```bash
    cgc analyze tree MyBaseClass --visual
    ```

4.  **Visualize module dependencies:**
    ```bash
    cgc analyze deps mymodule --visual
    ```

5.  **Visualize search results:**
    ```bash
    cgc find pattern "Controller" --visual
    ```

6.  **Visualize Cypher query results:**
    ```bash
    cgc query "MATCH (n:Function)-[r:CALLS]->(m:Function) RETURN n,r,m LIMIT 50" --visual
    ```

7.  **Use global flag (applies to any command):**
    ```bash
    cgc -V analyze callers my_function
    ```

**💡 Tip:** The visualizations are interactive! Drag to pan, scroll to zoom, and click on nodes to highlight connections.

**📍 Output:** Visualization HTML files are saved to `~/.codegraphcontext/visualizations/` and automatically opened in your default browser.
### Scenario G: Using Pre-indexed Bundles
1.  **Download a pre-indexed bundle:**
    ```bash
    # Download from GitHub Releases
    wget https://github.com/Shashankss1205/CodeGraphContext/releases/latest/download/numpy-1.26.4.cgc
    ```
2.  **Load it instantly:**
    ```bash
    cgc load numpy-1.26.4.cgc
    ```
3.  **Start querying immediately:**
    ```bash
    cgc find name linalg
    cgc analyze deps numpy.linalg
    ```

**💡 Tip:** Bundles let you skip the indexing step entirely! Perfect for exploring famous libraries or sharing pre-analyzed codebases.

### Scenario H: Creating Your Own Bundle
1.  **Index your project:**
    ```bash
    cgc index /path/to/my-project
    ```
2.  **Export to bundle:**
    ```bash
    cgc export my-project.cgc --repo /path/to/my-project
    ```
3.  **Share with your team:**
    ```bash
    # Upload to GitHub Releases, S3, or share directly
    # Others can load it with:
    cgc load my-project.cgc
    ```

**💡 Tip:** Great for onboarding new team members or sharing analysis results!
