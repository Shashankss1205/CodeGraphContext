# src/codegraphcontext/cli/cli_helpers.py
import asyncio
import json
import urllib.parse
from pathlib import Path
import time
from rich.console import Console
from rich.table import Table

from ..core import get_database_manager
from ..core.jobs import JobManager
from ..tools.code_finder import CodeFinder
from ..tools.graph_builder import GraphBuilder
from ..tools.package_resolver import get_local_package_path

console = Console()


def _initialize_services():
    """Initializes and returns core service managers."""
    console.print("[dim]Initializing services and database connection...[/dim]")
    try:
        db_manager = get_database_manager()
    except ValueError as e:
        console.print(f"[bold red]Database Configuration Error:[/bold red] {e}")
        return None, None, None

    try:
        db_manager.get_driver()
    except ValueError as e:
        console.print(f"[bold red]Database Connection Error:[/bold red] {e}")
        console.print("Please ensure your Neo4j credentials are correct and the database is running.")
        return None, None, None
    
    # The GraphBuilder requires an event loop, even for synchronous-style execution
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    graph_builder = GraphBuilder(db_manager, JobManager(), loop)
    code_finder = CodeFinder(db_manager)
    console.print("[dim]Services initialized.[/dim]")
    return db_manager, graph_builder, code_finder


def index_helper(path: str):
    """Synchronously indexes a repository."""
    time_start = time.time()
    services = _initialize_services()
    if not all(services):
        return

    db_manager, graph_builder, code_finder = services
    path_obj = Path(path).resolve()

    if not path_obj.exists():
        console.print(f"[red]Error: Path does not exist: {path_obj}[/red]")
        db_manager.close_driver()
        return

    indexed_repos = code_finder.list_indexed_repositories()
    repo_exists = any(Path(repo["path"]).resolve() == path_obj for repo in indexed_repos)
    
    if repo_exists:
        # Check if the repository actually has files (not just an empty node from interrupted indexing)
        try:
            with db_manager.get_driver().session() as session:
                result = session.run(
                    "MATCH (r:Repository {path: $path})-[:CONTAINS]->(f:File) RETURN count(f) as file_count",
                    path=str(path_obj)
                )
                record = result.single()
                file_count = record["file_count"] if record else 0
                
                if file_count > 0:
                    console.print(f"[yellow]Repository '{path}' is already indexed with {file_count} files. Skipping.[/yellow]")
                    console.print("[dim]💡 Tip: Use 'cgc index --force' to re-index[/dim]")
                    db_manager.close_driver()
                    return
                else:
                    console.print(f"[yellow]Repository '{path}' exists but has no files (likely interrupted). Re-indexing...[/yellow]")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not check file count: {e}. Proceeding with indexing...[/yellow]")

    console.print(f"Starting indexing for: {path_obj}")
    console.print("[yellow]This may take a few minutes for large repositories...[/yellow]")

    async def do_index():
        await graph_builder.build_graph_from_path_async(path_obj, is_dependency=False)

    try:
        asyncio.run(do_index())
        time_end = time.time()
        elapsed = time_end - time_start
        console.print(f"[green]Successfully finished indexing: {path} in {elapsed:.2f} seconds[/green]")
        
        # Check if auto-watch is enabled
        try:
            from codegraphcontext.cli.config_manager import get_config_value
            auto_watch = get_config_value('ENABLE_AUTO_WATCH')
            if auto_watch and str(auto_watch).lower() == 'true':
                console.print("\n[cyan]🔍 ENABLE_AUTO_WATCH is enabled. Starting watcher...[/cyan]")
                db_manager.close_driver()  # Close before starting watcher
                watch_helper(path)  # This will block the terminal
                return  # watch_helper handles its own cleanup
        except Exception as e:
            console.print(f"[yellow]Warning: Could not check ENABLE_AUTO_WATCH: {e}[/yellow]")
            
    except Exception as e:
        console.print(f"[bold red]An error occurred during indexing:[/bold red] {e}")
    finally:
        db_manager.close_driver()


