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
    if any(Path(repo["path"]).resolve() == path_obj for repo in indexed_repos):
        console.print(f"[yellow]Repository '{path}' is already indexed. Skipping.[/yellow]")
        db_manager.close_driver()
        return

    console.print(f"Starting indexing for: {path_obj}")
    console.print("[yellow]This may take a few minutes for large repositories...[/yellow]")

    async def do_index():
        await graph_builder.build_graph_from_path_async(path_obj, is_dependency=False)

    try:
        asyncio.run(do_index())
        time_end = time.time()
        elapsed = time_end - time_start
        console.print(f"[green]Successfully finished indexing: {path} in {elapsed:.2f} seconds[/green]")
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
        graph_builder.delete_repository_from_graph(repo_path)
        console.print(f"[green]Successfully deleted repository: {repo_path}[/green]")
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
            records = [record.data() for record in result]
            console.print(json.dumps(records, indent=2))
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
        _visualize_falkordb(db_manager)
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

def _visualize_falkordb(db_manager):
    console.print("[dim]Generating FalkorDB visualization (showing up to 500 relationships)...[/dim]")
    try:
        data_nodes = []
        data_edges = []
        
        with db_manager.get_driver().session() as session:
            # Fetch nodes and edges
            q = "MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 500"
            result = session.run(q)
            
            seen_nodes = set()
            
            for record in result:
                # record values are Node/Relationship objects from falkordb client
                n = record['n']
                r = record['r']
                m = record['m']
                
                # Process Node helper
                def process_node(node):
                    nid = getattr(node, 'id', -1)
                    labels = getattr(node, 'labels', [])
                    lbl = list(labels)[0] if labels else "Node"
                    props = getattr(node, 'properties', {})
                    name = props.get('name', str(nid))
                    
                    if nid not in seen_nodes:
                        seen_nodes.add(nid)
                        color = "#97c2fc" # Default blue
                        if "Repository" in labels: color = "#ffb3ba" # Red
                        elif "File" in labels: color = "#baffc9" # Green
                        elif "Class" in labels: color = "#bae1ff" # Light Blue
                        elif "Function" in labels: color = "#ffffba" # Yellow
                        elif "Package" in labels: color = "#ffdfba" # Orange
                        
                        data_nodes.append({
                            "id": nid, 
                            "label": name, 
                            "group": lbl, 
                            "title": str(props),
                            "color": color
                        })
                    return nid

                nid = process_node(n)
                mid = process_node(m)
                
                # Check Edge
                e_type = getattr(r, 'relation', '') or getattr(r, 'type', 'REL')
                data_edges.append({
                    "from": nid,
                    "to": mid,
                    "label": e_type,
                    "arrows": "to"
                })
        
        filename = "codegraph_viz.html"
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
  <title>CodeGraphContext Visualization</title>
  <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
  <style type="text/css">
    #mynetwork {{
      width: 100%;
      height: 100vh;
      border: 1px solid lightgray;
    }}
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
        
        out_path = Path(filename).resolve()
        with open(out_path, "w") as f:
            f.write(html_content)
            
        console.print(f"[green]Visualization generated at:[/green] {out_path}")
        console.print("Opening in default browser...")
        webbrowser.open(f"file://{out_path}")

    except Exception as e:
        console.print(f"[bold red]Visualization failed:[/bold red] {e}")
        import traceback
        traceback.print_exc()
    finally:
        db_manager.close_driver()


