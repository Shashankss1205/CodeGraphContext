# src/codegraphcontext/viz/server.py
"""FastAPI server for live graph visualization."""

import asyncio
import webbrowser
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from ..core.database import DatabaseManager


class VizServer:
    """Live visualization server for CodeGraphContext."""
    
    def __init__(self, db_manager: DatabaseManager, initial_query: Optional[str] = None):
        self.db_manager = db_manager
        self.initial_query = initial_query or "MATCH (n) RETURN n LIMIT 50"
        self.app = FastAPI(title="CodeGraphContext Visualizer")
        self.active_connections = []
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup FastAPI routes."""
        static_dir = Path(__file__).parent / "static"
        
        # Serve static files
        self.app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        
        @self.app.get("/")
        async def root():
            """Serve the main visualization page."""
            html_file = static_dir / "index.html"
            with open(html_file) as f:
                html_content = f.read()
            # Inject initial query
            html_content = html_content.replace(
                "{{INITIAL_QUERY}}", 
                self.initial_query
            )
            return HTMLResponse(content=html_content)
        
        @self.app.get("/api/query")
        async def execute_query(cypher: str):
            """Execute a Cypher query and return results."""
            try:
                # Safety: Enforce strict LIMIT if missing to prevent browser crashes
                if "LIMIT" not in cypher.upper():
                    cypher += " LIMIT 1000"
                
                with self.db_manager.get_driver().session() as session:
                    result = session.run(cypher)
                    
                    # Convert to graph format
                    nodes = []
                    edges = []
                    node_ids = set()
                    edge_ids = set()
                    
                    for record in result:
                        for key, value in record.items():
                            # Helper to process a single entity
                            def process_entity(entity):
                                # Handle nodes
                                if hasattr(entity, 'labels'):
                                    node_id = entity.id
                                    if node_id not in node_ids:
                                        node_ids.add(node_id)
                                        props = getattr(entity, 'properties', {})
                                        if props is None: props = {}
                                        if isinstance(entity, dict):
                                            props = entity
                                            
                                        nodes.append({
                                            "id": str(node_id),
                                            "label": props.get("name", str(node_id)),
                                            "type": list(entity.labels)[0] if entity.labels else "Node",
                                            "properties": props
                                        })
                                
                                # Handle FalkorDB Edge objects (from Paths)
                                elif hasattr(entity, 'relation') and hasattr(entity, 'src_node'):
                                    if entity.id not in edge_ids:
                                        edge_ids.add(entity.id)
                                        props = getattr(entity, 'properties', {})
                                        if props is None: props = {}
                                        
                                        edges.append({
                                            "id": "e-" + str(entity.id),
                                            "source": str(entity.src_node),
                                            "target": str(entity.dest_node),
                                            "type": entity.relation,
                                            "properties": props
                                        })

                                # Handle relationships
                                elif hasattr(entity, 'type'):
                                    if entity.id not in edge_ids:
                                        edge_ids.add(entity.id)
                                        props = getattr(entity, 'properties', {})
                                        if props is None: props = {}
                                        if isinstance(entity, dict):
                                                props = entity
        
                                        edges.append({
                                            "id": "e-" + str(entity.id),
                                            "source": str(entity.start_node.id),
                                            "target": str(entity.end_node.id),
                                            "type": entity.type,
                                            "properties": props
                                        })
                                # Handle Paths - Try multiple approaches for different drivers
                                # FalkorDB uses 'edges', Neo4j uses 'relationships'
                                elif hasattr(entity, 'nodes') and (hasattr(entity, 'relationships') or hasattr(entity, 'edges')):
                                    print(f"Viz Server: Found Path ({type(entity).__name__})")
                                    
                                    # Get nodes
                                    ns = entity.nodes
                                    if callable(ns): ns = ns()
                                    
                                    # Get edges/relationships
                                    if hasattr(entity, 'edges'):
                                        rs = entity.edges
                                    else:
                                        rs = entity.relationships
                                    if callable(rs): rs = rs()
                                    
                                    for n in ns: process_entity(n)
                                    for r in rs: process_entity(r)
                                
                                # FalkorDB may also use _nodes and _edges (backup)
                                elif hasattr(entity, '_nodes') and hasattr(entity, '_edges'):
                                    print(f"Viz Server: Found FalkorDB Path via _nodes/_edges")
                                    for n in entity._nodes: process_entity(n)
                                    for r in entity._edges: process_entity(r)
                                
                                # Handle Lists/Tuples (Flatten)
                                elif isinstance(entity, (list, tuple)):
                                    for item in entity: process_entity(item)
                                
                                # String representation of Path (FalkorDB fallback)
                                elif isinstance(entity, str) and entity.startswith('<') and '->' in entity:
                                    # Parse string like "<(48)-[260]->(41)>"
                                    # This is a last resort - we can't get full node/edge data from strings
                                    print(f"Viz Server: WARNING - Path returned as string: {entity}")
                                    print("Viz Server: Cannot visualize string-format paths. Use explicit node/relationship returns.")
                                    
                                # Fallback: unexpected object
                                else:
                                    # Only log truly unknown types (not scalars)
                                    if not isinstance(entity, (int, float, str, bool, type(None))):
                                        print(f"Viz Server: Unknown entity type: {type(entity).__name__}")
                                        # Try to inspect it
                                        if hasattr(entity, '__dict__'):
                                            print(f"Viz Server: Entity attributes: {list(entity.__dict__.keys())}")

                            process_entity(value)

                    # AUTO-CONNECT: Fetch implicit relationships between returned nodes
                    # This runs a secondary query to find edges between the nodes
                    # Disabled for very large result sets to prevent performance issues
                    MAX_NODES_FOR_AUTO_CONNECT = 1000
                    
                    if len(node_ids) > 1:
                        if len(node_ids) > MAX_NODES_FOR_AUTO_CONNECT:
                             print(f"Viz Server: Skipping auto-connect (Too many nodes: {len(node_ids)} > {MAX_NODES_FOR_AUTO_CONNECT})")
                        else:
                            ids_str = ", ".join(str(nid) for nid in node_ids)
                            
                            if ids_str:
                                # Use ID() explicitly and return start/end IDs to be safe
                                edge_query = f"""
                                MATCH (a)-[r]->(b)
                                WHERE ID(a) IN [{ids_str}] AND ID(b) IN [{ids_str}]
                                RETURN r, ID(a) as src, ID(b) as tgt
                                """
                                try:
                                    edge_result = session.run(edge_query)
                                    
                                    for record in edge_result:
                                        if 'r' in record.keys():
                                            rel = record['r']
                                            src_id = record['src']
                                            tgt_id = record['tgt']
                                            
                                            if hasattr(rel, 'id'):
                                                if rel.id in edge_ids: continue
                                                edge_ids.add(rel.id)
                                                
                                                props = getattr(rel, 'properties', {})
                                                if props is None: props = {}
                                                if isinstance(rel, dict): props = rel
                                                
                                                rel_type = "RELATED"
                                                if hasattr(rel, 'type'): rel_type = rel.type
                                                elif hasattr(rel, 'relation'): rel_type = rel.relation
                                                elif hasattr(rel, 'label'): rel_type = rel.label
                                                
                                                edges.append({
                                                    "id": "e-" + str(rel.id),
                                                    "source": str(src_id),
                                                    "target": str(tgt_id),
                                                    "type": rel_type,
                                                    "properties": props
                                                })
                                except Exception as e:
                                    print(f"Auto-connect error: {e}")

                    print(f"Viz Server: Returning {len(nodes)} nodes and {len(edges)} edges")

                    return {
                        "success": True,
                        "nodes": nodes,
                        "edges": edges,
                        "count": len(nodes)
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        
        @self.app.get("/api/stats")
        async def get_stats():
            """Get database statistics."""
            try:
                with self.db_manager.get_driver().session() as session:
                    result = session.run("MATCH (n) RETURN count(n) as total")
                    record = result.single()
                    total_nodes = record["total"] if record else 0
                    
                    return {
                        "success": True,
                        "total_nodes": total_nodes
                    }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.get("/api/schema")
        async def get_schema():
            """Get database schema information."""
            try:
                with self.db_manager.get_driver().session() as session:
                    # Get node labels
                    labels_result = session.run("CALL db.labels()")
                    labels = [record[0] for record in labels_result]
                    
                    # Get relationship types
                    rels_result = session.run("CALL db.relationshipTypes()")
                    relationships = [record[0] for record in rels_result]
                    
                    return {
                        "success": True,
                        "labels": labels,
                        "relationships": relationships
                    }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket for live updates."""
            await websocket.accept()
            self.active_connections.append(websocket)
            try:
                while True:
                    # Keep connection alive
                    data = await websocket.receive_text()
                    # Echo back for now (can add live update logic later)
                    await websocket.send_text(f"Received: {data}")
            except WebSocketDisconnect:
                self.active_connections.remove(websocket)


def start_viz_server(db_manager: DatabaseManager, query: Optional[str] = None, port: int = 8080):
    """
    Start the visualization server.
    
    Args:
        db_manager: Database manager instance
        query: Initial Cypher query to display
        port: Port to run server on (default: 8080)
    """
    server = VizServer(db_manager, query)
    
    # Open browser after a short delay
    def open_browser():
        import time
        time.sleep(1.5)
        webbrowser.open(f"http://localhost:{port}")
    
    import threading
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Start server
    print(f"🚀 Starting CodeGraphContext Visualizer at http://localhost:{port}")
    print("Press Ctrl+C to stop")
    
    uvicorn.run(server.app, host="0.0.0.0", port=port, log_level="error")
