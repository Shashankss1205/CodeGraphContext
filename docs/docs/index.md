# Welcome to CodeGraphContext

CodeGraphContext (CGC) is a **Code Intelligence Engine**. It indexes your codebase into a graph database to provide deep semantic understanding for both developers (via CLI) and AI agents (via MCP).

### :material-console: For Developers (CLI)
Use powerful terminal commands to query call chains, find dependencies, and visual architectural graphs.
**[Explore CLI Reference](reference/cli_indexing.md)**

### :material-robot: For AI Agents (MCP)
Connect your codebase to Cursor, Claude, or VS Code. Let AI assist you with full context awareness.
**[Setup AI Assistant](guides/mcp_guide.md)** & 
**[Explore Natural Language Queries](reference/mcp_master.md)**

### ⚙️ Configuration
Customize databases, file limits, and more.
**[View Configuration Guide](reference/configuration.md)**

---

## 🏗️ Architecture

CGC sits between your code and your tools. It's not just a script; it's a persistent system.

![CodeGraphContext Architecture](images/architecture.png)

## 🚀 Why CodeGraphContext?

*   **Beyond RegEx:** Text search is dumb. CGC understands *structure*. It knows that `User.save()` in `models.py` is called by `AuthController` even if the file names are different.
*   **Universal Context:** Index once, use everywhere. The same graph powers your CLI queries and your AI's answers.
*   **Privacy First:** Your code is indexed locally (or in your self-hosted DB). No code is sent to our servers.

---

## 🗺️ How to Read These Docs

We have organized the documentation to match your journey:

1.  **[Getting Started](getting-started/prerequisites.md):** The linear path to installation.
2.  **[Core Concepts](concepts/how_it_works.md):** Understand the "magic" (Nodes, Edges, Bundles).
3.  **[Guides](guides/mcp_guide.md):** Task-based generic tutorials.
4.  **[Reference](reference/cli_indexing.md):** The complete technical encyclopedia.

---

### :material-rocket-launch: Ready to Start?
**[Install CodeGraphContext](getting-started/installation.md)**

### :material-book-open-page-variant: Learn the Concepts
**[How Indexing Works](concepts/how_it_works.md)**
