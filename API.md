# API Reference

Complete API documentation for CodeGraphContext MCP Server tools.

## Available Tools

### Code Indexing Tools

#### add_code_to_graph
Performs a one-time scan of a local folder to add its code to the graph.

**Parameters:**
- `path` (string, required): Path to the directory or file to add
- `is_dependency` (boolean, optional): Whether this code is a dependency (default: false)

**Returns:** Job ID for background processing

**Example:**
```json
{
  "path": "/path/to/project",
  "is_dependency": false
}
```

---

#### add_package_to_graph
Add a Python package to Neo4j graph by discovering its location.

**Parameters:**
- `package_name` (string, required): Name of the Python package (e.g., 'requests')
- `is_dependency` (boolean, optional): Mark as a dependency (default: true)

**Returns:** Job ID

**Example:**
```json
{
  "package_name": "requests",
  "is_dependency": true
}
```

---

#### watch_directory
Performs an initial scan and continuously monitors a directory for changes.

**Parameters:**
- `path` (string, required): Path to directory to watch

**Returns:** Job ID for initial scan

**Example:**
```json
{
  "path": "/path/to/active/project"
}
```

---

#### unwatch_directory
Stops watching a directory for live file changes.

**Parameters:**
- `path` (string, required): Path to directory to stop watching

---

#### list_watched_paths
Lists all directories currently being watched for live file changes.

**Parameters:** None

**Returns:** List of watched directory paths

---

### Job Management Tools

#### check_job_status
Check the status and progress of a background job.

**Parameters:**
- `job_id` (string, required): Job ID from a previous tool call

**Returns:** Job status object with progress information

**Example:**
```json
{
  "job_id": "abc123"
}
```

---

#### list_jobs
List all background jobs and their current status.

**Parameters:** None

**Returns:** Array of job objects

---

### Code Search Tools

#### find_code
Find relevant code snippets related to a keyword.

**Parameters:**
- `query` (string, required): Keyword or phrase to search for

**Returns:** Matching code snippets with context

**Example:**
```json
{
  "query": "process_payment"
}
```

---

#### list_imports
Extract all package imports from code files in a directory or file.

**Parameters:**
- `path` (string, required): Path to file or directory to analyze
- `language` (string, optional): Programming language (default: "python")
- `recursive` (boolean, optional): Analyze subdirectories recursively (default: true)

**Returns:** List of imported packages

**Example:**
```json
{
  "path": "/path/to/project",
  "language": "python",
  "recursive": true
}
```

---

### Code Analysis Tools

#### analyze_code_relationships
Analyze code relationships like callers, callees, class hierarchy, etc.

**Parameters:**
- `query_type` (string, required): Type of relationship query
  - `find_callers`: Find direct callers of a function
  - `find_callees`: Find direct callees of a function
  - `find_all_callers`: Find all direct and indirect callers
  - `find_all_callees`: Find all direct and indirect callees
  - `find_importers`: Find files that import a module
  - `who_modifies`: Find who modifies a variable
  - `class_hierarchy`: Show class inheritance hierarchy
  - `overrides`: Find method overrides
  - `dead_code`: Find unused code
  - `call_chain`: Trace execution flow
  - `module_deps`: Analyze module dependencies
  - `variable_scope`: Analyze variable scope
  - `find_complexity`: Find complex code
  - `find_functions_by_argument`: Find functions by argument
  - `find_functions_by_decorator`: Find functions by decorator
- `target` (string, required): The function, class, or module to analyze
- `context` (string, optional): Specific file path for precise results

**Example:**
```json
{
  "query_type": "find_callers",
  "target": "process_data",
  "context": "/path/to/file.py"
}
```

---

#### find_dead_code
Find potentially unused functions across the entire indexed codebase.

**Parameters:**
- `exclude_decorated_with` (array of strings, optional): Decorator names to exclude (e.g., ['@app.route'])

**Returns:** List of potentially unused functions

**Example:**
```json
{
  "exclude_decorated_with": ["@app.route", "@celery.task"]
}
```

---

#### calculate_cyclomatic_complexity
Calculate the cyclomatic complexity of a specific function.

**Parameters:**
- `function_name` (string, required): Name of the function to analyze
- `file_path` (string, optional): Full path to the file containing the function

**Returns:** Cyclomatic complexity value and interpretation

**Example:**
```json
{
  "function_name": "process_data",
  "file_path": "/path/to/file.py"
}
```

---

#### find_most_complex_functions
Find the most complex functions based on cyclomatic complexity.

**Parameters:**
- `limit` (integer, optional): Maximum number of functions to return (default: 10)

**Returns:** List of most complex functions with their complexity scores

**Example:**
```json
{
  "limit": 5
}
```

---

### Repository Management Tools

#### list_indexed_repositories
List all indexed repositories.

**Parameters:** None

**Returns:** Array of repository objects with paths and metadata

---

#### delete_repository
Delete an indexed repository from the graph.

**Parameters:**
- `repo_path` (string, required): Path of the repository to delete

**Example:**
```json
{
  "repo_path": "/path/to/old/project"
}
```

---

### Advanced Query Tools

#### execute_cypher_query
Run a direct, read-only Cypher query against the code graph.

**Parameters:**
- `cypher_query` (string, required): The read-only Cypher query to execute

**Returns:** Query results

**Graph Schema:**
- **Nodes:** Repository, File, Module, Class, Function
- **Properties:** name, path, cyclomatic_complexity (on Function), code
- **Relationships:** CONTAINS, CALLS, IMPORTS, INHERITS

**Example:**
```json
{
  "cypher_query": "MATCH (f:Function) WHERE f.name = 'main' RETURN f"
}
```

---

#### visualize_graph_query
Generates a URL to visualize the results of a Cypher query in Neo4j Browser.

**Parameters:**
- `cypher_query` (string, required): The Cypher query to visualize

**Returns:** Neo4j Browser URL

**Example:**
```json
{
  "cypher_query": "MATCH (f:Function)-[:CALLS]->(c:Function) RETURN f, c LIMIT 25"
}
```

---

## Response Format

All tools return JSON responses in the following format:

**Success:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "Result message or data"
    }
  ]
}
```

**Error:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "Error: Description of the error"
    }
  ],
  "isError": true
}
```

## Job Status Values

- `pending`: Job is queued but not started
- `running`: Job is currently executing
- `completed`: Job finished successfully
- `failed`: Job encountered an error

## Graph Schema Details

### Node Types

1. **Repository**
   - Properties: `path`, `name`, `created_at`

2. **File**
   - Properties: `path`, `name`, `language`, `last_modified`
   - Relationships: `BELONGS_TO` → Repository, `CONTAINS` → Function/Class/Module

3. **Module**
   - Properties: `name`, `path`
   - Relationships: `IMPORTED_BY` ← File

4. **Class**
   - Properties: `name`, `path`, `docstring`, `code`
   - Relationships: `INHERITS` → Class, `CONTAINS` → Function

5. **Function**
   - Properties: `name`, `path`, `line_number`, `cyclomatic_complexity`, `code`, `docstring`, `decorators`, `arguments`
   - Relationships: `CALLS` → Function, `MODIFIES` → Variable

### Relationship Types

- `CONTAINS`: Parent contains child (File→Function, Class→Function)
- `CALLS`: Function calls another function
- `IMPORTS`: File imports a module
- `INHERITS`: Class inherits from another class
- `MODIFIES`: Function modifies a variable
- `BELONGS_TO`: File belongs to a repository
