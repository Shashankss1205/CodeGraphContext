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

## list_indexed_repositories and delete_repository Tools (Combined Demo)

These tools help you manage which repositories are currently indexed in the Neo4j code graph.

- list_indexed_repositories: Returns all repositories present in the graph with their names and paths.
- delete_repository: Removes a repository (and its nodes/relationships) from the graph by path.

### When to use
- Use list_indexed_repositories to verify what’s currently indexed before or after indexing/deleting.
- Use delete_repository to clean up an outdated or unwanted repository before re-indexing it.

### CLI usage
```bash
# List indexed repositories
cgc list_repos

# Delete a repository from the graph by its path
cgc delete "/absolute/or/project/path"
```

### Direct tool calls
```json
{
  "tool": "list_indexed_repositories",
  "args": {}
}
```
```json
{
  "tool": "delete_repository",
  "args": { "repo_path": "/absolute/or/project/path" }
}
```

### Expected responses
- list_indexed_repositories returns:
```json
{
  "success": true,
  "repositories": [
    { "name": "sample_project", "path": "/path/to/sample_project", "is_dependency": false }
  ]
}
```
- delete_repository returns:
```json
{
  "success": true,
  "message": "Repository '/path/to/sample_project' deleted successfully."
}
```

### Demo flow (suggested for video)
1) Run cgc list_repos and capture the current repositories.
2) Index a repo if needed (cgc index /path/to/repo), wait for job completion.
3) Run cgc list_repos again to show the newly indexed repo appears.
4) Run cgc delete "/path/to/repo" to remove it.
5) Run cgc list_repos once more to show it no longer appears.