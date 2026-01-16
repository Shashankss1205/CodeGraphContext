# Welcome to CodeGraphContext

This is the official documentation for CodeGraphContext.

---

# CodeGraphContext

<!-- ====== Project stats ====== -->
[![Stars](https://img.shields.io/github/stars/CodeGraphContext/CodeGraphContext?logo=github)](https://github.com/CodeGraphContext/CodeGraphContext/stargazers)
[![Forks](https://img.shields.io/github/forks/CodeGraphContext/CodeGraphContext?logo=github)](https://github.com/CodeGraphContext/CodeGraphContext/network/members)
[![Open Issues](https://img.shields.io/github/issues-raw/CodeGraphContext/CodeGraphContext?logo=github)](https://github.com/CodeGraphContext/CodeGraphContext/issues)
[![Open PRs](https://img.shields.io/github/issues-pr/CodeGraphContext/CodeGraphContext?logo=github)](https://github.com/CodeGraphContext/CodeGraphContext/pulls)
[![Closed PRs](https://img.shields.io/github/issues-pr-closed/CodeGraphContext/CodeGraphContext?logo=github&color=lightgrey)](https://github.com/CodeGraphContext/CodeGraphContext/pulls?q=is%3Apr+is%3Aclosed)
[![Contributors](https://img.shields.io/github/contributors/CodeGraphContext/CodeGraphContext?logo=github)](https://github.com/CodeGraphContext/CodeGraphContext/graphs/contributors)
[![Languages](https://img.shields.io/github/languages/count/CodeGraphContext/CodeGraphContext?logo=github)](https://github.com/CodeGraphContext/CodeGraphContext)
[![Build Status](https://github.com/CodeGraphContext/CodeGraphContext/actions/workflows/test.yml/badge.svg)](https://github.com/CodeGraphContext/CodeGraphContext/actions/workflows/test.yml)
[![Build Status](https://github.com/CodeGraphContext/CodeGraphContext/actions/workflows/e2e-tests.yml/badge.svg)](https://github.com/CodeGraphContext/CodeGraphContext/actions/workflows/e2e-tests.yml)
[![PyPI version](https://img.shields.io/pypi/v/codegraphcontext?)](https://pypi.org/project/codegraphcontext/)
[![PyPI downloads](https://img.shields.io/pypi/dm/codegraphcontext?)](https://pypi.org/project/codegraphcontext/)
[![License](https://img.shields.io/github/license/CodeGraphContext/CodeGraphContext?)](license.md)
[![Website](https://img.shields.io/badge/website-up-brightgreen?)](http://codegraphcontext.vercel.app/)
[![YouTube](https://img.shields.io/badge/YouTube-Watch%20Demo-red?logo=youtube)](https://youtu.be/KYYSdxhg1xU)
[![Discord](https://img.shields.io/badge/Discord-Join%20Chat-7289da?logo=discord&logoColor=white)](https://discord.gg/dR4QY32uYQ)



A powerful **MCP server** and **CLI toolkit** that indexes local code into a graph database to provide context to AI assistants and developers. Use it as a standalone CLI for comprehensive code analysis or connect it to your favorite AI IDE via MCP for AI-powered code understanding.

### Indexing a codebase (CLI or MCP)
![Indexing using an MCP client](images/Indexing.gif)

### Using the MCP server
![Using the MCP server](images/Usecase.gif)

## Project Details
- **Version:** 0.1.15
- **Authors:** Shashank Shekhar Singh <shashankshekharsingh1205@gmail.com>
- **License:** MIT License (See [LICENSE](license.md) for details)
- **Website:** [CodeGraphContext](http://codegraphcontext.vercel.app/)

## Star History
[![Star History Chart](https://api.star-history.com/svg?repos=CodeGraphContext/CodeGraphContext&type=Date)](https://www.star-history.com/#CodeGraphContext/CodeGraphContext&Date)

## Features

-   **Code Indexing:** Analyzes code and builds a knowledge graph of its components.
-   **Relationship Analysis:** Query for callers, callees, class hierarchies, call chains and more.
-   **Live File Watching:** Watch directories for changes and automatically update the graph in real-time (`cgc watch`).
-   **Interactive Setup:** A user-friendly command-line wizard for easy setup.
-   **Dual Mode:** Works as a standalone **CLI toolkit** for developers and as an **MCP server** for AI agents.
-   **Multi-Language Support:** Full support for 11 programming languages.
-   **Flexible Database Backend:** FalkorDB Lite (default, inbuilt for Unix) or Neo4j (all platforms via Docker/WSL/native).
-   **File Exclusion:** Supports `.cgcignore` files to exclude specific files and directories from indexing.


## Used By

CodeGraphContext is already being explored by developers and projects for:

- **Static code analysis in AI assistants**
- **Graph-based visualization of projects**
- **Dead code and complexity detection**

If you’re using CodeGraphContext in your project, feel free to open a PR and add it here! 🚀

## Dependencies

- `neo4j>=5.15.0`
- `watchdog>=3.0.0`
- `requests>=2.31.0`
- `stdlibs>=2023.11.18`
- `typer[all]>=0.9.0`
- `rich>=13.7.0`
- `inquirerpy>=0.3.4`
- `python-dotenv>=1.0.0`
- `tree-sitter==0.20.4`
- `tree-sitter-languages==1.10.2`

## Getting Started

1.  **Install:** `pip install codegraphcontext`
2.  **Configure Your Environment:**
    Run the interactive setup wizard to connect to your database and configure your IDE:
    ```bash
    cgc mcp setup
    ```
    This ensures your IDE is configured. To configure a Neo4j database, use `cgc neo4j setup`.
    The wizard helps you with:
    -   **Database Connection:**
        -   **Docker (Recommended):** Automatically sets up a local Neo4j instance.
        -   **Linux Binary:** Installs Neo4j directly on Debian-based systems.
        -   **Hosted:** Connects to a remote Neo4j database like AuraDB.
    -   **IDE Integration:**
        -   Automatically configures tools like VS Code, Cursor, Gemini CLI, and more.
        -   Generates the necessary `mcp.json` and `.env` files for you.

3.  **Start:** `cgc mcp start`

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

## Social Coverage

-   **Youtube:** [https://www.youtube.com/watch?v=KYYSdxhg1xU](https://www.youtube.com/watch?v=KYYSdxhg1xU)
-   **Blog:** [https://medium.com/@shashankshekharsingh1205/building-codegraphcontext-my-end-term-journey-in-summer-of-bitcoin-2025-422c9a4dc87e](https://medium.com/@shashankshekharsingh1205/building-codegraphcontext-my-end-term-journey-in-summer-of-bitcoin-2025-422c9a4dc87e)
-   **Twitter:** [https://x.com/braidpool/status/1968683721625637203](https://x.com/braidpool/status/1968683721625637203)
-   **PulseMCP:** [https://www.pulsemcp.com/servers/codegraphcontext](https://www.pulsemcp.com/servers/codegraphcontext)
-   **MCPMarket:** [https://mcpmarket.com/server/codegraphcontext](https://mcpmarket.com/server/codegraphcontext)
-   **Playbooks:** [https://playbooks.com/mcp/codegraphcontext](https://playbooks.com/mcp/codegraphcontext)
-   **MCPHunt:** [https://mcp-hunt.com/mcp/server/codegraphcontext](https://mcp-hunt.com/mcp/server/codegraphcontext)
-   **StackerNews:** [https://stacker.news/items/1227191](https://stacker.news/items/1227191)
-   **Glama.ai:** [https://glama.ai/mcp/servers/@CodeGraphContext/CodeGraphContext/blob/a346d340d8f705ce93626b4b322dd0e2823ba46b/src/codegraphcontext/core/jobs.py](https://glama.ai/mcp/servers/@CodeGraphContext/CodeGraphContext/blob/a346d340d8f705ce93626b4b322dd0e2823ba46b/src/codegraphcontext/core/jobs.py)

## Contributing

Contributions are welcome! 🎉  
Please see our [CONTRIBUTING.md](contributing.md) for detailed guidelines.
If you have ideas for new features, integrations, or improvements, open an [issue](https://github.com/CodeGraphContext/CodeGraphContext/issues) or submit a Pull Request.

Join discussions and help shape the future of CodeGraphContext.
