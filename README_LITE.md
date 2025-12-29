# CodeGraphContext - Lite Version (FalkorDB)

This is the **lite version** of CodeGraphContext that uses **FalkorDB Lite** instead of Neo4j, eliminating the need for external database server setup!

## What's Different?

### Standard Version (Neo4j)
- ❌ Requires Docker or Neo4j server installation
- ❌ Requires configuration (URI, username, password)
- ❌ Needs port management (7474, 7687)
- ✅ Suitable for production deployments
- ✅ Better for large-scale projects

### Lite Version (FalkorDB Lite)
- ✅ **Zero setup** - just install and run!
- ✅ **Embedded database** - no external server needed
- ✅ **Automatic persistence** - data saved to local file
- ✅ **Same Cypher queries** - compatible query language
- ✅ **Perfect for development** and personal projects
- ✅ **Portable** - database is just a file

## Installation

### Quick Start (Recommended)

```bash
# Install the lite version with FalkorDB
pip install codegraphcontext[lite]
```

That's it! No Docker, no server setup, no configuration files needed.

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/Shashankss1205/CodeGraphContext.git
cd CodeGraphContext

# Checkout the lite-version branch
git checkout lite-version

# Install with lite dependencies
pip install -e ".[lite]"
```

## Usage

### 1. Start the Server

```bash
# The lite version uses FalkorDB by default
cgc start
```

The database will be automatically created at `~/.codegraphcontext/falkordb.db`

### 2. Configure Your AI Assistant

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "codegraphcontext": {
      "command": "cgc",
      "args": ["start"]
    }
  }
}
```

### 3. Start Using!

In Claude Desktop, you can now:
- "Index the code in /path/to/my/project"
- "Find all functions that call process_data"
- "Show me the class hierarchy for User"
- "What are the most complex functions?"

## Configuration

### Database Location

By default, the database is stored at `~/.codegraphcontext/falkordb.db`. You can change this:

```bash
export FALKORDB_PATH="/path/to/your/database.db"
cgc start
```

### Graph Name

The default graph name is `codegraph`. To change it:

```bash
export FALKORDB_GRAPH_NAME="mygraph"
cgc start
```

### Switching Between Neo4j and FalkorDB

You can switch database backends using the `DATABASE_TYPE` environment variable:

```bash
# Use FalkorDB Lite (default for lite-version branch)
export DATABASE_TYPE=falkordb
cgc start

# Use Neo4j (requires Neo4j server setup)
export DATABASE_TYPE=neo4j
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USERNAME=neo4j
export NEO4J_PASSWORD=your_password
cgc start
```

## Features

All the same features as the standard version:

✅ **Multi-language support**: Python, JavaScript, TypeScript, Java, Go, C, C++, C#, Rust, Ruby
✅ **Code indexing**: Functions, classes, variables, imports
✅ **Relationship tracking**: Calls, inheritance, imports
✅ **Live watching**: Auto-update graph on file changes
✅ **Package discovery**: Auto-find and index dependencies
✅ **Complexity analysis**: Cyclomatic complexity calculation
✅ **Dead code detection**: Find unused functions
✅ **Cypher queries**: Full graph query support

## Advantages of Lite Version

### 1. **Zero Configuration**
```bash
pip install codegraphcontext[lite]
cgc start
# That's it! 🎉
```

### 2. **Portable**
Your entire code graph is in a single file. Easy to:
- Backup
- Share with team members
- Move between machines
- Version control (if small enough)

### 3. **No Resource Overhead**
- No Docker containers
- No background services
- No port conflicts
- Minimal memory footprint

### 4. **Perfect for Development**
- Quick prototyping
- Personal projects
- Learning and experimentation
- CI/CD pipelines

## Limitations

- **Performance**: For very large codebases (>100K files), Neo4j may be faster
- **Concurrent Access**: FalkorDB Lite is single-process (fine for MCP use case)
- **Advanced Features**: Some Neo4j-specific features may not be available

## Migration

### From Neo4j to FalkorDB Lite

1. Export your Neo4j data (optional - if you want to keep it)
2. Switch to lite version:
   ```bash
   git checkout lite-version
   pip install -e ".[lite]"
   ```
3. Re-index your code:
   ```bash
   cgc start
   # Then in Claude: "Index the code in /path/to/project"
   ```

### From FalkorDB Lite to Neo4j

1. Set up Neo4j server (Docker or standalone)
2. Configure environment variables:
   ```bash
   export DATABASE_TYPE=neo4j
   export NEO4J_URI=bolt://localhost:7687
   export NEO4J_USERNAME=neo4j
   export NEO4J_PASSWORD=your_password
   ```
3. Re-index your code

## Troubleshooting

### "FalkorDB Lite is not installed"

```bash
pip install falkordblite
```

### Database file permissions

Ensure you have write permissions to the database directory:
```bash
chmod 755 ~/.codegraphcontext
```

### Database corruption

If the database gets corrupted, simply delete it and re-index:
```bash
rm ~/.codegraphcontext/falkordb.db
cgc start
# Re-index your code
```

## Performance Tips

1. **Index incrementally**: Use `watch_directory` for active projects
2. **Exclude unnecessary files**: Add `.gitignore` patterns
3. **Backup regularly**: Copy the `.db` file periodically
4. **Clean old data**: Delete and re-index if graph gets too large

## FAQ

**Q: Can I use both Neo4j and FalkorDB?**
A: Yes! Switch using the `DATABASE_TYPE` environment variable.

**Q: Is the query syntax the same?**
A: Yes, both use Cypher queries.

**Q: Can I visualize the graph?**
A: FalkorDB Lite doesn't have a built-in browser like Neo4j, but you can use Cypher queries to explore the graph.

**Q: How big can my database get?**
A: FalkorDB Lite can handle databases up to several GB. For larger projects, consider Neo4j.

**Q: Is my data safe?**
A: Yes, FalkorDB Lite automatically persists data to disk after each transaction.

## Contributing

We welcome contributions! Please see the main [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](../LICENSE) for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/Shashankss1205/CodeGraphContext/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Shashankss1205/CodeGraphContext/discussions)

---

**Made with ❤️ for developers who want zero-friction code intelligence**
