# src/codegraphcontext/server.py
import urllib.parse
import asyncio
import json
import importlib
import stdlibs
import sys
import traceback
import os
import re
from datetime import datetime
from pathlib import Path
from neo4j.exceptions import CypherSyntaxError
from dataclasses import asdict

from typing import Any, Dict, Coroutine, Optional

from .prompts import LLM_SYSTEM_PROMPT
from .core import get_database_manager
from .core.jobs import JobManager, JobStatus
from .core.watcher import CodeWatcher
from .tools.graph_builder import GraphBuilder
from .tools.code_finder import CodeFinder
from .tools.package_resolver import get_local_package_path
from .utils.debug_log import debug_log, info_logger, error_logger, warning_logger, debug_logger

DEFAULT_EDIT_DISTANCE = 2
DEFAULT_FUZZY_SEARCH = False

class MCPServer:
    """
    The main MCP Server class.
    
    This class orchestrates all the major components of the application, including:
    - Database connection management (`DatabaseManager` or `FalkorDBManager`)
    - Background job tracking (`JobManager`)
    - File system watching for live updates (`CodeWatcher`)
    - Tool handlers for graph building, code searching, etc.
    - The main JSON-RPC communication loop for interacting with an AI assistant.
    """

    def __init__(self, loop=None):
        """
        Initializes the MCP server and its components. 
        
        Args:
            loop: The asyncio event loop to use. If not provided, it gets the current
                  running loop or creates a new one.
        """
        try:
            # Initialize the database manager (Neo4j or FalkorDB Lite based on env var)
            # to fail fast if credentials/configuration are wrong.
            self.db_manager = get_database_manager()
            self.db_manager.get_driver() 
        except ValueError as e:
            raise ValueError(f"Database configuration error: {e}")

        # Initialize managers for jobs and file watching.
        self.job_manager = JobManager()
        
        # Get the current event loop to pass to thread-sensitive components like the graph builder.
        if loop is None:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        self.loop = loop

        # Initialize all the tool handlers, passing them the necessary managers and the event loop.
        self.graph_builder = GraphBuilder(self.db_manager, self.job_manager, loop)
        self.code_finder = CodeFinder(self.db_manager)
        self.code_watcher = CodeWatcher(self.graph_builder, self.job_manager)
        
        # Define the tool manifest that will be exposed to the AI assistant.
        self._init_tools()

    def _init_tools(self):
        """
        Defines the complete tool manifest for the LLM.
        This dictionary contains the schema for every tool the AI can call,
        including its name, description, and input parameters.
        """
        self.tools = {
            "add_code_to_graph": {
                "name": "add_code_to_graph",
                "description": "Performs a one-time scan of a local folder to add its code to the graph. Ideal for indexing libraries, dependencies, or projects not being actively modified. Returns a job ID for background processing.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to the directory or file to add."},
                        "is_dependency": {"type": "boolean", "description": "Whether this code is a dependency.", "default": False}
                    },
                    "required": ["path"]
                }
            },
            "check_job_status": {
                "name": "check_job_status",
                "description": "Check the status and progress of a background job.",
                "inputSchema": {
                    "type": "object",
                    "properties": { "job_id": {"type": "string", "description": "Job ID from a previous tool call"} },
                    "required": ["job_id"]
                }
            },
            "list_jobs": {
                "name": "list_jobs",
                "description": "List all background jobs and their current status.",
                "inputSchema": {"type": "object", "properties": {}}
            },
           "find_code": {
                "name": "find_code",
                "description": "Find relevant code snippets related to a keyword (e.g., function name, class name, or content).",
                "inputSchema": {
                    "type": "object",
                    "properties": { "query": {"type": "string", "description": "Keyword or phrase to search for"}, "fuzzy_search": {"type": "boolean", "description": "Whether to use fuzzy search", "default": False}, "edit_distance": {"type": "number", "description": "Edit distance for fuzzy search (between 0-2)", "default": 2}}, 
                    "required": ["query"]
                }
            },

            "analyze_code_relationships": {
                "name": "analyze_code_relationships",
                "description": "Analyze code relationships like 'who calls this function' or 'class hierarchy'. Supported query types include: find_callers, find_callees, find_all_callers, find_all_callees, find_importers, who_modifies, class_hierarchy, overrides, dead_code, call_chain, module_deps, variable_scope, find_complexity, find_functions_by_argument, find_functions_by_decorator.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query_type": {"type": "string", "description": "Type of relationship query to run.", "enum": ["find_callers", "find_callees", "find_all_callers", "find_all_callees", "find_importers", "who_modifies", "class_hierarchy", "overrides", "dead_code", "call_chain", "module_deps", "variable_scope", "find_complexity", "find_functions_by_argument", "find_functions_by_decorator"]},
                        "target": {"type": "string", "description": "The function, class, or module to analyze."},
                        "context": {"type": "string", "description": "Optional: specific file path for precise results."} 
                    },
                    "required": ["query_type", "target"]
                }
            },
            "watch_directory": {
                "name": "watch_directory",
                "description": "Performs an initial scan of a directory and then continuously monitors it for changes, automatically keeping the graph up-to-date. Ideal for projects under active development. Returns a job ID for the initial scan.",
                "inputSchema": {
                    "type": "object",
                    "properties": { "path": {"type": "string", "description": "Path to directory to watch"} },
                    "required": ["path"]
                }
            },
            "execute_cypher_query": {
                "name": "execute_cypher_query",
                "description": "Fallback tool to run a direct, read-only Cypher query against the code graph. Use this for complex questions not covered by other tools. The graph contains nodes representing code structures and relationships between them. **Schema Overview:**\n- **Nodes:** `Repository`, `File`, `Module`, `Class`, `Function`.\n- **Properties:** Nodes have properties like `name`, `path`, `cyclomatic_complexity` (on Function nodes), and `code`.\n- **Relationships:** `CONTAINS` (e.g., File-[:CONTAINS]->Function), `CALLS` (Function-[:CALLS]->Function or File-[:CALLS]->Function), `IMPORTS` (File-[:IMPORTS]->Module), `INHERITS` (Class-[:INHERITS]->Class).",
                "inputSchema": {
                    "type": "object",
                    "properties": { "cypher_query": {"type": "string", "description": "The read-only Cypher query to execute."} },
                    "required": ["cypher_query"]
                }
            },
            "add_package_to_graph": {
                "name": "add_package_to_graph",
                "description": "Add a package to the graph by discovering its location. Supports multiple languages. Returns immediately with a job ID.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "package_name": {"type": "string", "description": "Name of the package to add (e.g., 'requests', 'express', 'moment', 'lodash')."},
                        "language": {"type": "string", "description": "The programming language of the package.", "enum": ["python", "javascript", "typescript", "java", "c", "go", "ruby", "php","cpp"]},
                        "is_dependency": {"type": "boolean", "description": "Mark as a dependency.", "default": True}
                    },
                    "required": ["package_name", "language"]
                }
            },
            "find_dead_code": {
                "name": "find_dead_code",
                "description": "Find potentially unused functions (dead code) across the entire indexed codebase, optionally excluding functions with specific decorators.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "exclude_decorated_with": {"type": "array", "items": {"type": "string"}, "description": "Optional: A list of decorator names (e.g., '@app.route') to exclude from dead code detection.", "default": []}
                    }
                }
            },
            "calculate_cyclomatic_complexity": {
                "name": "calculate_cyclomatic_complexity",
                "description": "Calculate the cyclomatic complexity of a specific function to measure its complexity.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "function_name": {"type": "string", "description": "The name of the function to analyze."},
                        "file_path": {"type": "string", "description": "Optional: The full path to the file containing the function for a more specific query."} 
                    },
                    "required": ["function_name"]
                }
            },
            "find_most_complex_functions": {
                "name": "find_most_complex_functions",
                "description": "Find the most complex functions in the codebase based on cyclomatic complexity.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer", "description": "The maximum number of complex functions to return.", "default": 10}
                    }
                }
            },
            "list_indexed_repositories": {
                "name": "list_indexed_repositories",
                "description": "List all indexed repositories.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            "delete_repository": {
                "name": "delete_repository",
                "description": "Delete an indexed repository from the graph.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "repo_path": {"type": "string", "description": "The path of the repository to delete."} 
                    },
                    "required": ["repo_path"]
                }
            },
            "visualize_graph_query": {
                "name": "visualize_graph_query",
                "description": "Generates a URL to visualize the results of a Cypher query in the Neo4j Browser. The user can open this URL in their web browser to see the graph visualization.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "cypher_query": {"type": "string", "description": "The Cypher query to visualize."}
                    },
                    "required": ["cypher_query"]
                }
            },
            "list_watched_paths": {
                "name": "list_watched_paths",
                "description": "Lists all directories currently being watched for live file changes.",
                "inputSchema": {"type": "object", "properties": {}}
            },
            "unwatch_directory": {
                "name": "unwatch_directory",
                "description": "Stops watching a directory for live file changes.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "The absolute path of the directory to stop watching."}
                    },
                    "required": ["path"]
                }
            }
        }    

    def get_database_status(self) -> dict:
        """Returns the current connection status of the Neo4j database."""
        return {"connected": self.db_manager.is_connected()}
        

    def execute_cypher_query_tool(self, **args) -> Dict[str, Any]:
        """
        Tool implementation for executing a read-only Cypher query.
        
        Important: Includes a safety check to prevent any database modification
        by disallowing keywords like CREATE, MERGE, DELETE, etc.
        """
        cypher_query = args.get("cypher_query")
        if not cypher_query:
            return {"error": "Cypher query cannot be empty."}

        # Safety Check: Prevent any write operations to the database.
        # This check first removes all string literals and then checks for forbidden keywords.
        forbidden_keywords = ['CREATE', 'MERGE', 'DELETE', 'SET', 'REMOVE', 'DROP', 'CALL apoc']
        
        # Regex to match single or double quoted strings, handling escaped quotes.
        string_literal_pattern = r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''
        
        # Remove all string literals from the query.
        query_without_strings = re.sub(string_literal_pattern, '', cypher_query)
        
        # Now, check for forbidden keywords in the query without strings.
        for keyword in forbidden_keywords:
            if re.search(r'\b' + keyword + r'\b', query_without_strings, re.IGNORECASE):
                return {
                    "error": "This tool only supports read-only queries. Prohibited keywords like CREATE, MERGE, DELETE, SET, etc., are not allowed."
                }

        try:
            debug_log(f"Executing Cypher query: {cypher_query}")
            with self.db_manager.get_driver().session() as session:
                result = session.run(cypher_query)
                # Convert results to a list of dictionaries for clean JSON serialization.
                records = [record.data() for record in result]
                
                return {
                    "success": True,
                    "query": cypher_query,
                    "record_count": len(records),
                    "results": records
                }
        
        except CypherSyntaxError as e:
            debug_log(f"Cypher syntax error: {str(e)}")
            return {
                "error": "Cypher syntax error.",
                "details": str(e),
                "query": cypher_query
            }
        except Exception as e:
            debug_log(f"Error executing Cypher query: {str(e)}")
            return {
                "error": "An unexpected error occurred while executing the query.",
                "details": str(e)
            }
    
    def find_dead_code_tool(self, **args) -> Dict[str, Any]:
        """Tool to find potentially dead code across the entire project."""
        exclude_decorated_with = args.get("exclude_decorated_with", [])
        try:
            debug_log("Finding dead code.")
            results = self.code_finder.find_dead_code(exclude_decorated_with=exclude_decorated_with)
            
            return {
                "success": True,
                "query_type": "dead_code",
                "results": results
            }
        except Exception as e:
            debug_log(f"Error finding dead code: {str(e)}")
            return {"error": f"Failed to find dead code: {str(e)}"}

    def calculate_cyclomatic_complexity_tool(self, **args) -> Dict[str, Any]:
        """Tool to calculate cyclomatic complexity for a given function."""
        function_name = args.get("function_name")
        file_path = args.get("file_path")

        try:
            debug_log(f"Calculating cyclomatic complexity for function: {function_name}")
            results = self.code_finder.get_cyclomatic_complexity(function_name, file_path)
            
            response = {
                "success": True,
                "function_name": function_name,
                "results": results
            }
            if file_path:
                response["file_path"] = file_path
            
            return response
        except Exception as e:
            debug_log(f"Error calculating cyclomatic complexity: {str(e)}")
            return {"error": f"Failed to calculate cyclomatic complexity: {str(e)}"}

    def find_most_complex_functions_tool(self, **args) -> Dict[str, Any]:
        """Tool to find the most complex functions."""
        limit = args.get("limit", 10)
        try:
            debug_log(f"Finding the top {limit} most complex functions.")
            results = self.code_finder.find_most_complex_functions(limit)
            return {
                "success": True,
                "limit": limit,
                "results": results
            }
        except Exception as e:
            debug_log(f"Error finding most complex functions: {str(e)}")
            return {"error": f"Failed to find most complex functions: {str(e)}"}

    def list_indexed_repositories_tool(self, **args) -> Dict[str, Any]:
        """Tool to list indexed repositories."""
        try:
            debug_log("Listing indexed repositories.")
            results = self.code_finder.list_indexed_repositories()
            return {
                "success": True,
                "repositories": results
            }
        except Exception as e:
            debug_log(f"Error listing indexed repositories: {str(e)}")
            return {"error": f"Failed to list indexed repositories: {str(e)}"}

    def delete_repository_tool(self, **args) -> Dict[str, Any]:
        """Tool to delete a repository from the graph."""
        repo_path = args.get("repo_path")
        try:
            debug_log(f"Deleting repository: {repo_path}")
            self.graph_builder.delete_repository_from_graph(repo_path)
            return {
                "success": True,
                "message": f"Repository '{repo_path}' deleted successfully."
            }
        except Exception as e:
            debug_log(f"Error deleting repository: {str(e)}")
            return {"error": f"Failed to delete repository: {str(e)}"}

    def visualize_graph_query_tool(self, **args) -> Dict[str, Any]:
        """Tool to generate a visualization URL (Neo4j URL or FalkorDB HTML file)."""
        cypher_query = args.get("cypher_query")
        if not cypher_query:
            return {"error": "Cypher query cannot be empty."}

        # Check DB Type: FalkorDBManager vs DatabaseManager
        is_falkor = "FalkorDB" in self.db_manager.__class__.__name__

        if is_falkor:
            try:
                data_nodes = []
                data_edges = []
                seen_nodes = set()

                with self.db_manager.get_driver().session() as session:
                    result = session.run(cypher_query)
                    for record in result:
                        # Iterate all values in the record to find Nodes and Relationships
                        # record is a FalkorDBRecord (dict-like), values() works
                        for val in record.values():
                            # Process Node
                            if hasattr(val, 'labels') and hasattr(val, 'id'):
                                nid = val.id
                                if nid not in seen_nodes:
                                    seen_nodes.add(nid)
                                    lbl = list(val.labels)[0] if val.labels else "Node"
                                    props = getattr(val, 'properties', {}) or {}
                                    name = props.get('name', str(nid))
                                    
                                    color = "#97c2fc"
                                    if "Repository" in val.labels: color = "#ffb3ba"
                                    elif "File" in val.labels: color = "#baffc9"
                                    elif "Class" in val.labels: color = "#bae1ff"
                                    elif "Function" in val.labels: color = "#ffffba"
                                    
                                    data_nodes.append({
                                        "id": nid, "label": name, "group": lbl, 
                                        "title": str(props), "color": color
                                    })
                            
                            # Process Relationship
                            # FalkorDB client relationship objects have src_node/dest_node (ids) and relation (type)
                            # We check for both standard names just in case
                            src = getattr(val, 'src_node', None)
                            if src is None: src = getattr(val, 'start_node', None)
                            
                            dst = getattr(val, 'dest_node', None)
                            if dst is None: dst = getattr(val, 'end_node', None)

                            if src is not None and dst is not None:
                                lbl = getattr(val, 'relation', None) or getattr(val, 'type', 'REL')
                                data_edges.append({
                                    "from": src,
                                    "to": dst,
                                    "label": lbl,
                                    "arrows": "to"
                                })

                # Generate HTML
                html_content = f"""
<!DOCTYPE html>
<html>
<head>
  <title>CodeGraphContext Visualization</title>
  <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
  <style type="text/css">
    #mynetwork {{ width: 100%; height: 100vh; border: 1px solid lightgray; }}
  </style>
</head>
<body>
  <div id="mynetwork"></div>
  <script type="text/javascript">
    var nodes = new vis.DataSet({json.dumps(data_nodes)});
    var edges = new vis.DataSet({json.dumps(data_edges)});
    var container = document.getElementById('mynetwork');
    var data = {{ nodes: nodes, edges: edges }};
    var options = {{
        nodes: {{ shape: 'dot', size: 16 }},
        physics: {{ stabilization: false }},
        layout: {{ improvedLayout: false }}
    }};
    var network = new vis.Network(container, data, options);
  </script>
</body>
</html>
"""
                # filename = f"codegraph_viz_{int(datetime.now().timestamp())}.html"
                filename = f"codegraph_viz.html"
                out_path = Path(os.getcwd()) / filename
                with open(out_path, "w") as f:
                    f.write(html_content)
                
                return {
                    "success": True,
                    "visualization_url": f"file://{out_path}",
                    "message": f"Visualization generated at {out_path}. Open this file in your browser."
                }

            except Exception as e:
                debug_log(f"Error generating FalkorDB visualization: {str(e)}")
                return {"error": f"Failed to generate visualization: {str(e)}"}

        else:
            # Neo4j fallback
            try:
                encoded_query = urllib.parse.quote(cypher_query)
                visualization_url = f"http://localhost:7474/browser/?cmd=edit&arg={encoded_query}"
                
                return {
                    "success": True,
                    "visualization_url": visualization_url,
                    "message": "Open the URL in your browser to visualize the graph query. The query will be pre-filled for editing."
                }
            except Exception as e:
                debug_log(f"Error generating visualization URL: {str(e)}")
                return {"error": f"Failed to generate visualization URL: {str(e)}"}

    def list_watched_paths_tool(self, **args) -> Dict[str, Any]:
        """Tool to list all currently watched directory paths."""
        try:
            paths = self.code_watcher.list_watched_paths()
            return {"success": True, "watched_paths": paths}
        except Exception as e:
            return {"error": f"Failed to list watched paths: {str(e)}"}

    def unwatch_directory_tool(self, **args) -> Dict[str, Any]:
        """Tool to stop watching a directory."""
        path = args.get("path")
        if not path:
            return {"error": "Path is a required argument."}
        # The watcher class handles the logic of checking if the path is watched
        # and returns an error dictionary if not, so we can just call it.
        return self.code_watcher.unwatch_directory(path)

    def watch_directory_tool(self, **args) -> Dict[str, Any]:
        """
        Tool implementation to start watching a directory for changes.
        This tool is now smart: it checks if the path exists and if it has already been indexed.
        """
        path = args.get("path")
        if not path:
            return {"error": "Path is a required argument."}

        path_obj = Path(path).resolve()
        path_str = str(path_obj)

        # 1. Validate the path before the try...except block
        if not path_obj.is_dir():
            return {
                "success": True,
                "status": "path_not_found",
                "message": f"Path '{path_str}' does not exist or is not a directory."
            }
        try:
            # Check if already watching
            if path_str in self.code_watcher.watched_paths:
                return {"success": True, "message": f"Already watching directory: {path_str}"}

            # 2. Check if the repository is already indexed
            indexed_repos = self.list_indexed_repositories_tool().get("repositories", [])
            is_already_indexed = any(Path(repo["path"]).resolve() == path_obj for repo in indexed_repos)

            # 3. Decide whether to perform an initial scan
            if is_already_indexed:
                # If already indexed, just start the watcher without a scan
                self.code_watcher.watch_directory(path_str, perform_initial_scan=False)
                return {
                    "success": True,
                    "message": f"Path '{path_str}' is already indexed. Now watching for live changes."
                }
            else:
                # If not indexed, perform the scan AND start the watcher
                scan_job_result = self.add_code_to_graph_tool(path=path_str, is_dependency=False)
                if "error" in scan_job_result:
                    return scan_job_result
                
                self.code_watcher.watch_directory(path_str, perform_initial_scan=True)
                
                return {
                    "success": True,
                    "message": f"Path '{path_str}' was not indexed. Started initial scan and now watching for live changes.",
                    "job_id": scan_job_result.get("job_id"),
                    "details": "Use check_job_status to monitor the initial scan."
                }
            
        except Exception as e:
            error_logger(f"Failed to start watching directory {path}: {e}")
            return {"error": f"Failed to start watching directory: {str(e)}"}        
    
    def add_code_to_graph_tool(self, **args) -> Dict[str, Any]:
        """
        Tool implementation to index a directory of code.

        This creates a background job and runs the indexing asynchronously
        so the AI assistant can continue to be responsive.
        """
        path = args.get("path")
        is_dependency = args.get("is_dependency", False)
        
        try:
            path_obj = Path(path).resolve()

            if not path_obj.exists():
                return {
                    "success": True,
                    "status": "path_not_found",
                    "message": f"Path '{path}' does not exist."
                }

            # Prevent re-indexing the same repository.
            indexed_repos = self.list_indexed_repositories_tool().get("repositories", [])
            for repo in indexed_repos:
                if Path(repo["path"]).resolve() == path_obj:
                    return {
                        "success": False,
                        "message": f"Repository '{path}' is already indexed."
                    }
            
            # Estimate time and create a job for the user to track.
            total_files, estimated_time = self.graph_builder.estimate_processing_time(path_obj)
            job_id = self.job_manager.create_job(str(path_obj), is_dependency)
            self.job_manager.update_job(job_id, total_files=total_files, estimated_duration=estimated_time)
            
            # Create the coroutine for the background task and schedule it on the main event loop.
            coro = self.graph_builder.build_graph_from_path_async(
                path_obj, is_dependency, job_id
            )
            asyncio.run_coroutine_threadsafe(coro, self.loop)
            
            debug_log(f"Started background job {job_id} for path: {str(path_obj)}, is_dependency: {is_dependency}")
            
            return {
                "success": True, "job_id": job_id,
                "message": f"Background processing started for {str(path_obj)}",
                "estimated_files": total_files,
                "estimated_duration_seconds": round(estimated_time, 2),
                "estimated_duration_human": f"{int(estimated_time // 60)}m {int(estimated_time % 60)}s" if estimated_time >= 60 else f"{int(estimated_time)}s",
                "instructions": f"Use 'check_job_status' with job_id '{job_id}' to monitor progress"
            }
        
        except Exception as e:
            debug_log(f"Error creating background job: {str(e)}")
            return {"error": f"Failed to start background processing: {str(e)}"}
    
    def add_package_to_graph_tool(self, **args) -> Dict[str, Any]:
        """Tool to add a package to the graph by auto-discovering its location"""
        package_name = args.get("package_name")
        language = args.get("language")
        is_dependency = args.get("is_dependency", True)

        if not language:
            return {"error": "The 'language' parameter is required."}

        try:
            # Check if the package is already indexed
            indexed_repos = self.list_indexed_repositories_tool().get("repositories", [])
            for repo in indexed_repos:
                if repo.get("is_dependency") and (repo.get("name") == package_name or repo.get("name") == f"{package_name}.py"):
                    return {
                        "success": False,
                        "message": f"Package '{package_name}' is already indexed."
                    }

            package_path = get_local_package_path(package_name, language)
            
            if not package_path:
                return {"error": f"Could not find package '{package_name}' for language '{language}'. Make sure it's installed."}
            
            if not os.path.exists(package_path):
                return {"error": f"Package path '{package_path}' does not exist"}
            
            path_obj = Path(package_path)
            
            total_files, estimated_time = self.graph_builder.estimate_processing_time(path_obj)
            
            job_id = self.job_manager.create_job(package_path, is_dependency)
            
            self.job_manager.update_job(job_id, total_files=total_files, estimated_duration=estimated_time)
            
            coro = self.graph_builder.build_graph_from_path_async(
                path_obj, is_dependency, job_id
            )
            asyncio.run_coroutine_threadsafe(coro, self.loop)
            
            debug_log(f"Started background job {job_id} for package: {package_name} at {package_path}, is_dependency: {is_dependency}")
            
            return {
                "success": True, "job_id": job_id, "package_name": package_name,
                "discovered_path": package_path,
                "message": f"Background processing started for package '{package_name}'",
                "estimated_files": total_files,
                "estimated_duration_seconds": round(estimated_time, 2),
                "estimated_duration_human": f"{int(estimated_time // 60)}m {int(estimated_time % 60)}s" if estimated_time >= 60 else f"{int(estimated_time)}s",
                "instructions": f"Use 'check_job_status' with job_id '{job_id}' to monitor progress"
            }
        
        except Exception as e:
            debug_log(f"Error creating background job for package {package_name}: {str(e)}")
            return {"error": f"Failed to start background processing for package '{package_name}': {str(e)}"}
    
    def check_job_status_tool(self, **args) -> Dict[str, Any]:
        """Tool to check job status"""
        job_id = args.get("job_id")
        if not job_id:
            return {"error": "Job ID is a required argument."}
                
        try:
            job = self.job_manager.get_job(job_id)
            
            if not job:
                return {
                    "success": True, # Return success to avoid generic error wrapper
                    "status": "not_found",
                    "message": f"Job with ID '{job_id}' not found. The ID may be incorrect or the job may have been cleared after a server restart."
                }
            
            job_dict = asdict(job)
            
            if job.status == JobStatus.RUNNING:
                if job.estimated_time_remaining:
                    remaining = job.estimated_time_remaining
                    job_dict["estimated_time_remaining_human"] = (
                        f"{int(remaining // 60)}m {int(remaining % 60)}s" 
                        if remaining >= 60 else f"{int(remaining)}s"
                    )
                
                if job.start_time:
                    elapsed = (datetime.now() - job.start_time).total_seconds()
                    job_dict["elapsed_time_human"] = (
                        f"{int(elapsed // 60)}m {int(elapsed % 60)}s" 
                        if elapsed >= 60 else f"{int(elapsed)}s"
                    )
            
            elif job.status == JobStatus.COMPLETED and job.start_time and job.end_time:
                duration = (job.end_time - job.start_time).total_seconds()
                job_dict["actual_duration_human"] = (
                    f"{int(duration // 60)}m {int(duration % 60)}s" 
                    if duration >= 60 else f"{int(duration)}s"
                )
            
            job_dict["start_time"] = job.start_time.strftime("%Y-%m-%d %H:%M:%S")
            if job.end_time:
                job_dict["end_time"] = job.end_time.strftime("%Y-%m-%d %H:%M:%S")
            
            job_dict["status"] = job.status.value
            
            return {"success": True, "job": job_dict}
        
        except Exception as e:
            debug_log(f"Error checking job status: {str(e)}")
            return {"error": f"Failed to check job status: {str(e)}"}
    
    def list_jobs_tool(self) -> Dict[str, Any]:
        """Tool to list all jobs"""
        try:
            jobs = self.job_manager.list_jobs()
            
            jobs_data = []
            for job in jobs:
                job_dict = asdict(job)
                job_dict["status"] = job.status.value
                job_dict["start_time"] = job.start_time.strftime("%Y-%m-%d %H:%M:%S")
                if job.end_time:
                    job_dict["end_time"] = job.end_time.strftime("%Y-%m-%d %H:%M:%S")
                jobs_data.append(job_dict)
            
            jobs_data.sort(key=lambda x: x["start_time"], reverse=True)
            
            return {"success": True, "jobs": jobs_data, "total_jobs": len(jobs_data)}
        
        except Exception as e:
            debug_log(f"Error listing jobs: {str(e)}")
            return {"error": f"Failed to list jobs: {str(e)}"}
    
    def analyze_code_relationships_tool(self, **args) -> Dict[str, Any]:
        """Tool to analyze code relationships"""
        query_type = args.get("query_type")
        target = args.get("target")
        context = args.get("context")

        if not query_type or not target:
            return {
                "error": "Both 'query_type' and 'target' are required",
                "supported_query_types": [
                    "find_callers", "find_callees", "find_importers", "who_modifies",
                    "class_hierarchy", "overrides", "dead_code", "call_chain",
                    "module_deps", "variable_scope", "find_complexity"
                ]
            }
        
        try:
            debug_log(f"Analyzing relationships: {query_type} for {target}")
            results = self.code_finder.analyze_code_relationships(query_type, target, context)
            
            return {
                "success": True, "query_type": query_type, "target": target,
                "context": context, "results": results
            }
        
        except Exception as e:
            debug_log(f"Error analyzing relationships: {str(e)}")
            return {"error": f"Failed to analyze relationships: {str(e)}"}
        
    @staticmethod
    def _normalize(text: str) -> str:
        return text.lower().replace("_", " ").strip()

    def find_code_tool(self, **args) -> Dict[str, Any]:
        """Tool to find relevant code snippets"""
        query = args.get("query")
        fuzzy_search = args.get("fuzzy_search", DEFAULT_FUZZY_SEARCH)
        edit_distance = args.get("edit_distance", DEFAULT_EDIT_DISTANCE)

        if fuzzy_search:
            query = self._normalize(query)
            
        try:
            debug_log(f"Finding code for query: {query} with fuzzy_search={fuzzy_search}, edit_distance={edit_distance}")
            results = self.code_finder.find_related_code(query, fuzzy_search, edit_distance)

            return {"success": True, "query": query, "results": results}
        
        except Exception as e:
            debug_log(f"Error finding code: {str(e)}")
            return {"error": f"Failed to find code: {str(e)}"}
    

    async def handle_tool_call(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Routes a tool call from the AI assistant to the appropriate handler function. 
        
        Args:
            tool_name: The name of the tool to execute.
            args: A dictionary of arguments for the tool.

        Returns:
            A dictionary containing the result of the tool execution.
        """
        tool_map: Dict[str, Coroutine] = {
            "add_package_to_graph": self.add_package_to_graph_tool,
            "find_dead_code": self.find_dead_code_tool,
            "find_code": self.find_code_tool,
            "analyze_code_relationships": self.analyze_code_relationships_tool,
            "watch_directory": self.watch_directory_tool,
            "execute_cypher_query": self.execute_cypher_query_tool,
            "add_code_to_graph": self.add_code_to_graph_tool,
            "check_job_status": self.check_job_status_tool,
            "list_jobs": self.list_jobs_tool,
            "calculate_cyclomatic_complexity": self.calculate_cyclomatic_complexity_tool,
            "find_most_complex_functions": self.find_most_complex_functions_tool,
            "list_indexed_repositories": self.list_indexed_repositories_tool,
            "delete_repository": self.delete_repository_tool,
            "visualize_graph_query": self.visualize_graph_query_tool,
            "list_watched_paths": self.list_watched_paths_tool,
            "unwatch_directory": self.unwatch_directory_tool
        }
        handler = tool_map.get(tool_name)
        if handler:
            # Run the synchronous tool function in a separate thread to avoid
            # blocking the main asyncio event loop.
            return await asyncio.to_thread(handler, **args)
        else:
            return {"error": f"Unknown tool: {tool_name}"}

    async def run(self):
        """
        Runs the main server loop, listening for JSON-RPC requests from stdin.
        
        This loop continuously reads lines from stdin, parses them as JSON-RPC
        requests, and routes them to the appropriate handlers (e.g., initialize,
        tools/list, tools/call). The response is then printed to stdout.
        """
        debug_logger("MCP Server is running. Waiting for requests...")
        self.code_watcher.start()
        
        loop = asyncio.get_event_loop()
        while True:
            try:
                # Read a request from the standard input.
                line = await loop.run_in_executor(None, sys.stdin.readline)
                if not line:
                    debug_logger("Client disconnected (EOF received). Shutting down.")
                    break
                
                request = json.loads(line.strip())
                method = request.get('method')
                params = request.get('params', {})
                request_id = request.get('id')
                
                response = {}
                # Route the request based on the JSON-RPC method.
                if method == 'initialize':
                    response = {
                        "jsonrpc": "2.0", "id": request_id,
                        "result": {
                            "protocolVersion": "2025-03-26",
                            "serverInfo": {
                                "name": "CodeGraphContext", "version": "0.1.0",
                                "systemPrompt": LLM_SYSTEM_PROMPT
                            },
                            "capabilities": {"tools": {"listTools": True}},
                        }
                    }
                elif method == 'tools/list':
                    # Return the list of tools defined in _init_tools.
                    response = {
                        "jsonrpc": "2.0", "id": request_id,
                        "result": {"tools": list(self.tools.values())}
                    }
                elif method == 'tools/call':
                    # Execute a tool call and return the result.
                    tool_name = params.get('name')
                    args = params.get('arguments', {})
                    result = await self.handle_tool_call(tool_name, args)
                    
                    if "error" in result:
                        response = {
                            "jsonrpc": "2.0", "id": request_id,
                            "error": {"code": -32000, "message": "Tool execution error", "data": result}
                        }
                    else:
                        response = {
                            "jsonrpc": "2.0", "id": request_id,
                            "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
                        }
                elif method == 'notifications/initialized':
                    # This is a notification, no response needed.
                    pass
                else:
                    # Handle unknown methods.
                    if request_id is not None:
                        response = {
                            "jsonrpc": "2.0", "id": request_id,
                            "error": {"code": -32601, "message": f"Method not found: {method}"}
                        }
                
                # Send the response to standard output if it's not a notification.
                if request_id is not None and response:
                    print(json.dumps(response), flush=True)

            except Exception as e:
                error_logger(f"Error processing request: {e}\n{traceback.format_exc()}")
                request_id = "unknown"
                if 'request' in locals() and isinstance(request, dict):
                    request_id = request.get('id', "unknown")

                error_response = {
                    "jsonrpc": "2.0", "id": request_id,
                    "error": {"code": -32603, "message": f"Internal error: {str(e)}", "data": traceback.format_exc()}
                }
                print(json.dumps(error_response), flush=True)

    def shutdown(self):
        """Gracefully shuts down the server and its components."""
        debug_logger("Shutting down server...")
        self.code_watcher.stop()
        self.db_manager.close_driver()
