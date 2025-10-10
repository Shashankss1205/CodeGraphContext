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
from rich.table import Table
from typing import Optional
import asyncio
import logging
import json
import os
import time
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
    add_completion=True,
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

def _load_credentials():
    """
    Loads Neo4j credentials from various sources into environment variables.
    Priority order:
    1. Local `mcp.json`
    2. Global `~/.codegraphcontext/.env`
    3. Any `.env` file found in the directory tree.
    """
    # 1. Prefer loading from mcp.json
    mcp_file_path = Path.cwd() / "mcp.json"
    if mcp_file_path.exists():
        try:
            with open(mcp_file_path, "r") as f:
                mcp_config = json.load(f)
            server_env = mcp_config.get("mcpServers", {}).get("CodeGraphContext", {}).get("env", {})
            for key, value in server_env.items():
                os.environ[key] = value
            console.print("[green]Loaded Neo4j credentials from local mcp.json.[/green]")
            return
        except Exception as e:
            console.print(f"[bold red]Error loading mcp.json:[/bold red] {e}")
    
    # 2. Try global .env file
    global_env_path = Path.home() / ".codegraphcontext" / ".env"
    if global_env_path.exists():
        try:
            load_dotenv(dotenv_path=global_env_path)
            console.print(f"[green]Loaded Neo4j credentials from global .env file: {global_env_path}[/green]")
            return
        except Exception as e:
            console.print(f"[bold red]Error loading global .env file from {global_env_path}:[/bold red] {e}")

    # 3. Fallback to any discovered .env
    try:
        dotenv_path = find_dotenv(usecwd=True, raise_error_if_not_found=False)
        if dotenv_path:
            load_dotenv(dotenv_path)
            console.print(f"[green]Loaded Neo4j credentials from discovered .env file: {dotenv_path}[/green]")
        else:
            console.print("[yellow]No local mcp.json or .env file found. Credentials may not be set.[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Error loading .env file:[/bold red] {e}")


@app.command()
def start():
    """
    Starts the CodeGraphContext MCP server, which listens for JSON-RPC requests from stdin.
    """
    console.print("[bold green]Starting CodeGraphContext Server...[/bold green]")
    _load_credentials()

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



def _run_tool(tool_name: str, tool_args: dict):
    """Helper function to run a tool and handle the server lifecycle."""
    _load_credentials()
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        server = MCPServer(loop=loop)

        result = loop.run_until_complete(server.handle_tool_call(tool_name, tool_args))
        
        if isinstance(result, dict) and "job_id" in result:
            job_id = result["job_id"]
            console.print(f"[green]Successfully started job '{job_id}' for tool '{tool_name}'.[/green]")
            console.print(f"Estimated files: {result.get('estimated_files')}, Estimated duration: {result.get('estimated_duration_human')}")
            console.print(f"\n[bold yellow]Polling for completion...[/bold yellow]")
            
            while True:
                time.sleep(2)
                status_result = loop.run_until_complete(server.handle_tool_call("check_job_status", {"job_id": job_id}))
                job_status = status_result.get("job", {}).get("status")
                processed_files = status_result.get("job", {}).get("processed_files", 0)
                total_files = status_result.get("job", {}).get("total_files", 0)
                console.print(f"Job status: {job_status} ({processed_files}/{total_files} files)")
                if job_status in ["completed", "failed", "cancelled"]:
                    console.print(json.dumps(status_result, indent=2))
                    break
        else:
            console.print(json.dumps(result, indent=2))

    except ValueError as e:
        console.print(f"[bold red]Configuration Error:[/bold red] {e}")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {e}")
    finally:
        if 'loop' in locals() and loop.is_running():
            loop.close()

@app.command()
def index(path: Optional[str] = typer.Argument(None, help="Path to the directory or file to index. Defaults to the current directory.")):
    """
    Indexes a directory or file by adding it to the code graph.
    If no path is provided, it indexes the current directory.
    """
    if path is None:
        # Use absolute current working directory to avoid ambiguous '.' path behavior
        path = str(Path.cwd())
    _run_tool("add_code_to_graph", {"path": path})

@app.command()
def delete(path: str = typer.Argument(..., help="Path of the repository to delete from the code graph.")):
    """
    Deletes a repository from the code graph.
    """
    _run_tool("delete_repository", {"repo_path": path})

@app.command()
def visualize(query: Optional[str] = typer.Argument(None, help="The Cypher query to visualize.")):
    """
    Generates a URL to visualize a Cypher query in the Neo4j Browser.
    If no query is provided, a default query will be used.
    """
    if query is None:
        query = "MATCH p=()-->() RETURN p"
    _run_tool("visualize_graph_query", {"cypher_query": query})

@app.command(name="list_repos")
def list_repos():
    """
    Lists all indexed repositories.
    """
    _run_tool("list_indexed_repositories", {})

@app.command(name="add_package")
def add_package(package_name: str = typer.Argument(..., help="Name of the package to add."), language: str = typer.Argument(..., help="Language of the package." )):
    """
    Adds a package to the code graph.
    """
    _run_tool("add_package_to_graph", {"package_name": package_name, "language": language})

@app.command()
def cypher(query: str = typer.Argument(..., help="The read-only Cypher query to execute.")):
    """
    Executes a read-only Cypher query.
    """
    _run_tool("execute_cypher_query", {"cypher_query": query})


@app.command(name="list_mcp_tools")
def list_mcp_tools():
    """
    Lists all available tools and their descriptions.
    """
    _load_credentials()
    console.print("[bold green]Available Tools:[/bold green]")
    try:
        # Instantiate the server to access the tool definitions.
        server = MCPServer()
        tools = server.tools.values()

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Tool Name", style="dim", width=30)
        table.add_column("Description")

        for tool in sorted(tools, key=lambda t: t['name']):
            table.add_row(tool['name'], tool['description'])

        console.print(table)

    except ValueError as e:
        console.print(f"[bold red]Error loading tools:[/bold red] {e}")
        console.print("Please ensure your Neo4j credentials are set up correctly (`cgc setup`), as they are needed to initialize the server.")
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred:[/bold red] {e}")


@app.command()
def help(ctx: typer.Context):
    """Show the main help message and exit."""
    root_ctx = ctx.parent or ctx
    typer.echo(root_ctx.get_help())


@app.command("version")
def version_cmd():
    """Show the application version."""
    console.print(f"CodeGraphContext [bold cyan]{get_version()}[/bold cyan]")


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
