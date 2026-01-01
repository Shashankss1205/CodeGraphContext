## 🧩 Installation Guide

Welcome to **CodeGraphContext**! This guide provides a clear and seamless path to installing and configuring the tool.

## 📋 Understanding CodeGraphContext Modes

CodeGraphContext operates in **two modes**, and you can use either or both:

### 🛠️ Mode 1: CLI Toolkit (Standalone)
Use CodeGraphContext as a **powerful command-line toolkit** for code analysis:
- Index and analyze codebases directly from your terminal
- Query code relationships, find dead code, analyze complexity
- Visualize code graphs and dependencies
- Perfect for developers who want direct control via CLI commands

### 🤖 Mode 2: MCP Server (AI-Powered)
Use CodeGraphContext as an **MCP server** for AI assistants:
- Connect to AI IDEs (VS Code, Cursor, Windsurf, Claude, etc.)
- Let AI agents query your codebase using natural language
- Automatic code understanding and relationship analysis
- Perfect for AI-assisted development workflows

**You can use both modes!** Install once, then use CLI commands directly OR connect to your AI assistant.

---

## ⚙️ Prerequisites

Ensure the following are installed before you begin:

- **Python**: Version 3.10 or higher (3.12+ recommended for FalkorDB Lite support)
- **AI Assistant** (optional): An MCP-compatible tool (e.g., VS Code, Cursor, Claude, Gemini CLI) if you plan to use Mode 2

---

## 🚀 Installation

### Step 1: Install from PyPI

Install the `codegraphcontext` package using pip:

```bash
pip install codegraphcontext
```

### Step 2: Database Setup

CodeGraphContext uses a graph database to store code relationships. You have two options:

#### Option A: FalkorDB Lite (Default - Recommended)
- **Automatic** on Unix/Linux/macOS/WSL with Python 3.12+
- **No configuration needed** - works out of the box
- Lightweight, in-memory, perfect for most use cases

If you're on Unix/Linux/macOS/WSL with Python 3.12+, **you're done!** Skip to Step 3.

#### Option B: Neo4j (Alternative)
- Available on **all platforms** (Windows, Linux, macOS)
- Required if you're on Windows without WSL or prefer Neo4j
- Can be installed via Docker, native installation, or cloud (AuraDB)

To set up Neo4j, run:

```bash
cgc neo4j setup
```

The wizard will guide you through:
- **Docker** (recommended): Automatically sets up a local Neo4j container
- **Native Installation**: Installs Neo4j directly on Debian-based systems or macOS
- **Hosted/AuraDB**: Connect to a remote Neo4j instance
- **Existing Instance**: Use your own Neo4j server

---

## 🎯 Mode-Specific Setup

### For CLI Toolkit Mode (Mode 1)

You're ready to go! Start using CLI commands:

```bash
# Index your current directory
cgc index .

# List indexed repositories
cgc list

# Analyze code relationships
cgc analyze callers my_function

# Find complex functions
cgc analyze complexity --threshold 10

# See all available commands
cgc --help
```

**See the [CLI Reference](cli.md) for all available commands.**

---

### For MCP Server Mode (Mode 2)

Configure your AI assistant to connect to CodeGraphContext:

#### Step 1: Run MCP Setup Wizard

```bash
cgc mcp setup
```

The wizard will:
- Detect your installed AI tools (VS Code, Cursor, Claude, etc.)
- Automatically configure the selected tool
- Generate `mcp.json` configuration file
- Store credentials securely in `~/.codegraphcontext/.env`

**Supported AI Tools:**
- VS Code
- Cursor
- Windsurf
- Claude Desktop
- Gemini CLI
- ChatGPT Codex
- Cline
- RooCode
- Amazon Q Developer

#### Step 2: Start the MCP Server

```bash
cgc mcp start
```

Your MCP server is now running and ready to receive requests from your AI assistant!

#### Manual Configuration (Optional)

If you prefer to configure manually or your tool isn't auto-detected, add this to your tool's settings file:

```json
{
  "mcpServers": {
    "CodeGraphContext": {
      "command": "cgc",
      "args": ["mcp", "start"],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "your-password"
      }
    }
  }
}
```

**Note:** If using FalkorDB Lite (default), you don't need to set NEO4J_* environment variables.

---

## 🧭 Quick Start Examples

### CLI Toolkit Workflow
```bash
# Install
pip install codegraphcontext

# Index a project
cgc index /path/to/my-project

# Find all callers of a function
cgc analyze callers process_payment

# Find dead code
cgc analyze dead-code

# Check database stats
cgc stats
```

### MCP Server Workflow
```bash
# Install
pip install codegraphcontext

# Configure your AI assistant
cgc mcp setup

# Start the server
cgc mcp start

# Now use natural language in your AI assistant:
# "Index the code in /path/to/my-project"
# "Find all functions that call process_payment"
# "Show me the class hierarchy for UserController"
```

---

## 🔧 Database Configuration Details

### FalkorDB Lite (Default)
- **Platform**: Unix/Linux/macOS/WSL
- **Python**: 3.12+ required
- **Setup**: Automatic, no configuration needed
- **Storage**: In-memory
- **Best for**: Most use cases, quick testing, development

### Neo4j
- **Platform**: All (Windows, Linux, macOS)
- **Python**: 3.10+ supported
- **Setup**: Via `cgc neo4j setup` wizard
- **Storage**: Persistent disk storage
- **Best for**: Windows users, production deployments, large codebases

---

## 📚 Next Steps

### For CLI Users
- Explore the [CLI Reference](cli.md) for all available commands
- Check out the [Cookbook](cookbook.md) for common analysis patterns
- Learn about [Code Analysis](core.md) capabilities

### For MCP Users
- See [MCP Tools Documentation](tools.md) for available AI tools
- Review [Natural Language Examples](index.md#natural-language-interaction-examples)
- Explore the [Use Cases](use_cases.md) guide

---

## 🆘 Troubleshooting

If you encounter issues, see our [Troubleshooting Guide](troubleshooting.md) for common problems and solutions.

**Common Issues:**
- **"cgc: command not found"**: Run the PATH fix script (see main README)
- **Database connection errors**: Ensure Neo4j is running (if using Neo4j) or Python 3.12+ (if using FalkorDB)
- **MCP server won't start**: Check that your AI assistant is properly configured

---

With **CodeGraphContext** installed, you're ready to explore powerful code analysis capabilities! Happy coding ✨!