def add_package_helper(package_name: str, language: str):
    """Synchronously indexes a package."""
    services = _initialize_services()
    if not all(services):
        return

    db_manager, graph_builder, code_finder = services

    package_path_str = get_local_package_path(package_name, language)
    if not package_path_str:
        console.print(f"[red]Error: Could not find package '{package_name}' for language '{language}'.[/red]")
        db_manager.close_driver()
        return

    package_path = Path(package_path_str)
    
    indexed_repos = code_finder.list_indexed_repositories()
    if any(repo.get("name") == package_name for repo in indexed_repos if repo.get("is_dependency")):
        console.print(f"[yellow]Package '{package_name}' is already indexed. Skipping.[/yellow]")
        db_manager.close_driver()
        return

    console.print(f"Starting indexing for package '{package_name}' at: {package_path}")
    console.print("[yellow]This may take a few minutes...[/yellow]")

    async def do_index():
        await graph_builder.build_graph_from_path_async(package_path, is_dependency=True)

    try:
        asyncio.run(do_index())
        console.print(f"[green]Successfully finished indexing package: {package_name}[/green]")
    except Exception as e:
        console.print(f"[bold red]An error occurred during package indexing:[/bold red] {e}")
    finally:
        db_manager.close_driver()


def list_repos_helper():
    """Lists all indexed repositories."""
    services = _initialize_services()
    if not all(services):
        return
    
    db_manager, _, code_finder = services
    
    try:
        repos = code_finder.list_indexed_repositories()
        if not repos:
            console.print("[yellow]No repositories indexed yet.[/yellow]")
            return

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name", style="dim")
        table.add_column("Path")
        table.add_column("Type")

        for repo in repos:
            repo_type = "Dependency" if repo.get("is_dependency") else "Project"
            table.add_row(repo["name"], repo["path"], repo_type)
        
        console.print(table)
    except Exception as e:
        console.print(f"[bold red]An error occurred:[/bold red] {e}")
    finally:
        db_manager.close_driver()


def delete_helper(repo_path: str):
    """Deletes a repository from the graph."""
    services = _initialize_services()
    if not all(services):
        return

    db_manager, graph_builder, _ = services
    
    try:
        if graph_builder.delete_repository_from_graph(repo_path):
            console.print(f"[green]Successfully deleted repository: {repo_path}[/green]")
        else:
            console.print(f"[yellow]Repository not found in graph: {repo_path}[/yellow]")
            console.print("[dim]Tip: Use 'cgc list' to see available repositories.[/dim]")
    except Exception as e:
        console.print(f"[bold red]An error occurred:[/bold red] {e}")
    finally:
        db_manager.close_driver()


def cypher_helper(query: str):
    """Executes a read-only Cypher query."""
    services = _initialize_services()
    if not all(services):
        return

    db_manager, _, _ = services
    
    # Replicating safety checks from MCPServer
    forbidden_keywords = ['CREATE', 'MERGE', 'DELETE', 'SET', 'REMOVE', 'DROP', 'CALL apoc']
    if any(keyword in query.upper() for keyword in forbidden_keywords):
        console.print("[bold red]Error: This command only supports read-only queries.[/bold red]")
        db_manager.close_driver()
        return

    try:
        with db_manager.get_driver().session() as session:
            result = session.run(query)
            
            # Helper for serialization
            def _serialize_graph_types(obj):
                # Handle Nodes
                if hasattr(obj, 'labels'):
                    return {
                        "id": obj.id,
                        "labels": list(obj.labels),
                        "properties": getattr(obj, 'properties', {}) or {}
                    }
                # Handle Relationships
                if hasattr(obj, 'type'):
                    # Handle varying driver implementations for type
                    rel_type = "RELATED"
                    if hasattr(obj, 'type'): rel_type = obj.type
                    elif hasattr(obj, 'relation'): rel_type = obj.relation
                    elif hasattr(obj, 'label'): rel_type = obj.label
                    
                    return {
                        "id": obj.id,
                        "type": rel_type,
                        "start_node_id": obj.start_node.id,
                        "end_node_id": obj.end_node.id,
                        "properties": getattr(obj, 'properties', {}) or {}
                    }
                # Handle Paths
                if hasattr(obj, 'nodes') and hasattr(obj, 'relationships'):
                    return {
                        "nodes": [_serialize_graph_types(n) for n in obj.nodes],
                        "relationships": [_serialize_graph_types(r) for r in obj.relationships]
                    }
                # Fallback
                return str(obj)

            # Manually process records if .data() is not available or insufficient
            records = []
            for record in result:
                # If record is dict-like (Neo4j)
                if hasattr(record, 'data'):
                    records.append(record.data())
                # If record is key-value based but not a standard Record object
                elif hasattr(record, 'keys') and callable(record.keys):
                     records.append(dict(record.items()))
                # Fallback for list-like records (RedisGraph/FalkorDB default)
                else:
                    # Try to map if keys are available in result object?
                    # Some drivers don't attach keys to records easily.
                    records.append(list(record))

            console.print(json.dumps(records, indent=2, default=_serialize_graph_types))
    except Exception as e:
        console.print(f"[bold red]An error occurred while executing query:[/bold red] {e}")
    finally:
        db_manager.close_driver()


