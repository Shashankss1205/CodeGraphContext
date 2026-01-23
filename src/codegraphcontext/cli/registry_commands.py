# src/codegraphcontext/cli/registry_commands.py
"""
CLI commands for interacting with the CodeGraphContext bundle registry.
Allows users to list, search, download, and request bundles from the command line.
"""

import requests
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path
from typing import Optional, List, Dict, Any
import time

console = Console()

GITHUB_ORG = "CodeGraphContext"
GITHUB_REPO = "CodeGraphContext"
REGISTRY_API_URL = f"https://api.github.com/repos/{GITHUB_ORG}/{GITHUB_REPO}/releases"
MANIFEST_URL = f"https://github.com/{GITHUB_ORG}/{GITHUB_REPO}/releases/download/on-demand-bundles/manifest.json"


def fetch_available_bundles() -> List[Dict[str, Any]]:
    """
    Fetch all available bundles from GitHub Releases.
    Returns a list of bundle dictionaries with metadata.
    """
    all_bundles = []
    
    try:
        # 1. Fetch on-demand bundles from manifest
        try:
            response = requests.get(MANIFEST_URL, timeout=10)
            if response.status_code == 200:
                manifest = response.json()
                if manifest.get('bundles'):
                    for bundle in manifest['bundles']:
                        bundle['source'] = 'on-demand'
                        all_bundles.append(bundle)
        except Exception as e:
            console.print(f"[dim]Note: Could not fetch on-demand bundles: {e}[/dim]")
        
        # 2. Fetch weekly pre-indexed bundles
        try:
            response = requests.get(REGISTRY_API_URL, timeout=10)
            if response.status_code == 200:
                releases = response.json()
                
                # Find weekly releases (bundles-YYYYMMDD pattern)
                weekly_releases = [r for r in releases if r['tag_name'].startswith('bundles-') and r['tag_name'] != 'bundles-latest']
                
                if weekly_releases:
                    # Get the most recent weekly release
                    latest_weekly = weekly_releases[0]
                    
                    for asset in latest_weekly.get('assets', []):
                        if asset['name'].endswith('.cgc'):
                            # Parse bundle name
                            name_parts = asset['name'].replace('.cgc', '').split('-')
                            bundle = {
                                'name': name_parts[0],
                                'repo': f"{name_parts[0]}/{name_parts[0]}",  # Simplified
                                'bundle_name': asset['name'],
                                'version': name_parts[1] if len(name_parts) > 1 else 'latest',
                                'commit': name_parts[2] if len(name_parts) > 2 else 'unknown',
                                'size': f"{asset['size'] / 1024 / 1024:.1f}MB",
                                'download_url': asset['browser_download_url'],
                                'generated_at': asset['updated_at'],
                                'source': 'weekly'
                            }
                            all_bundles.append(bundle)
        except Exception as e:
            console.print(f"[dim]Note: Could not fetch weekly bundles: {e}[/dim]")
        
        # Remove duplicates (prefer on-demand over weekly)
        unique_bundles = {}
        for bundle in all_bundles:
            # Extract name from repo field (e.g., "pallets/flask" -> "flask")
            repo = bundle.get('repo', '')
            if '/' in repo:
                name = repo.split('/')[-1]  # Get the last part after /
            else:
                name = bundle.get('name', repo.split('/')[-1] if '/' in repo else 'unknown')
            
            # Add name to bundle if not present
            if 'name' not in bundle or bundle['name'] == 'unknown':
                bundle['name'] = name
            
            if name not in unique_bundles or bundle.get('source') == 'on-demand':
                unique_bundles[name] = bundle
        
        return list(unique_bundles.values())
    
    except Exception as e:
        console.print(f"[bold red]Error fetching bundles: {e}[/bold red]")
        return []


def list_bundles(verbose: bool = False):
    """Display all available bundles in a table."""
    console.print("[cyan]Fetching available bundles...[/cyan]")
    
    bundles = fetch_available_bundles()
    
    if not bundles:
        console.print("[yellow]No bundles found in registry.[/yellow]")
        console.print("[dim]The registry may be empty or unreachable.[/dim]")
        return
    
    # Create table
    table = Table(show_header=True, header_style="bold magenta", title="Available Bundles")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Repository", style="dim")
    table.add_column("Version", style="green")
    table.add_column("Size", justify="right")
    table.add_column("Source", style="yellow")
    
    if verbose:
        table.add_column("Download URL", style="blue", no_wrap=False)
    
    # Sort by name
    bundles.sort(key=lambda b: b.get('name', ''))
    
    for bundle in bundles:
        name = bundle.get('name', 'unknown')
        repo = bundle.get('repo', 'unknown')
        version = bundle.get('version', bundle.get('tag', 'latest'))
        size = bundle.get('size', 'unknown')
        source = bundle.get('source', 'unknown')
        
        if verbose:
            download_url = bundle.get('download_url', 'N/A')
            table.add_row(name, repo, version, size, source, download_url)
        else:
            table.add_row(name, repo, version, size, source)
    
    console.print(table)
    console.print(f"\n[dim]Total bundles: {len(bundles)}[/dim]")
    console.print("[dim]Use 'cgc registry download <name>' to download a bundle[/dim]")


