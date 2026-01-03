# CodeGraphContext

<!-- ====== Project stats ====== -->
[![Stars](https://img.shields.io/github/stars/Shashankss1205/CodeGraphContext?logo=github)](https://github.com/Shashankss1205/CodeGraphContext/stargazers)
[![Forks](https://img.shields.io/github/forks/Shashankss1205/CodeGraphContext?logo=github)](https://github.com/Shashankss1205/CodeGraphContext/network/members)
[![Open Issues](https://img.shields.io/github/issues-raw/Shashankss1205/CodeGraphContext?logo=github)](https://github.com/Shashankss1205/CodeGraphContext/issues)
[![Open PRs](https://img.shields.io/github/issues-pr/Shashankss1205/CodeGraphContext?logo=github)](https://github.com/Shashankss1205/CodeGraphContext/pulls)
[![Closed PRs](https://img.shields.io/github/issues-pr-closed/Shashankss1205/CodeGraphContext?logo=github&color=lightgrey)](https://github.com/Shashankss1205/CodeGraphContext/pulls?q=is%3Apr+is%3Aclosed)
[![Contributors](https://img.shields.io/github/contributors/Shashankss1205/CodeGraphContext?logo=github)](https://github.com/Shashankss1205/CodeGraphContext/graphs/contributors)
[![Languages](https://img.shields.io/github/languages/count/Shashankss1205/CodeGraphContext?logo=github)](https://github.com/Shashankss1205/CodeGraphContext)
[![Build Status](https://github.com/Shashankss1205/CodeGraphContext/actions/workflows/test.yml/badge.svg)](https://github.com/Shashankss1205/CodeGraphContext/actions/workflows/test.yml)
[![Build Status](https://github.com/Shashankss1205/CodeGraphContext/actions/workflows/e2e-tests.yml/badge.svg)](https://github.com/Shashankss1205/CodeGraphContext/actions/workflows/e2e-tests.yml)
[![PyPI version](https://img.shields.io/pypi/v/codegraphcontext?)](https://pypi.org/project/codegraphcontext/)
[![PyPI downloads](https://img.shields.io/pypi/dm/codegraphcontext?)](https://pypi.org/project/codegraphcontext/)
[![License](https://img.shields.io/github/license/Shashankss1205/CodeGraphContext?)](LICENSE)
[![Website](https://img.shields.io/badge/website-up-brightgreen?)](http://codegraphcontext.vercel.app/)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://shashankss1205.github.io/CodeGraphContext/)
[![YouTube](https://img.shields.io/badge/YouTube-Watch%20Demo-red?logo=youtube)](https://youtu.be/KYYSdxhg1xU)
[![Discord](https://img.shields.io/badge/Discord-Join%20Chat-7289da?logo=discord&logoColor=white)](https://discord.gg/dR4QY32uYQ)



A powerful **MCP server** and **CLI toolkit** that indexes local code into a graph database to provide context to AI assistants and developers. Use it as a standalone CLI for comprehensive code analysis or connect it to your favorite AI IDE via MCP for AI-powered code understanding.

### Indexing a codebase
![Indexing using an MCP client](https://github.com/Shashankss1205/CodeGraphContext/blob/main/images/Indexing.gif)

### Using the MCP server
![Using the MCP server](https://github.com/Shashankss1205/CodeGraphContext/blob/main/images/Usecase.gif)

## Project Details
- **Version:** 0.1.27
- **Authors:** Shashank Shekhar Singh <shashankshekharsingh1205@gmail.com>
- **License:** MIT License (See [LICENSE](LICENSE) for details)
- **Website:** [CodeGraphContext](http://codegraphcontext.vercel.app/)

## Star History
[![Star History Chart](https://api.star-history.com/svg?repos=Shashankss1205/CodeGraphContext&type=Date)](https://www.star-history.com/#Shashankss1205/CodeGraphContext&Date)

## Features

-   **Code Indexing:** Analyzes code and builds a knowledge graph of its components.
-   **Relationship Analysis:** Query for callers, callees, class hierarchies, call chains and more.
-   **Live File Watching:** Watch directories for changes and automatically update the graph in real-time (`cgc watch`).
-   **Interactive Setup:** A user-friendly command-line wizard for easy setup.
-   **Dual Mode:** Works as a standalone **CLI toolkit** for developers and as an **MCP server** for AI agents.
-   **Multi-Language Support:** Full support for 11 programming languages.
-   **Flexible Database Backend:** FalkorDB Lite (default, inbuilt for Unix and through WSL for Windows) or Neo4j (all platforms via Docker/native).


## Supported Programming Languages

CodeGraphContext provides comprehensive parsing and analysis for the following languages:

- **Python** (`.py`) - Including Jupyter notebooks (`.ipynb`)
- **JavaScript** (`.js`)
- **TypeScript** (`.ts`)
- **Java** (`.java`)
- **C** (`.c`, `.h`)
- **C++** (`.cpp`, `.cc`, `.cxx`, `.hpp`, `.hxx`)
- **C#** (`.cs`) - Full support for classes, methods, namespaces, and inheritance
- **Go** (`.go`)
- **Rust** (`.rs`)
- **Ruby** (`.rb`)
- **PHP** (`.php`)
- **Kotlin** (`.kt`) - Full support for classes, objects, companions, functions, and coroutines

Each language parser extracts functions, classes, methods, parameters, inheritance relationships, function calls, and imports to build a comprehensive code graph.

## Database Options

CodeGraphContext supports two graph database backends:

### FalkorDB Lite (Default for Unix/Linux/macOS)
- **Lightweight** in-memory graph database
- **No external dependencies** - runs entirely in-process
- **Inbuilt and enabled by default** for Unix-based systems (Linux, macOS)
- Available for **Python 3.12+** only
- Perfect for quick testing, development, and most use cases
- Automatically installed and configured when using Python 3.12 or higher on Unix systems

> ⚠️ **Windows Users:**  
> FalkorDB Lite / redislite is **not supported on Windows**.  
> You have three options:  
> 1. Run the project under **WSL (Windows Subsystem for Linux)**: [WSL Install](https://learn.microsoft.com/en-us/windows/wsl/install)  
> 2. Use **Docker** to run the project in a containerized Linux environment  
> 3. Use **Neo4j** directly as your graph database (see below)

### Neo4j (Available for All Platforms)
- **Production-ready** and widely used graph database
- **Available on all operating systems**: Windows, Linux, macOS
- Can be installed via:
  - **Docker** (recommended, cross-platform)
  - **WSL** (for Windows users)
  - **Native installation** (dedicated command for each OS)
- Supports local instances and cloud hosting (Neo4j AuraDB)
- Full Cypher query support for advanced graph analytics
- Recommended for Windows users and production deployments

The `cgc neo4j setup` wizard helps you configure the Neo4j database backend, while FalkorDB Lite is enabled by default on Unix systems with no configuration needed.

## Used By

CodeGraphContext is already being explored by developers and projects for:

- **Static code analysis in AI assistants**
- **Graph-based visualization of projects**
- **Dead code and complexity detection**

If you’re using CodeGraphContext in your project, feel free to open a PR and add it here! 🚀

## Dependencies

- `neo4j>=5.15.0`
- `watchdog>=3.0.0`
- `stdlibs>=2023.11.18`
- `typer[all]>=0.9.0`
- `rich>=13.7.0`
- `inquirerpy>=0.3.4`
- `python-dotenv>=1.0.0`
- `tree-sitter>=0.21.0`
- `tree-sitter-language-pack>=0.6.0`
- `pyyaml`
- `pytest`
- `nbformat`
- `nbconvert>=7.16.6`
- `pathspec>=0.12.1`

**Note:** Python 3.10-3.14 is supported.

## Getting Started

### 📋 Understanding CodeGraphContext Modes

CodeGraphContext operates in **two modes**, and you can use either or both:

#### 🛠️ Mode 1: CLI Toolkit (Standalone)
Use CodeGraphContext as a **powerful command-line toolkit** for code analysis:
- Index and analyze codebases directly from your terminal
- Query code relationships, find dead code, analyze complexity
- Visualize code graphs and dependencies
- Perfect for developers who want direct control via CLI commands

#### 🤖 Mode 2: MCP Server (AI-Powered)
Use CodeGraphContext as an **MCP server** for AI assistants:
- Connect to AI IDEs (VS Code, Cursor, Windsurf, Claude, etc.)
- Let AI agents query your codebase using natural language
- Automatic code understanding and relationship analysis
- Perfect for AI-assisted development workflows

**You can use both modes!** Install once, then use CLI commands directly OR connect to your AI assistant.

---

### Installation (Both Modes)

1.  **Install:** `pip install codegraphcontext`

    <details>
    <summary>⚙️ Troubleshooting: In case, command <code>cgc</code> not found</summary>

    If you encounter <i>"cgc: command not found"</i> after installation, run the PATH fix script:
    
    **Linux/Mac:**
    ```bash
    # Download the fix script
    curl -O https://raw.githubusercontent.com/Shashankss1205/CodeGraphContext/main/scripts/post_install_fix.sh
    
    # Make it executable
    chmod +x post_install_fix.sh
    
    # Run the script
    ./post_install_fix.sh
    
    # Restart your terminal or reload shell config
    source ~/.bashrc  # or ~/.zshrc for zsh users
    ```
    
    **Windows (PowerShell):**
    ```powershell
    # Download the fix script
    curl -O https://raw.githubusercontent.com/Shashankss1205/CodeGraphContext/main/scripts/post_install_fix.sh
    
    # Run with bash (requires Git Bash or WSL)
    bash post_install_fix.sh
    
    # Restart PowerShell or reload profile
    . $PROFILE
    ``` 
    </details>

2.  **Database Setup (Automatic for Unix/WSL)**
    
    - **FalkorDB Lite (Default):** If you're on Unix/Linux/macOS/WSL with Python 3.12+, you're done! FalkorDB Lite is already configured.
    - **Neo4j (Optional/Windows):** To use Neo4j instead, or if you're on Windows without WSL, run: `cgc neo4j setup`

---

### 🛠️ For CLI Toolkit Mode

**Start using immediately with CLI commands:**

```bash
# Index your current directory
cgc index .

# List all indexed repositories
cgc list

# Analyze who calls a function
cgc analyze callers my_function

# Find complex code
cgc analyze complexity --threshold 10

# Find dead code
cgc analyze dead-code

# Watch for live changes (optional)
cgc watch .

# See all commands
cgc help
```

**See the full [CLI Commands Guide](CLI_Commands.md) for all available commands and usage scenarios.**


---

### 🤖 For MCP Server Mode

**Configure your AI assistant to use CodeGraphContext:**

1.  **Setup:** Run the MCP setup wizard to configure your IDE/AI assistant:
    
    ```bash
    cgc mcp setup
    ```
    
    The wizard can automatically detect and configure:
    *   VS Code
    *   Cursor
    *   Windsurf
    *   Claude
    *   Gemini CLI
    *   ChatGPT Codex
    *   Cline
    *   RooCode
    *   Amazon Q Developer

    Upon successful configuration, `cgc mcp setup` will generate and place the necessary configuration files:
    *   It creates an `mcp.json` file in your current directory for reference.
    *   It stores your database credentials securely in `~/.codegraphcontext/.env`.
    *   It updates the settings file of your chosen IDE/CLI (e.g., `.claude.json` or VS Code's `settings.json`).

2.  **Start:** Launch the MCP server:
    
    ```bash
    cgc mcp start
    ```

3.  **Use:** Now interact with your codebase through your AI assistant using natural language! See examples below.

## Ignoring Files (`.cgcignore`)

You can tell CodeGraphContext to ignore specific files and directories by creating a `.cgcignore` file in the root of your project. This file uses the same syntax as `.gitignore`.

**Example `.cgcignore` file:**
```
# Ignore build artifacts
/build/
/dist/

# Ignore dependencies
/node_modules/
/vendor/

# Ignore logs
*.log
```

## MCP Client Configuration

The `cgc mcp setup` command attempts to automatically configure your IDE/CLI. If you choose not to use the automatic setup, or if your tool is not supported, you can configure it manually.

Add the following server configuration to your client's settings file (e.g., VS Code's `settings.json` or `.claude.json`):

```json
{
  "mcpServers": {
    "CodeGraphContext": {
      "command": "cgc",
      "args": [
        "mcp",
        "start"
      ],
      "env": {
        "NEO4J_URI": "YOUR_NEO4J_URI",
        "NEO4J_USERNAME": "YOUR_NEO4J_USERNAME",
        "NEO4J_PASSWORD": "YOUR_NEO4J_PASSWORD"
      },
      "tools": {
        "alwaysAllow": [
          "add_code_to_graph",
          "add_package_to_graph",
          "check_job_status",
          "list_jobs",
          "find_code",
          "analyze_code_relationships",
          "watch_directory",
          "find_dead_code",
          "execute_cypher_query",
          "calculate_cyclomatic_complexity",
          "find_most_complex_functions",
          "list_indexed_repositories",
          "delete_repository",
          "visualize_graph_query",
          "list_watched_paths",
          "unwatch_directory"
        ],
        "disabled": false
      },
      "disabled": false,
      "alwaysAllow": []
    }
  }
}
```

## Natural Language Interaction Examples

Once the server is running, you can interact with it through your AI assistant using plain English. Here are some examples of what you can say:

### Indexing and Watching Files

-   **To index a new project:**
    -   "Please index the code in the `/path/to/my-project` directory."
    OR
    -   "Add the project at `~/dev/my-other-project` to the code graph."


-   **To start watching a directory for live changes:**
    -   "Watch the `/path/to/my-active-project` directory for changes."
    OR
    -   "Keep the code graph updated for the project I'm working on at `~/dev/main-app`."

    When you ask to watch a directory, the system performs two actions at once:
    1.  It kicks off a full scan to index all the code in that directory. This process runs in the background, and you'll receive a `job_id` to track its progress.
    2.  It begins watching the directory for any file changes to keep the graph updated in real-time.

    This means you can start by simply telling the system to watch a directory, and it will handle both the initial indexing and the continuous updates automatically.

### Querying and Understanding Code

-   **Finding where code is defined:**
    -   "Where is the `process_payment` function?"
    -   "Find the `User` class for me."
    -   "Show me any code related to 'database connection'."

-   **Analyzing relationships and impact:**
    -   "What other functions call the `get_user_by_id` function?"
    -   "If I change the `calculate_tax` function, what other parts of the code will be affected?"
    -   "Show me the inheritance hierarchy for the `BaseController` class."
    -   "What methods does the `Order` class have?"

-   **Exploring dependencies:**
    -   "Which files import the `requests` library?"
    -   "Find all implementations of the `render` method."

-   **Advanced Call Chain and Dependency Tracking (Spanning Hundreds of Files):**
    The CodeGraphContext excels at tracing complex execution flows and dependencies across vast codebases. Leveraging the power of graph databases, it can identify direct and indirect callers and callees, even when a function is called through multiple layers of abstraction or across numerous files. This is invaluable for:
    -   **Impact Analysis:** Understand the full ripple effect of a change to a core function.
    -   **Debugging:** Trace the path of execution from an entry point to a specific bug.
    -   **Code Comprehension:** Grasp how different parts of a large system interact.

    -   "Show me the full call chain from the `main` function to `process_data`."
    -   "Find all functions that directly or indirectly call `validate_input`."
    -   "What are all the functions that `initialize_system` eventually calls?"
    -   "Trace the dependencies of the `DatabaseManager` module."

-   **Code Quality and Maintenance:**
    -   "Is there any dead or unused code in this project?"
    -   "Calculate the cyclomatic complexity of the `process_data` function in `src/utils.py`."
    -   "Find the 5 most complex functions in the codebase."

-   **Repository Management:**
    -   "List all currently indexed repositories."
    -   "Delete the indexed repository at `/path/to/old-project`."

## Contributing

Contributions are welcome! 🎉  
Please see our [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.
If you have ideas for new features, integrations, or improvements, open an [issue](https://github.com/Shashankss1205/CodeGraphContext/issues) or submit a Pull Request.

Join discussions and help shape the future of CodeGraphContext.