import webbrowser

def visualize_helper(query: str):
    """Generates a visualization."""
    services = _initialize_services()
    if not all(services):
        return

    db_manager, _, _ = services
    
    # Check if FalkorDB
    if "FalkorDB" in db_manager.__class__.__name__:
        _visualize_falkordb(db_manager, query)
    else:
        try:
            encoded_query = urllib.parse.quote(query)
            visualization_url = f"http://localhost:7474/browser/?cmd=edit&arg={encoded_query}"
            console.print("[green]Graph visualization URL:[/green]")
            console.print(visualization_url)
            console.print("Open the URL in your browser to see the graph.")
        except Exception as e:
            console.print(f"[bold red]An error occurred while generating URL:[/bold red] {e}")
        finally:
            db_manager.close_driver()

def _visualize_falkordb(db_manager, query: str = None):
    """
    Starts the live visualization server for FalkorDB.
    """
    try:
        from ..viz import start_viz_server
        console.print("[green]Starting live visualization server...[/green]")
        console.print("[dim]This provides an interactive Neo4j Browser-like interface for FalkorDB.[/dim]")
        
        # This blocks until the server is stopped (Ctrl+C)
        start_viz_server(db_manager, query)
        
    except ImportError as e:
        console.print(f"[bold red]Visualization Error:[/bold red] Could not import visualization module: {e}")
        console.print("Please ensure fastapi and uvicorn are installed: pip install fastapi uvicorn")
    except Exception as e:
        console.print(f"[bold red]Visualization failed:[/bold red] {e}")
    finally:
        # The db_manager is closed by visualize_helper, but if start_viz_server handles it,
        # we should be careful. Actually visualize_helper has a finally block calling close_driver.
        # However, start_viz_server needs the driver open.
        # Since start_viz_server blocks, when it returns (Ctrl+C), we can let visualize_helper close it.
        pass



def reindex_helper(path: str):
    """Force re-index by deleting and rebuilding the repository."""
    time_start = time.time()
    services = _initialize_services()
    if not all(services):
        return

    db_manager, graph_builder, code_finder = services
    path_obj = Path(path).resolve()

    if not path_obj.exists():
        console.print(f"[red]Error: Path does not exist: {path_obj}[/red]")
        db_manager.close_driver()
        return

    # Check if already indexed
    indexed_repos = code_finder.list_indexed_repositories()
    repo_exists = any(Path(repo["path"]).resolve() == path_obj for repo in indexed_repos)
    
    if repo_exists:
        console.print(f"[yellow]Deleting existing index for: {path_obj}[/yellow]")
        try:
            graph_builder.delete_repository_from_graph(str(path_obj))
            console.print("[green]✓[/green] Deleted old index")
        except Exception as e:
            console.print(f"[red]Error deleting old index: {e}[/red]")
            db_manager.close_driver()
            return
    
    console.print(f"[cyan]Re-indexing: {path_obj}[/cyan]")
    console.print("[yellow]This may take a few minutes for large repositories...[/yellow]")

    async def do_index():
        await graph_builder.build_graph_from_path_async(path_obj, is_dependency=False)

    try:
        asyncio.run(do_index())
        time_end = time.time()
        elapsed = time_end - time_start
        console.print(f"[green]Successfully re-indexed: {path} in {elapsed:.2f} seconds[/green]")
    except Exception as e:
        console.print(f"[bold red]An error occurred during re-indexing:[/bold red] {e}")
    finally:
        db_manager.close_driver()


def update_helper(path: str):
    """Update/refresh index for a path (alias for reindex)."""
    console.print("[cyan]Updating repository index...[/cyan]")
    reindex_helper(path)