def search_bundles(query: str):
    """Search for bundles matching the query."""
    console.print(f"[cyan]Searching for '{query}'...[/cyan]")
    
    bundles = fetch_available_bundles()
    
    if not bundles:
        console.print("[yellow]No bundles found in registry.[/yellow]")
        return
    
    # Filter bundles
    query_lower = query.lower()
    matching_bundles = [
        b for b in bundles
        if query_lower in b.get('name', '').lower() or
           query_lower in b.get('repo', '').lower() or
           query_lower in b.get('description', '').lower()
    ]
    
    if not matching_bundles:
        console.print(f"[yellow]No bundles found matching '{query}'[/yellow]")
        console.print("[dim]Try a different search term or use 'cgc registry list' to see all bundles[/dim]")
        return
    
    # Create table
    table = Table(show_header=True, header_style="bold magenta", title=f"Search Results for '{query}'")
    table.add_column("Name", style="cyan")
    table.add_column("Repository", style="dim")
    table.add_column("Version", style="green")
    table.add_column("Size", justify="right")
    
    for bundle in matching_bundles:
        name = bundle.get('name', 'unknown')
        repo = bundle.get('repo', 'unknown')
        version = bundle.get('version', bundle.get('tag', 'latest'))
        size = bundle.get('size', 'unknown')
        table.add_row(name, repo, version, size)
    
    console.print(table)
    console.print(f"\n[dim]Found {len(matching_bundles)} matching bundle(s)[/dim]")


def download_bundle(name: str, output_dir: Optional[str] = None, auto_load: bool = False):
    """Download a bundle from the registry."""
    console.print(f"[cyan]Looking for bundle '{name}'...[/cyan]")
    
    bundles = fetch_available_bundles()
    
    if not bundles:
        console.print("[bold red]Could not fetch bundle registry.[/bold red]")
        raise typer.Exit(code=1)
    
    # Find the bundle
    bundle = None
    for b in bundles:
        if b.get('name', '').lower() == name.lower():
            bundle = b
            break
    
    if not bundle:
        console.print(f"[bold red]Bundle '{name}' not found in registry.[/bold red]")
        console.print("[dim]Use 'cgc registry list' to see available bundles[/dim]")
        raise typer.Exit(code=1)
    
    # Get download URL
    download_url = bundle.get('download_url')
    if not download_url:
        console.print(f"[bold red]No download URL found for bundle '{name}'[/bold red]")
        raise typer.Exit(code=1)
    
    # Determine output path
    bundle_filename = bundle.get('bundle_name', f"{name}.cgc")
    if output_dir:
        output_path = Path(output_dir) / bundle_filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        output_path = Path.cwd() / bundle_filename
    
    # Check if already exists
    if output_path.exists():
        console.print(f"[yellow]Bundle already exists: {output_path}[/yellow]")
        if not typer.confirm("Overwrite?", default=False):
            console.print("[yellow]Download cancelled[/yellow]")
            if auto_load:
                console.print(f"[cyan]Using existing bundle for loading...[/cyan]")
                return str(output_path)
            return
        output_path.unlink()
    
    # Download with progress bar
    try:
        console.print(f"[cyan]Downloading {bundle_filename}...[/cyan]")
        console.print(f"[dim]From: {download_url}[/dim]")
        
        response = requests.get(download_url, stream=True, timeout=30)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"Downloading {bundle.get('size', 'unknown')}...", total=total_size)
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        progress.update(task, advance=len(chunk))
        
        console.print(f"[bold green]✓ Downloaded successfully: {output_path}[/bold green]")
        
        if auto_load:
            return str(output_path)
        else:
            console.print(f"[dim]Load with: cgc load {output_path}[/dim]")
    
    except requests.exceptions.RequestException as e:
        console.print(f"[bold red]Download failed: {e}[/bold red]")
        if output_path.exists():
            output_path.unlink()
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        if output_path.exists():
            output_path.unlink()
        raise typer.Exit(code=1)


def request_bundle(repo_url: str, wait: bool = False):
    """Request on-demand generation of a bundle."""
    console.print(f"[cyan]Requesting bundle generation for: {repo_url}[/cyan]")
    
    # Validate GitHub URL
    if not repo_url.startswith('https://github.com/'):
        console.print("[bold red]Invalid GitHub URL. Must start with 'https://github.com/'[/bold red]")
        raise typer.Exit(code=1)
    
    # For now, provide instructions to use the website
    # In the future, this could trigger the workflow via GitHub API
    console.print("\n[yellow]Note: Bundle generation requires GitHub authentication.[/yellow]")
    console.print("[cyan]Please use one of these methods:[/cyan]\n")
    
    console.print("1. [bold]Via Website (Recommended):[/bold]")
    console.print(f"   Visit: https://codegraphcontext.vercel.app")
    console.print(f"   Enter: {repo_url}")
    console.print(f"   Click 'Generate Bundle'\n")
    
    console.print("2. [bold]Via GitHub Actions (Manual):[/bold]")
    console.print(f"   Go to: https://github.com/{GITHUB_ORG}/{GITHUB_REPO}/actions")
    console.print(f"   Select: 'Generate Bundle On-Demand'")
    console.print(f"   Click: 'Run workflow'")
    console.print(f"   Enter: {repo_url}\n")
    
    console.print("[dim]Bundle generation typically takes 5-10 minutes.[/dim]")
    console.print("[dim]Use 'cgc registry list' to check when it's available.[/dim]")
    
    if wait:
        console.print("\n[yellow]Note: Automatic waiting not yet implemented.[/yellow]")
        console.print("[dim]Please check back in 5-10 minutes and use 'cgc registry download <name>'[/dim]")
