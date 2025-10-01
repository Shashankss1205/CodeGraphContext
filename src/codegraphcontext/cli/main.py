# src/codegraphcontext/cli/main.py
"""
This module defines the command-line interface (CLI) for the CodeGraphContext application.
It uses the Typer library to create a user-friendly and well-documented CLI.

Commands:
- setup: Runs an interactive wizard to configure the Neo4j database connection.
- start: Launches the main MCP server.
- tool: A placeholder for directly calling server tools (for debugging).
- help: Displays help information.
- version: Show the installed version.
"""
import typer
from rich.console import Console
import asyncio
import logging
import json
import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from importlib.metadata import version as pkg_version, PackageNotFoundError
from codegraphcontext.server import MCPServer
from .setup_wizard import run_setup_wizard

# Set the log level for the noisy neo4j logger to WARNING to keep the output clean.
logging.getLogger("neo4j").setLevel(logging.WARNING)

# Initialize the Typer app and Rich console for formatted output.
app = typer.Typer(
    name="cgc",
    help="CodeGraphContext: An MCP server for AI-powered code analysis.",
    add_completion=False,
)
console = Console(stderr=True)

# Configure basic logging for the application.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')


def get_version() -> str:
    """
    Try to read version from the installed package metadata.
    Fallback to a dev version if not installed.
    """
    try:
        return pkg_version("codegraphcontext")  # must match [project].name in pyproject.toml
    except PackageNotFoundError:
        return "0.0.0 (dev)"


@app.command()
def setup():
    """
    Runs the interactive setup wizard to configure the server and database connection.
    This helps users set up a local Docker-based Neo4j instance or connect to a remote one.
    """
    run_setup_wizard()

@app.command()
def start():
    """
    Starts the CodeGraphContext MCP server, which listens for JSON-RPC requests from stdin.
    It first attempts to load Neo4j credentials from various sources before starting.
    """
    console.print("[bold green]Starting CodeGraphContext Server...[/bold green]")

    # The server needs Neo4j credentials. It attempts to load them in the following order of priority:
    # 1. From a local `mcp.json` file in the current working directory.
    # 2. From a global `.env` file at `~/.codegraphcontext/.env`.
    # 3. From any `.env` file found by searching upwards from the current directory.

    # 1. Prefer loading environment variables from mcp.json in the current directory.
    mcp_file_path = Path.cwd() / "mcp.json"
    if mcp_file_path.exists():
        try:
            with open(mcp_file_path, "r") as f:
                mcp_config = json.load(f)

            server_env = mcp_config.get("mcpServers", {}).get("CodeGraphContext", {}).get("env", {})
            for key, value in server_env.items():
                os.environ[key] = value
            console.print("[green]Loaded Neo4j credentials from local mcp.json.[/green]")
        except Exception as e:
            console.print(f"[bold red]Error loading mcp.json:[/bold red] {e}")
            console.print("[yellow]Attempting to start server without mcp.json environment variables.[/yellow]")
    else:
        # 2. If no local mcp.json, try to load from the global config directory.
        global_env_path = Path.home() / ".codegraphcontext" / ".env"
        if global_env_path.exists():
            try:
                load_dotenv(dotenv_path=global_env_path)
                console.print(f"[green]Loaded Neo4j credentials from global .env file: {global_env_path}[/green]")
            except Exception as e:
                console.print(f"[bold red]Error loading global .env file from {global_env_path}:[/bold red] {e}")
                console.print("[yellow]Attempting to start server without .env environment variables.[/yellow]")
        else:
            # 3. Fallback: try to load from any .env file found by searching up the directory tree.
            try:
                dotenv_path = find_dotenv(usecwd=True, raise_error_if_not_found=False)
                if dotenv_path:
                    load_dotenv(dotenv_path)
                    console.print(f"[green]Loaded Neo4j credentials from discovered .env file: {dotenv_path}[/green]")
                else:
                    console.print("[yellow]No local mcp.json or global .env file found. Attempting to start server without explicit Neo4j credentials.[/yellow]")
            except Exception as e:
                console.print(f"[bold red]Error loading .env file:[/bold red] {e}")
                console.print("[yellow]Attempting to start server without .env environment variables.[/yellow]")

    server = None
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        # Initialize and run the main server.
        server = MCPServer(loop=loop)
        loop.run_until_complete(server.run())
    except ValueError as e:
        # This typically happens if credentials are still not found after all checks.
        console.print(f"[bold red]Configuration Error:[/bold red] {e}")
        console.print("Please run `cgc setup` to configure the server.")
    except KeyboardInterrupt:
        # Handle graceful shutdown on Ctrl+C.
        console.print("\n[bold yellow]Server stopped by user.[/bold yellow]")
    finally:
        # Ensure server and event loop are properly closed.
        if server:
            server.shutdown()
        loop.close()