def clean_helper():
    """Remove orphaned nodes and relationships from the database."""
    services = _initialize_services()
    if not all(services):
        return

    db_manager, _, _ = services
    
    console.print("[cyan]🧹 Cleaning database (removing orphaned nodes)...[/cyan]")
    
    try:
        with db_manager.get_driver().session() as session:
            # Find and delete orphaned nodes (nodes not connected to any repository)
            # Using OPTIONAL MATCH for FalkorDB compatibility
            query = """
            MATCH (n)
            WHERE NOT (n:Repository)
            OPTIONAL MATCH path = (n)-[*]-(r:Repository)
            WITH n, path
            WHERE path IS NULL
            WITH n LIMIT 1000
            DETACH DELETE n
            RETURN count(n) as deleted
            """
            result = session.run(query)
            record = result.single()
            deleted_count = record["deleted"] if record else 0
            
            if deleted_count > 0:
                console.print(f"[green]✓[/green] Deleted {deleted_count} orphaned nodes")
            else:
                console.print("[green]✓[/green] No orphaned nodes found")
            
            # Clean up any duplicate relationships (if any)
            console.print("[dim]Checking for duplicate relationships...[/dim]")
            # Note: This is database-specific and might not work for all backends
            
        console.print("[green]✅ Database cleanup complete![/green]")
    except Exception as e:
        console.print(f"[bold red]An error occurred during cleanup:[/bold red] {e}")
    finally:
        db_manager.close_driver()


def stats_helper(path: str = None):
    """Show indexing statistics for a repository or overall."""
    services = _initialize_services()
    if not all(services):
        return

    db_manager, _, code_finder = services
    
    try:
        if path:
            # Stats for specific repository
            path_obj = Path(path).resolve()
            console.print(f"[cyan]📊 Statistics for: {path_obj}[/cyan]\n")
            
            with db_manager.get_driver().session() as session:
                # Get repository node
                repo_query = """
                MATCH (r:Repository {path: $path})
                RETURN r
                """
                result = session.run(repo_query, path=str(path_obj))
                if not result.single():
                    console.print(f"[red]Repository not found: {path_obj}[/red]")
                    return
                
                # Get stats
                stats_query = """
                MATCH (r:Repository {path: $path})-[:CONTAINS]->(f:File)
                WITH r, count(f) as file_count, f
                OPTIONAL MATCH (f)-[:CONTAINS]->(func:Function)
                OPTIONAL MATCH (f)-[:CONTAINS]->(cls:Class)
                OPTIONAL MATCH (f)-[:IMPORTS]->(m:Module)
                RETURN 
                    file_count,
                    count(DISTINCT func) as function_count,
                    count(DISTINCT cls) as class_count,
                    count(DISTINCT m) as module_count
                """
                result = session.run(stats_query, path=str(path_obj))
                record = result.single()
                
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("Metric", style="cyan")
                table.add_column("Count", style="green", justify="right")
                
                table.add_row("Files", str(record["file_count"] if record else 0))
                table.add_row("Functions", str(record["function_count"] if record else 0))
                table.add_row("Classes", str(record["class_count"] if record else 0))
                table.add_row("Imported Modules", str(record["module_count"] if record else 0))
                
                console.print(table)
        else:
            # Overall stats
            console.print("[cyan]📊 Overall Database Statistics[/cyan]\n")
            
            with db_manager.get_driver().session() as session:
                # Get overall counts
                stats_query = """
                MATCH (r:Repository)
                WITH count(r) as repo_count
                MATCH (f:File)
                WITH repo_count, count(f) as file_count
                MATCH (func:Function)
                WITH repo_count, file_count, count(func) as function_count
                MATCH (cls:Class)
                WITH repo_count, file_count, function_count, count(cls) as class_count
                MATCH (m:Module)
                RETURN 
                    repo_count,
                    file_count,
                    function_count,
                    class_count,
                    count(m) as module_count
                """
                result = session.run(stats_query)
                record = result.single()
                
                if record:
                    table = Table(show_header=True, header_style="bold magenta")
                    table.add_column("Metric", style="cyan")
                    table.add_column("Count", style="green", justify="right")
                    
                    table.add_row("Repositories", str(record["repo_count"]))
                    table.add_row("Files", str(record["file_count"]))
                    table.add_row("Functions", str(record["function_count"]))
                    table.add_row("Classes", str(record["class_count"]))
                    table.add_row("Modules", str(record["module_count"]))
                    
                    console.print(table)
                else:
                    console.print("[yellow]No data indexed yet.[/yellow]")
                    
    except Exception as e:
        console.print(f"[bold red]An error occurred:[/bold red] {e}")
    finally:
        db_manager.close_driver()


