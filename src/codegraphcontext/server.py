# src/codegraphcontext/server.py
import asyncio
import json
import logging
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
from .core.database import DatabaseManager
from .core.jobs import JobManager, JobStatus
from .core.watcher import CodeWatcher
from .tools.graph_builder import GraphBuilder
from .tools.code_finder import CodeFinder
from .tools.import_extractor import ImportExtractor
from .tools.graph_exporter import GraphExporter
from .utils.debug_log import debug_log

logger = logging.getLogger(__name__)

class MCPServer:
    """
    The main MCP Server class.
    
    This class orchestrates all the major components of the application, including:
    - Database connection management (`DatabaseManager`)
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
            # Initialize the database manager and establish a connection early
            # to fail fast if credentials are wrong.
            self.db_manager = DatabaseManager()
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
        self.import_extractor = ImportExtractor()
        self.graph_exporter = GraphExporter(self.db_manager)
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
                    "properties": { "query": {"type": "string", "description": "Keyword or phrase to search for"} },
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
                "description": "Add a Python package to Neo4j graph by discovering its location. Returns immediately with job ID.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "package_name": {"type": "string", "description": "Name of the Python package to add (e.g., 'requests')"},
                        "is_dependency": {"type": "boolean", "description": "Mark as a dependency", "default": True}
                    },
                    "required": ["package_name"]
                }
            },
            "list_imports": {
                "name": "list_imports",
                "description": "Extract all package imports from code files in a directory or file",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to file or directory to analyze"},
                        "language": {"type": "string", "description": "Programming language (python, javascript, etc.)", "default": "python"},
                        "recursive": {"type": "boolean", "description": "Whether to analyze subdirectories recursively", "default": True}
                    },
                    "required": ["path"]
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
            "export_graph_visualization": {
                "name": "export_graph_visualization",
                "description": "Export code graph visualization in various formats (PNG, SVG, PDF, HTML, JSON, GraphML). Supports multiple layout algorithms and filtering options.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "output_path": {"type": "string", "description": "Path where the exported file will be saved."},
                        "format": {"type": "string", "description": "Export format.", "enum": ["png", "svg", "pdf", "html", "json", "graphml"], "default": "png"},
                        "repository_path": {"type": "string", "description": "Optional: Filter graph to specific repository path."},
                        "layout": {"type": "string", "description": "Graph layout algorithm.", "enum": ["spring", "circular", "kamada_kawai", "planar", "random", "shell", "spectral"], "default": "spring"},
                        "include_dependencies": {"type": "boolean", "description": "Include dependency nodes in the visualization.", "default": True},
                        "max_nodes": {"type": "integer", "description": "Maximum number of nodes to include.", "default": 1000},
                        "width": {"type": "integer", "description": "Image width in pixels.", "default": 1200},
                        "height": {"type": "integer", "description": "Image height in pixels.", "default": 800},
                        "show_labels": {"type": "boolean", "description": "Show node labels in the visualization.", "default": True},
                        "dpi": {"type": "integer", "description": "DPI for high-quality image exports.", "default": 300}
                    },
                    "required": ["output_path"]
                }
            }
        }    

    def get_database_status(self) -> dict:
        """Returns the current connection status of the Neo4j database."""
        return {"connected": self.db_manager.is_connected()}
        
    def get_local_package_path(self, package_name: str) -> Optional[str]:
        """
        Finds the local installation path of a Python package.

        This method uses `importlib` to locate a package and determines its root
        directory, handling both regular packages (directories with __init__.py)
        and single-file modules.

        Args:
            package_name: The name of the package to locate (e.g., "requests").

        Returns:
            The absolute path to the package's directory as a string, or None if not found.
        """
        try:
            debug_log(f"Getting local path for package: {package_name}")
            
            module = importlib.import_module(package_name)
            
            if hasattr(module, '__file__') and module.__file__:
                module_file = Path(module.__file__)
                debug_log(f"Module file: {module_file}")

                if module_file.name == '__init__.py':
                    # For a package, the path is the parent directory of __init__.py
                    package_path = str(module_file.parent)
                elif package_name in stdlibs.module_names:
                    # For a standard library single file module, the path is the file itself
                    package_path = str(module_file)
                else:
                    # For other single-file modules, assume the parent directory is the container
                    package_path = str(module_file.parent)

                debug_log(f"Determined package path: {package_path}")
                return package_path

            elif hasattr(module, '__path__'):
                # This handles namespace packages which may not have an __init__.py
                if isinstance(module.__path__, list) and module.__path__:
                    package_path = str(Path(module.__path__[0]))
                    debug_log(f"Package path from __path__: {package_path}")
                    return package_path
                else:
                    # Fallback for other __path__ formats
                    package_path = str(Path(str(module.__path__)))
                    debug_log(f"Package path from __path__ (str): {package_path}")
                    return package_path
            
            debug_log(f"Could not determine path for {package_name}")
            return None
            
        except ImportError as e:
            debug_log(f"Could not import {package_name}: {e}")
            return None
        except Exception as e:
            debug_log(f"Error getting local path for {package_name}: {e}")
            return None
        
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

    def watch_directory_tool(self, **args) -> Dict[str, Any]:
        """
        Tool implementation to start watching a directory for changes.

        This process involves two steps:
        1. Kicking off a background job to do an initial scan of the directory.
        2. Starting the file watcher to catch live changes.
        """
        path = args.get("path")
        if not path or not Path(path).is_dir():
            return {"error": f"Invalid path provided: {path}. Must be a directory."}

        try:
            # First, ensure the code is added/scanned by calling the appropriate tool.
            scan_job_result = self.add_code_to_graph_tool(path=path, is_dependency=False)
            if "error" in scan_job_result:
                return scan_job_result

            # Now, start the file system watcher.
            watch_result = self.code_watcher.watch_directory(path)
            
            # Combine results into a single, informative response.
            final_result = {
                "success": True,
                "message": f"Initial scan started for {path}. Now watching for live changes.",
                "job_id": scan_job_result.get("job_id"),
                "details": watch_result
            }
            return final_result
            
        except Exception as e:
            logger.error(f"Failed to start watching directory {path}: {e}")
            return {"error": f"Failed to start watching directory: {str(e)}"}
        
    def list_imports_tool(self, **args) -> Dict[str, Any]:
        """Tool to list all imports from code files"""        
        path = args.get("path")
        language = args.get("language", "python")
        recursive = args.get("recursive", True)
        all_imports = set()
        file_extensions = {
            'python': ['.py'], 'javascript': ['.js', '.jsx', '.mjs'],
            'typescript': ['.ts', '.tsx'], 'java': ['.java'],
        }
        
        extensions = file_extensions.get(language, ['.py'])
        extract_func = {
            'python': self.import_extractor.extract_python_imports,
            'javascript': self.import_extractor.extract_javascript_imports,
            'typescript': self.import_extractor.extract_javascript_imports,
            'java': self.import_extractor.extract_java_imports,
        }.get(language, self.import_extractor.extract_python_imports)
        
        try:
            path_obj = Path(path)
            
            if path_obj.is_file():
                if any(str(path_obj).endswith(ext) for ext in extensions):
                    all_imports.update(extract_func(str(path_obj)))
            elif path_obj.is_dir():
                pattern = "**/*" if recursive else "*"
                for ext in extensions:
                    for file_path in path_obj.glob(f"{pattern}{ext}"):
                        if file_path.is_file():
                            all_imports.update(extract_func(str(file_path)))
            else:
                return {"error": f"Path {path} does not exist"}
            
            # Removed standard library filtering as per user request.
            # if language == 'python':
            #     # Get the list of stdlib modules for the current Python version
            #     stdlib_modules = set(stdlibs.module_names)
            #     all_imports = all_imports - stdlib_modules
            
            return {
                "imports": sorted(list(all_imports)), "language": language,
                "path": path, "count": len(all_imports)
            }
        
        except Exception as e:
            return {"error": f"Failed to analyze imports: {str(e)}"}
    
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
                return {"error": f"Path {path} does not exist"}

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
        """Tool to add a Python package to Neo4j graph by auto-discovering its location"""
        package_name = args.get("package_name")
        is_dependency = args.get("is_dependency", True)
        
        try:
            # Check if the package is already indexed
            indexed_repos = self.list_indexed_repositories_tool().get("repositories", [])
            for repo in indexed_repos:
                if repo.get("is_dependency") and (repo.get("name") == package_name or repo.get("name") == f"{package_name}.py"):
                    return {
                        "success": False,
                        "message": f"Package '{package_name}' is already indexed."
                    }

            package_path = self.get_local_package_path(package_name)
            
            if not package_path:
                return {"error": f"Could not find package '{package_name}'. Make sure it's installed."}
            
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
                
        try:
            job = self.job_manager.get_job(job_id)
            
            if not job:
                return {"error": f"Job {job_id} not found"}
            
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

    def find_code_tool(self, **args) -> Dict[str, Any]:
        """Tool to find relevant code snippets"""
        query = args.get("query")
        
        try:
            debug_log(f"Finding code for query: {query}")
            results = self.code_finder.find_related_code(query)
            
            return {"success": True, "query": query, "results": results}
        
        except Exception as e:
            debug_log(f"Error finding code: {str(e)}")
            return {"error": f"Failed to find code: {str(e)}"}

    def export_graph_visualization_tool(self, **args) -> Dict[str, Any]:
        """Tool to export graph visualizations in various formats"""
        try:
            debug_log(f"Exporting graph visualization with args: {args}")
            return self.graph_exporter.export_graph_tool(**args)
        
        except Exception as e:
            debug_log(f"Error exporting graph: {str(e)}")
            return {"error": f"Failed to export graph: {str(e)}"}
    

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
            "list_imports": self.list_imports_tool,
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
            "export_graph_visualization": self.export_graph_visualization_tool
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
        logger.info("MCP Server is running. Waiting for requests...")
        self.code_watcher.start()
        
        loop = asyncio.get_event_loop()
        while True:
            try:
                # Read a request from the standard input.
                line = await loop.run_in_executor(None, sys.stdin.readline)
                if not line:
                    logger.info("Client disconnected (EOF received). Shutting down.")
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
                logger.error(f"Error processing request: {e}\n{traceback.format_exc()}")
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
        logger.info("Shutting down server...")
        self.code_watcher.stop()
        self.db_manager.close_driver()