@app.command()
def tool(
    name: str = typer.Argument(..., help="The name of the tool to call."),
    args: str = typer.Argument("{}", help="A JSON string of arguments for the tool."),
):
    """
    Directly call a CodeGraphContext tool from the command line.

    IMPORTANT: This is a placeholder for debugging and does not connect to a running
    server. It creates a new, temporary server instance for each call, so it cannot
    be used to check the status of jobs started by `cgc start`.
    """
    console.print(f"Calling tool [bold cyan]{name}[/bold cyan] with args: {args}")
    console.print("[yellow]Note: This is a placeholder for direct tool invocation.[/yellow]")

@app.command()
def help(ctx: typer.Context):
    """Show the main help message and exit."""
    root_ctx = ctx.parent or ctx
    typer.echo(root_ctx.get_help())


@app.command("version")
def version_cmd():
    """Show the application version."""
    console.print(f"CodeGraphContext [bold cyan]{get_version()}[/bold cyan]")


@app.command("export")
def export_cmd(
    output_path: str = typer.Argument(..., help="Path where the exported file will be saved"),
    format: str = typer.Option("png", "--format", "-f", 
                              help="Export format: png, svg, pdf, html, json, graphml"),
    repository_path: str = typer.Option(None, "--repository", "-r", 
                                       help="Filter graph to specific repository path"),
    layout: str = typer.Option("spring", "--layout", "-l",
                              help="Graph layout algorithm: spring, circular, kamada_kawai, planar, random, shell, spectral"),
    include_dependencies: bool = typer.Option(True, "--include-deps/--exclude-deps",
                                            help="Include dependency nodes in the visualization"),
    max_nodes: int = typer.Option(1000, "--max-nodes", "-n",
                                 help="Maximum number of nodes to include"),
    width: int = typer.Option(1200, "--width", "-w",
                             help="Image width in pixels"),
    height: int = typer.Option(800, "--height", "-h",
                              help="Image height in pixels"),
    show_labels: bool = typer.Option(True, "--labels/--no-labels",
                                    help="Show node labels in the visualization"),
    dpi: int = typer.Option(300, "--dpi",
                           help="DPI for high-quality image exports")
):
    """Export a code graph visualization in various formats."""
    from codegraphcontext.core.database import DatabaseManager
    from codegraphcontext.tools.graph_exporter import GraphExporter, check_dependencies
    
    # Check dependencies
    deps = check_dependencies()
    format_lower = format.lower()
    
    if format_lower in ["png", "svg", "pdf"] and not deps["matplotlib"]:
        console.print("[bold red]Error:[/bold red] Matplotlib and NetworkX are required for static image exports.")
        console.print("Install with: [cyan]pip install 'codegraphcontext[visualization]'[/cyan]")
        raise typer.Exit(1)
    
    if format_lower == "html" and not deps["plotly"]:
        console.print("[bold red]Error:[/bold red] Plotly is required for HTML exports.")
        console.print("Install with: [cyan]pip install 'codegraphcontext[visualization]'[/cyan]")
        raise typer.Exit(1)
    
    try:
        # Initialize database connection
        db_manager = DatabaseManager()
        exporter = GraphExporter(db_manager)
        
        console.print(f"[green]Exporting graph visualization...[/green]")
        console.print(f"Format: [cyan]{format}[/cyan]")
        console.print(f"Output: [cyan]{output_path}[/cyan]")
        if repository_path:
            console.print(f"Repository: [cyan]{repository_path}[/cyan]")
        
        # Export the graph
        result = exporter.export_graph_tool(
            output_path=output_path,
            format=format_lower,
            repository_path=repository_path,
            layout=layout,
            include_dependencies=include_dependencies,
            max_nodes=max_nodes,
            width=width,
            height=height,
            show_labels=show_labels,
            dpi=dpi
        )
        
        if result["success"]:
            console.print(f"[bold green]✅ Export successful![/bold green]")
            console.print(f"File saved to: [cyan]{result['result']['output_path']}[/cyan]")
            console.print(f"Nodes: [yellow]{result['result']['node_count']}[/yellow], "
                         f"Edges: [yellow]{result['result']['edge_count']}[/yellow]")
            if 'file_size' in result['result']:
                file_size = result['result']['file_size']
                if file_size > 1024 * 1024:
                    console.print(f"File size: [yellow]{file_size / (1024 * 1024):.1f} MB[/yellow]")
                else:
                    console.print(f"File size: [yellow]{file_size / 1024:.1f} KB[/yellow]")
        else:
            console.print(f"[bold red]❌ Export failed:[/bold red] {result['error']}")
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version_: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show the application version and exit.",
        is_eager=True,
    ),
):
    """
    Main entry point for the cgc CLI application.
    If no subcommand is provided, it displays a welcome message with instructions.
    """
    if version_:
        console.print(f"CodeGraphContext [bold cyan]{get_version()}[/bold cyan]")
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        console.print("[bold green]👋 Welcome to CodeGraphContext (cgc)![/bold green]\n")
        console.print("👉 Run [cyan]cgc setup[/cyan] to configure the server and database.")
        console.print("👉 Run [cyan]cgc start[/cyan] to launch the server.")
        console.print("👉 Run [cyan]cgc help[/cyan] to see all available commands.\n")
        console.print("👉 Run [cyan]cgc --version[/cyan] to check the version.\n")
        console.print("👉 Running [green]codegraphcontext [white]works the same as using [green]cgc")