def watch_helper(path: str):
    """Watch a directory for changes and auto-update the graph (blocking mode)."""
    import logging
    from ..core.watcher import CodeWatcher
    
    # Suppress verbose watchdog DEBUG logs
    logging.getLogger('watchdog').setLevel(logging.WARNING)
    logging.getLogger('watchdog.observers').setLevel(logging.WARNING)
    logging.getLogger('watchdog.observers.inotify_buffer').setLevel(logging.WARNING)
    
    services = _initialize_services()
    if not all(services):
        return

    db_manager, graph_builder, code_finder = services
    path_obj = Path(path).resolve()

    if not path_obj.exists():
        console.print(f"[red]Error: Path does not exist: {path_obj}[/red]")
        db_manager.close_driver()
        return
    
    if not path_obj.is_dir():
        console.print(f"[red]Error: Path must be a directory: {path_obj}[/red]")
        db_manager.close_driver()
        return

    console.print(f"[bold cyan]🔍 Watching {path_obj} for changes...[/bold cyan]")
    
    # Check if already indexed
    indexed_repos = code_finder.list_indexed_repositories()
    is_indexed = any(Path(repo["path"]).resolve() == path_obj for repo in indexed_repos)
    
    # Create watcher instance
    job_manager = JobManager()
    watcher = CodeWatcher(graph_builder, job_manager)
    
    try:
        # Start the observer thread
        watcher.start()
        
        # Add the directory to watch
        if is_indexed:
            console.print("[green]✓[/green] Already indexed (no initial scan needed)")
            watcher.watch_directory(str(path_obj), perform_initial_scan=False)
        else:
            console.print("[yellow]⚠[/yellow]  Not indexed yet. Performing initial scan...")
            
            # Index the repository first (like MCP does)
            async def do_index():
                await graph_builder.build_graph_from_path_async(path_obj, is_dependency=False)
            
            asyncio.run(do_index())
            console.print("[green]✓[/green] Initial scan complete")
            
            # Now start watching (without another scan)
            watcher.watch_directory(str(path_obj), perform_initial_scan=False)
        
        console.print("[bold green]👀 Monitoring for file changes...[/bold green] (Press Ctrl+C to stop)")
        console.print("[dim]💡 Tip: Open a new terminal window to continue working[/dim]\n")
        
        # Block here and keep the watcher running
        import threading
        stop_event = threading.Event()
        
        try:
            stop_event.wait()  # Wait indefinitely until interrupted
        except KeyboardInterrupt:
            console.print("\n[yellow]🛑 Stopping watcher...[/yellow]")
            
    except KeyboardInterrupt:
        console.print("\n[yellow]🛑 Stopping watcher...[/yellow]")
    except Exception as e:
        console.print(f"[bold red]An error occurred:[/bold red] {e}")
    finally:
        watcher.stop()
        db_manager.close_driver()
        console.print("[green]✓[/green] Watcher stopped. Graph is up to date.")



def unwatch_helper(path: str):
    """Stop watching a directory."""
    console.print(f"[yellow]⚠️  Note: 'cgc unwatch' only works when the watcher is running via MCP server.[/yellow]")
    console.print(f"[dim]For CLI watch mode, simply press Ctrl+C in the watch terminal.[/dim]")
    console.print(f"\n[cyan]Path specified:[/cyan] {Path(path).resolve()}")


def list_watching_helper():
    """List all directories currently being watched."""
    console.print(f"[yellow]⚠️  Note: 'cgc watching' only works when the watcher is running via MCP server.[/yellow]")
    console.print(f"[dim]For CLI watch mode, check the terminal where you ran 'cgc watch'.[/dim]")
    console.print(f"\n[cyan]To see watched directories in MCP mode:[/cyan]")
    console.print(f"  1. Start the MCP server: cgc mcp start")
    console.print(f"  2. Use the 'list_watched_paths' MCP tool from your IDE")
