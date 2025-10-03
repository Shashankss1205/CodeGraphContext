# Tools Exploration
There are a total of 14 tools available to the users, and here we have attached illustrative demos for each one of them.

## find_code Tool

The `find_code` tool allows users to search for code snippets, functions, classes, and variables within the codebase using natural language queries. This tool helps developers understand and navigate large codebases efficiently.

Below is an embedded link to a demo video showcasing the usage of the `find_code` tool in action.
[![Watch the demo video](./images/tool_images/1.png)](https://drive.google.com/file/d/1ojCDIIAwcir9e3jgHHIVC5weZ9nuIQcs/view?usp=drive_link)

---

## watch_directory Tool

The `watch_directory` tool allows users to monitor a specified directory for file changes, additions, or deletions in real-time. It helps developers automate workflows such as triggering scripts, updating indexes, or syncing files whenever changes occur in the directory.

Below is an embedded link to a demo video showcasing the usage of the `watch_directory` tool in a development environment.
[![Watch the demo](./images/tool_images/2.png)](https://drive.google.com/file/d/1OEjcS2iwwymss99zLidbeBjcblferKBX/view?usp=drive_link) 

---

## analyze_code_relationships Tool

The `analyze_code_relationships` tool in CodeGraphContext is designed to let users query and explore the various relationships between code elements in a codebase, represented as a graph in Neo4j. 

### Relationship Types That Can Be Analyzed

- **CALLS:** Finds which functions call or are called by a function.
- **CALLED_BY:** Finds all functions that directly or indirectly call a target function (inverse of CALLS).
- **INHERITS_FROM:** Finds class inheritance relationships; which classes inherit from which.
- **CONTAINS:** Shows containment (which classes/functions are inside which modules or files).
- **IMPLEMENTS:** Shows which classes implement an interface.
- **IMPORTS:** Identifies which files or modules import a specific module.
- **DEFINED_IN:** Locates where an entity (function/class) is defined.
- **HAS_ARGUMENT:** Shows relationships from functions to their arguments.
- **DECLARES:** Finds variables declared in functions or classes.

Below is an embedded link to a demo video showcasing the usage of the `analyse_code_relationships` tool.
[![Watch the demo](./images/tool_images/3.png)](https://drive.google.com/file/d/154M_lTPbg9_Gj9bd2ErnAVbJArSbcb2M/view?usp=drive_link) 

---

## execute_cypher_query Tool

The `execute_cypher_query` tool lets you run read-only Cypher queries against the CodeGraphContext Neo4j graph to explore the indexed codebase. It is ideal for custom graph lookups beyond the built-in analysis tools.

### Safety and Restrictions
- Read-only only: queries are validated to block mutation keywords like `CREATE`, `MERGE`, `DELETE`, `SET`, `REMOVE`, `DROP`, and `CALL apoc`.
- Validation happens server-side before execution to protect the database.

### Where it’s implemented
- Server tool: `src/codegraphcontext/server.py` (`execute_cypher_query_tool`)
- System wrapper: `src/codegraphcontext/tools/system.py` (`execute_cypher_query_tool`)

### CLI usage
Run a Cypher query directly from the CLI:

```
python -m codegraphcontext cypher "MATCH (f:Function) RETURN f.name, f.file_path LIMIT 10"
```

### MCP tool invocation
Use the tool name `execute_cypher_query` with the argument `cypher_query`:

```json
{
  "tool": "execute_cypher_query",
  "args": {
    "cypher_query": "MATCH (c:Class) RETURN c.name, c.file_path LIMIT 25"
  }
}
```

### Useful example queries
- Find functions:
  - `MATCH (n:Function) RETURN n.name, n.file_path, n.line_number LIMIT 50`
- Find classes:
  - `MATCH (n:Class) RETURN n.name, n.file_path, n.line_number LIMIT 50`
- Find dataclasses:
  - `MATCH (c:Class) WHERE 'dataclass' IN c.decorators RETURN c.name, c.file_path`
- Circular imports between files:
  - `MATCH path = (f1:File)-[:IMPORTS*2..]->(f1) RETURN path LIMIT 10`

### Demo video
A short demo showing end-to-end usage (CLI and tool invocation) will be attached as part of issue tracking. See the issue for updates: [Add Demo and Usage Guide for execute_cypher_query Tool #225](https://github.com/Shashankss1205/CodeGraphContext/issues/225).

---