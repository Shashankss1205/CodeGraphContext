"""
Graph Export Tool for CodeGraphContext

This module provides functionality to export code graph visualizations 
in various formats including PNG, SVG, PDF, HTML, JSON, and GraphML.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from ..core.database import DatabaseManager

def check_dependencies() -> Dict[str, bool]:
    """Check if optional visualization dependencies are available."""
    deps = {
        "matplotlib": False,
        "networkx": False,
        "plotly": False
    }
    
    try:
        import matplotlib
        deps["matplotlib"] = True
    except ImportError:
        pass
    
    try:
        import networkx
        deps["networkx"] = True
    except ImportError:
        pass
    
    try:
        import plotly
        deps["plotly"] = True
    except ImportError:
        pass
    
    return deps


class GraphExporter:
    """Export code graphs in various formats."""
    
    def __init__(self, db_manager: DatabaseManager):
        """Initialize the GraphExporter with a database manager."""
        self.db_manager = db_manager
        self.dependencies = check_dependencies()
    
    def export_graph_tool(self, **kwargs) -> Dict[str, Any]:
        """
        MCP tool interface for exporting graphs.
        
        Returns a tool result with success/error status.
        """
        try:
            result = self.export_graph(**kwargs)
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def export_graph(
        self,
        output_path: str,
        format: str = "png",
        repository_path: Optional[str] = None,
        layout: str = "spring",
        include_dependencies: bool = True,
        max_nodes: int = 1000,
        width: int = 1200,
        height: int = 800,
        show_labels: bool = True,
        dpi: int = 300
    ) -> Dict[str, Any]:
        """
        Export a code graph visualization.
        
        Args:
            output_path: Path where the file will be saved
            format: Export format (png, svg, pdf, html, json, graphml)
            repository_path: Optional filter for specific repository
            layout: Graph layout algorithm
            include_dependencies: Whether to include dependency nodes
            max_nodes: Maximum number of nodes to include
            width: Image width in pixels
            height: Image height in pixels
            show_labels: Whether to show node labels
            dpi: DPI for image exports
            
        Returns:
            Dictionary with export results and metadata
        """
        # Validate format
        supported_formats = ["png", "svg", "pdf", "html", "json", "graphml"]
        if format.lower() not in supported_formats:
            raise ValueError(f"Unsupported format: {format}. Supported: {supported_formats}")
        
        # Check dependencies for the requested format
        format_lower = format.lower()
        if format_lower in ["png", "svg", "pdf"] and not (self.dependencies["matplotlib"] and self.dependencies["networkx"]):
            raise ValueError("Matplotlib and NetworkX are required for static image exports. Install with: pip install 'codegraphcontext[visualization]'")
        
        if format_lower == "html" and not self.dependencies["plotly"]:
            raise ValueError("Plotly is required for HTML exports. Install with: pip install 'codegraphcontext[visualization]'")
        
        # Fetch graph data
        nodes, edges = self.fetch_graph_data(repository_path, include_dependencies, max_nodes)
        
        if not nodes:
            raise ValueError("No graph data found. Make sure the database is populated.")
        
        # Ensure output directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Export based on format
        result = {
            "output_path": str(Path(output_path).resolve()),
            "format": format_lower,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "layout": layout
        }
        
        if format_lower in ["png", "svg", "pdf"]:
            self._export_matplotlib(nodes, edges, output_path, format_lower, layout, width, height, show_labels, dpi)
        elif format_lower == "html":
            self._export_html(nodes, edges, output_path, layout, width, height, show_labels)
        elif format_lower == "json":
            self._export_json(nodes, edges, output_path)
        elif format_lower == "graphml":
            self._export_graphml(nodes, edges, output_path)
        
        # Add file size to result
        if os.path.exists(output_path):
            result["file_size"] = os.path.getsize(output_path)
        
        return result
    
    def fetch_graph_data(
        self, 
        repository_path: Optional[str] = None, 
        include_dependencies: bool = True,
        max_nodes: int = 1000
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Fetch graph data from Neo4j database.
        
        Returns:
            Tuple of (nodes, edges) lists
        """
        # Build the Cypher query
        query_parts = []
        params = {"max_nodes": max_nodes}
        
        if repository_path:
            query_parts.append("MATCH (n) WHERE n.file_path STARTS WITH $repo_path")
            params["repo_path"] = repository_path
        else:
            query_parts.append("MATCH (n)")
        
        if not include_dependencies:
            query_parts.append("WHERE NOT n:Dependency")
        
        query_parts.extend([
            "WITH n LIMIT $max_nodes",
            "MATCH (n)-[r]-(m)",
            "RETURN n, r, m"
        ])
        
        query = " ".join(query_parts)
        
        # Execute query
        with self.db_manager.get_session() as session:
            result = session.run(query, params)
            
            nodes_dict = {}
            edges = []
            
            for record in result:
                # Process nodes
                for node_key in ['n', 'm']:
                    if node_key in record:
                        node = record[node_key]
                        if node.id not in nodes_dict:
                            nodes_dict[node.id] = {
                                "id": node.id,
                                "labels": list(node.labels),
                                "properties": dict(node)
                            }
                
                # Process relationship
                if 'r' in record:
                    rel = record['r']
                    edges.append({
                        "source": rel.start_node.id,
                        "target": rel.end_node.id,
                        "type": rel.type,
                        "properties": dict(rel)
                    })
        
        nodes = list(nodes_dict.values())
        return nodes, edges
    
    def _export_matplotlib(
        self, 
        nodes: List[Dict], 
        edges: List[Dict], 
        output_path: str, 
        format: str,
        layout: str,
        width: int,
        height: int,
        show_labels: bool,
        dpi: int
    ):
        """Export using matplotlib and networkx."""
        import matplotlib.pyplot as plt
        import networkx as nx
        
        # Create NetworkX graph
        G = nx.Graph()
        
        # Add nodes
        for node in nodes:
            node_id = node["id"]
            label = node["properties"].get("name", f"Node_{node_id}")
            G.add_node(node_id, label=label, **node["properties"])
        
        # Add edges
        for edge in edges:
            G.add_edge(edge["source"], edge["target"], type=edge["type"])
        
        # Choose layout
        layout_functions = {
            "spring": nx.spring_layout,
            "circular": nx.circular_layout,
            "kamada_kawai": nx.kamada_kawai_layout,
            "planar": nx.planar_layout,
            "random": nx.random_layout,
            "shell": nx.shell_layout,
            "spectral": nx.spectral_layout
        }
        
        layout_func = layout_functions.get(layout, nx.spring_layout)
        
        try:
            pos = layout_func(G)
        except Exception:
            # Fallback to spring layout if chosen layout fails
            pos = nx.spring_layout(G)
        
        # Create figure
        plt.figure(figsize=(width/100, height/100), dpi=dpi)
        
        # Draw graph
        nx.draw_networkx_nodes(G, pos, node_color='lightblue', 
                              node_size=300, alpha=0.7)
        nx.draw_networkx_edges(G, pos, alpha=0.5, edge_color='gray')
        
        if show_labels:
            labels = {node: G.nodes[node].get('label', f'Node_{node}') 
                     for node in G.nodes()}
            nx.draw_networkx_labels(G, pos, labels, font_size=8)
        
        plt.title("Code Graph Visualization")
        plt.axis('off')
        plt.tight_layout()
        
        # Save based on format
        if format == "png":
            plt.savefig(output_path, format='png', dpi=dpi, bbox_inches='tight')
        elif format == "svg":
            plt.savefig(output_path, format='svg', bbox_inches='tight')
        elif format == "pdf":
            plt.savefig(output_path, format='pdf', bbox_inches='tight')
        
        plt.close()
    
    def _export_html(
        self, 
        nodes: List[Dict], 
        edges: List[Dict], 
        output_path: str,
        layout: str,
        width: int,
        height: int,
        show_labels: bool
    ):
        """Export interactive HTML visualization using Plotly."""
        import plotly.graph_objects as go
        import plotly.offline as pyo
        import networkx as nx
        
        # Create NetworkX graph for layout
        G = nx.Graph()
        for node in nodes:
            G.add_node(node["id"], **node["properties"])
        for edge in edges:
            G.add_edge(edge["source"], edge["target"])
        
        # Get layout positions
        layout_functions = {
            "spring": nx.spring_layout,
            "circular": nx.circular_layout,
            "kamada_kawai": nx.kamada_kawai_layout,
            "random": nx.random_layout,
            "shell": nx.shell_layout,
            "spectral": nx.spectral_layout
        }
        
        layout_func = layout_functions.get(layout, nx.spring_layout)
        try:
            pos = layout_func(G)
        except Exception:
            pos = nx.spring_layout(G)
        
        # Prepare edge traces
        edge_x = []
        edge_y = []
        for edge in edges:
            x0, y0 = pos[edge["source"]]
            x1, y1 = pos[edge["target"]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        edge_trace = go.Scatter(x=edge_x, y=edge_y,
                               line=dict(width=0.5, color='#888'),
                               hoverinfo='none',
                               mode='lines')
        
        # Prepare node traces
        node_x = []
        node_y = []
        node_text = []
        node_info = []
        
        for node in nodes:
            x, y = pos[node["id"]]
            node_x.append(x)
            node_y.append(y)
            
            label = node["properties"].get("name", f"Node_{node['id']}")
            node_text.append(label if show_labels else "")
            
            info = f"ID: {node['id']}<br>"
            info += f"Labels: {', '.join(node['labels'])}<br>"
            for key, value in node["properties"].items():
                if key != "name":
                    info += f"{key}: {value}<br>"
            node_info.append(info)
        
        node_trace = go.Scatter(x=node_x, y=node_y,
                               mode='markers+text' if show_labels else 'markers',
                               hoverinfo='text',
                               text=node_text,
                               hovertext=node_info,
                               textposition="middle center",
                               marker=dict(showscale=True,
                                         colorscale='YlGnBu',
                                         reversescale=True,
                                         color=[],
                                         size=10,
                                         colorbar=dict(
                                             thickness=15,
                                             len=0.5,
                                             x=1.01,
                                             title="Node Connections"
                                         ),
                                         line=dict(width=2)))
        
        # Color nodes by number of connections
        node_adjacencies = []
        for node in nodes:
            adjacencies = len([e for e in edges if e["source"] == node["id"] or e["target"] == node["id"]])
            node_adjacencies.append(adjacencies)
        
        node_trace.marker.color = node_adjacencies
        
        # Create figure
        fig = go.Figure(data=[edge_trace, node_trace],
                       layout=go.Layout(
                           title='Interactive Code Graph Visualization',
                           titlefont_size=16,
                           showlegend=False,
                           hovermode='closest',
                           margin=dict(b=20,l=5,r=5,t=40),
                           annotations=[ dict(
                               text="Python code relationships visualization",
                               showarrow=False,
                               xref="paper", yref="paper",
                               x=0.005, y=-0.002,
                               xanchor='left', yanchor='bottom',
                               font=dict(color="#888", size=12)
                           )],
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           width=width,
                           height=height))
        
        # Save HTML
        pyo.plot(fig, filename=output_path, auto_open=False)
    
    def _export_json(self, nodes: List[Dict], edges: List[Dict], output_path: str):
        """Export graph data as JSON."""
        data = {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "export_format": "json",
                "node_count": len(nodes),
                "edge_count": len(edges)
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _export_graphml(self, nodes: List[Dict], edges: List[Dict], output_path: str):
        """Export graph in GraphML format."""
        if not self.dependencies["networkx"]:
            raise ValueError("NetworkX is required for GraphML export. Install with: pip install 'codegraphcontext[visualization]'")
        
        import networkx as nx
        
        G = nx.Graph()
        
        # Add nodes with attributes
        for node in nodes:
            node_attrs = {
                "labels": ",".join(node["labels"]),
                **node["properties"]
            }
            G.add_node(node["id"], **node_attrs)
        
        # Add edges with attributes
        for edge in edges:
            edge_attrs = {
                "type": edge["type"],
                **edge["properties"]
            }
            G.add_edge(edge["source"], edge["target"], **edge_attrs)
        
        # Write GraphML
        nx.write_graphml(G, output_path)