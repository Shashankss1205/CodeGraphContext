<div align="center">

# CodeGraphContext

Intelligent code graph context for AI assistants – index, relate, and query your codebase with natural language.

[![Stars](https://img.shields.io/github/stars/Shashankss1205/CodeGraphContext?logo=github)](https://github.com/Shashankss1205/CodeGraphContext/stargazers)
[![Forks](https://img.shields.io/github/forks/Shashankss1205/CodeGraphContext?logo=github)](https://github.com/Shashankss1205/CodeGraphContext/network/members)
[![Open Issues](https://img.shields.io/github/issues-raw/Shashankss1205/CodeGraphContext?logo=github)](https://github.com/Shashankss1205/CodeGraphContext/issues)
[![Build Status](https://github.com/Shashankss1205/CodeGraphContext/actions/workflows/test.yml/badge.svg)](https://github.com/Shashankss1205/CodeGraphContext/actions/workflows/test.yml)
[![PyPI version](https://img.shields.io/pypi/v/codegraphcontext?)](https://pypi.org/project/codegraphcontext/)
[![Downloads](https://img.shields.io/pypi/dm/codegraphcontext?)](https://pypi.org/project/codegraphcontext/)
[![License](https://img.shields.io/github/license/Shashankss1205/CodeGraphContext?)](LICENSE)
[![Website](https://img.shields.io/badge/website-up-brightgreen?)](http://codegraphcontext.vercel.app/)
[![YouTube](https://img.shields.io/badge/Demo-Video-red?logo=youtube)](https://youtu.be/KYYSdxhg1xU)
[![Discord](https://img.shields.io/badge/Discord-Join-7289da?logo=discord&logoColor=white)](https://discord.gg/dR4QY32uYQ)

</div>

CodeGraphContext is an **MCP (Model Context Protocol) server** that indexes your local code into a Neo4j **knowledge graph** so AI assistants can answer deep structural questions: *Who calls this function? What imports are unused? Which modules form dependency cycles? What changes ripple if I modify X?*

---

## Table of Contents
1. [Features](#features)
2. [Screenshots / Demo](#screenshots--demo)
3. [Supported Languages](#supported-languages)
4. [Quick Start](#quick-start)
5. [How It Works](#how-it-works)
6. [Typical Workflow](#typical-workflow)
7. [Natural Language Examples](#natural-language-examples)
8. [Tool Guides](#tool-guides)
9. [MCP Client Configuration](#mcp-client-configuration)
10. [Use Cases](#use-cases)
11. [Roadmap](#roadmap)
12. [Architecture Overview](#architecture-overview)
13. [Dependencies](#dependencies)
14. [Contributing](#contributing)
15. [Security & Privacy](#security--privacy)
16. [License](#license)

---

## Features
- **Graph-Based Code Intelligence**: Functions, classes, files, imports, relationships (CALLS, CONTAINS, INHERITS, IMPORTS, ARGUMENTS) stored in Neo4j.
- **Natural Language Querying**: Ask questions via any MCP-enabled AI client; the server selects tools and returns structured results.
- **Live File Watching**: Continuous incremental updates using `watchdog`—no need to re-index manually.
- **Complexity & Dead Code Detection**: Cyclomatic complexity, most complex functions, unused functions.
- **Import & Dependency Introspection**: Enumerate imported packages across Python/JS/TS/Java (`list_imports`).
- **Background Job Management**: Long-running indexing jobs tracked with IDs & status checks.
- **Interactive Setup Wizard**: Automatic environment + MCP client configuration.
- **Extensible Tooling Layer**: Add new analysis tools with minimal friction.

## Screenshots / Demo
### Indexing a Codebase
![Indexing using an MCP client](images/Indexing.gif)

### Using the MCP Server
![Using the MCP server](images/Usecase.gif)

## Supported Languages
| Purpose | Languages |
|---------|-----------|
| Full AST / graph extraction | Python (primary) |
| Import enumeration | Python, JavaScript, TypeScript, Java |

Additional language parsers (e.g. CSS, C++, Rust) are planned / in progress. See open issues.

## Quick Start
```bash
pip install codegraphcontext
cgc setup   # guide through Neo4j + client configuration
cgc start   # launch MCP server
```
Then connect from a supported MCP client (VS Code, Cursor, Claude, Windsurf, etc.) and ask: *"Find the 5 most complex functions"*.

## How It Works
1. **Index**: Parses source files → builds nodes/relationships → stores them in Neo4j.
2. **Serve**: Exposes a catalog of tools (find_code, analyze_code_relationships, list_imports, etc.).
3. **Query**: AI assistant calls tools based on your natural language request.
4. **Update**: File watcher applies minimal diffs to the graph on change.

## Typical Workflow
1. `cgc setup` → configure Neo4j + client.
2. `cgc start` → run the server.
3. "Index the project at ~/dev/app" → background job starts.
4. "Show me all functions that call update_cache" → relationship traversal.
5. "Watch ~/dev/app" → continuous updates.
6. "Find unused code" → dead code scan.

## Natural Language Examples
| Question | What Happens Internally |
|----------|-------------------------|
| "Where is process_payment defined?" | `find_code` scans graph for matching symbol nodes |
| "Call chain from wrapper to helper" | `analyze_code_relationships` (call_chain) traversal |
| "Most complex 5 functions" | `find_most_complex_functions` ranked query |
| "List python imports in tests/sample_project" | `list_imports` collects & normalizes imports |
| "Show unused functions (ignore @app.route)" | `find_dead_code` filtering decorated items |

See the full [Cookbook](docs/cookbook.md) for many more.

## Tool Guides
Focused deep dives:
- [list_imports](docs/list_imports.md)
More guides will be added as tools expand.

## MCP Client Configuration
If auto-setup is skipped, add this to (for example) VS Code `settings.json`:
```json
{
  "mcpServers": {
    "CodeGraphContext": {
      "command": "cgc",
      "args": ["start"],
      "env": {
        "NEO4J_URI": "YOUR_NEO4J_URI",
        "NEO4J_USERNAME": "YOUR_NEO4J_USERNAME",
        "NEO4J_PASSWORD": "YOUR_NEO4J_PASSWORD"
      },
      "tools": {"alwaysAllow": [
        "list_imports","add_code_to_graph","add_package_to_graph","check_job_status","list_jobs",
        "find_code","analyze_code_relationships","watch_directory","find_dead_code","execute_cypher_query",
        "calculate_cyclomatic_complexity","find_most_complex_functions","list_indexed_repositories","delete_repository"
      ],"disabled": false},
      "disabled": false,
      "alwaysAllow": []
    }
  }
}
```

## Use Cases
- **AI Pairing / Context Expansion** – Provide the assistant with structural awareness.
- **Impact Analysis** – Before refactoring a core function.
- **Architecture Review** – Explore coupling, hubs, inheritance depth.
- **Onboarding** – New engineers query relationships instead of grepping.
- **Quality Audits** – Detect dead code & complexity hot-spots.

## Roadmap
Planned / potential enhancements (see issues for status):
- Additional language parsers (C++, Rust, CSS, TypeScript deeper semantics).
- Optional `exclude_stdlib` flag for `list_imports`.
- Performance / scaling benchmarks & caching layers.
- Graph visualization export (e.g. Graphviz / Mermaid / web viewer).
- SBOM / dependency risk overlays.
- IDE inline hints via LSP integration.

## Architecture Overview
| Component | Responsibility |
|-----------|----------------|
| CLI (`cgc`) | Setup, launching server, user ergonomics |
| Import / AST Parsers | Extract symbols, imports, relationships |
| Graph Builder | Persists nodes + edges to Neo4j |
| Job Manager | Tracks long-running indexing tasks |
| File Watcher | Incremental updates on save/change |
| Tool Layer | Implements callable MCP tools |
| MCP Server | JSON-RPC interface for AI clients |

Why Neo4j? Efficient relationship traversal, flexible schema evolution, expressive Cypher queries.

## Dependencies
Core runtime libraries (subset):
```
neo4j, watchdog, requests, stdlibs, typer, rich, inquirerpy, python-dotenv, tree-sitter, tree-sitter-languages
```
See `pyproject.toml` for full, pinned details.

## Contributing
Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md). Ways to help:
- Add a new language parser or complexity metric.
- Improve docs (examples, screenshots, demos).
- Optimize query performance.
- Extend tooling (e.g. security scans, architectural smells).

Join the community on [Discord](https://discord.gg/dR4QY32uYQ) and open an [issue](https://github.com/Shashankss1205/CodeGraphContext/issues) to discuss ideas first for larger changes.

## Security & Privacy
- Credentials stored locally at `~/.codegraphcontext/.env`.
- Source code is processed locally; only your Neo4j instance receives data.
- Do not index proprietary code into a remote database you do not control.
- Report concerns via [SECURITY.md](SECURITY.md).

## License
MIT – see [LICENSE](LICENSE).

## Attribution & Inspiration
Built to make AI-assisted code comprehension structurally accurate and explainable.

---
If this project helps you, consider starring the repo ⭐ and sharing feedback.
