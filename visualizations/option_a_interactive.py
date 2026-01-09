#!/usr/bin/env python3
"""
Option A: Enhanced Interactive Multi-Mode Visualizer
Generates interactive HTML visualizations with filtering by diagram type.
"""

import os
import json
import platform
from pathlib import Path
from typing import List, Dict, Any

if platform.system() == "Windows":
    raise RuntimeError(
        "CodeGraphContext uses redislite/FalkorDB, which does not support Windows.\n"
        "Please run the project using WSL or Docker."
    )

from redislite import FalkorDB


class InteractiveVisualizer:
    """Enhanced interactive visualizer with multiple diagram modes."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.path.expanduser('~/.codegraphcontext/falkordb.db')
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database not found at {self.db_path}")
        
        print(f"📊 Reading graph from {self.db_path}...")
        self.f = FalkorDB(self.db_path)
        self.g = self.f.select_graph('codegraph')
    
    def fetch_all_data(self) -> tuple:
        """Fetch all nodes and edges from the graph."""
        # Fetch nodes with all properties
        nodes_res = self.g.query("""
            MATCH (n) 
            RETURN id(n), labels(n)[0], n.name, n.file_path, n.path, 
                   n.line_number, n.decorators, n.args
        """)
        
        nodes = []
        for row in nodes_res.result_set:
            node_id, label, name, file_path, path, line_num, decorators, args = row
            display_name = name if name else (os.path.basename(path or file_path or "unknown"))
            
            # Build detailed tooltip
            tooltip_parts = [f"Type: {label}"]
            if file_path:
                tooltip_parts.append(f"File: {file_path}")
            if line_num:
                tooltip_parts.append(f"Line: {line_num}")
            if decorators:
                tooltip_parts.append(f"Decorators: {', '.join(decorators)}")
            if args:
                tooltip_parts.append(f"Args: {', '.join(args)}")
            
            nodes.append({
                "id": node_id,
                "label": display_name,
                "group": label,
                "title": "\\n".join(tooltip_parts),
                "file_path": file_path or path or "",
                "line_number": line_num or 0
            })
        
        # Fetch relationships with properties
        edges_res = self.g.query("""
            MATCH (s)-[r]->(t) 
            RETURN id(s), type(r), id(t), r.line_number, r.args, r.full_call_name
        """)
        
        edges = []
        for row in edges_res.result_set:
            source, rel_type, target, line_num, args, full_call = row
            
            # Build edge label
            edge_label = rel_type
            if args:
                edge_label += f"({', '.join(args[:3])}{'...' if len(args) > 3 else ''})"
            
            edges.append({
                "from": source,
                "to": target,
                "label": edge_label,
                "type": rel_type,
                "arrows": "to",
                "line_number": line_num or 0,
                "title": f"{rel_type} @ line {line_num}" if line_num else rel_type
            })
        
        return nodes, edges
    
    def generate_html(self, output_path: str = "interactive_viz.html"):
        """Generate enhanced interactive HTML visualization."""
        nodes, edges = self.fetch_all_data()
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>CodeGraphContext - Interactive Multi-Mode Visualizer</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style type="text/css">
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #ffffff;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            overflow: hidden;
        }}
        
        #mynetwork {{
            width: 100vw;
            height: 100vh;
        }}
        
        .control-panel {{
            position: absolute;
            top: 20px;
            left: 20px;
            z-index: 10;
            background: rgba(0, 0, 0, 0.85);
            padding: 20px;
            border-radius: 12px;
            border: 2px solid #00d4ff;
            box-shadow: 0 8px 32px rgba(0, 212, 255, 0.3);
            max-width: 350px;
        }}
        
        h1 {{
            margin: 0 0 15px 0;
            font-size: 1.4em;
            color: #00d4ff;
            text-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
        }}
        
        .stats {{
            font-size: 0.85em;
            color: #aaa;
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 1px solid #333;
        }}
        
        .filter-section {{
            margin-bottom: 15px;
        }}
        
        .filter-title {{
            font-size: 0.9em;
            color: #00d4ff;
            margin-bottom: 8px;
            font-weight: bold;
        }}
        
        .filter-buttons {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }}
        
        .filter-btn {{
            padding: 6px 12px;
            border: 1px solid #555;
            background: rgba(255, 255, 255, 0.1);
            color: #fff;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.8em;
            transition: all 0.3s ease;
        }}
        
        .filter-btn:hover {{
            background: rgba(0, 212, 255, 0.2);
            border-color: #00d4ff;
            transform: translateY(-2px);
        }}
        
        .filter-btn.active {{
            background: #00d4ff;
            color: #000;
            border-color: #00d4ff;
            font-weight: bold;
        }}
        
        .layout-section {{
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #333;
        }}
        
        select {{
            width: 100%;
            padding: 8px;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid #555;
            color: #fff;
            border-radius: 6px;
            font-size: 0.85em;
            cursor: pointer;
        }}
        
        select:focus {{
            outline: none;
            border-color: #00d4ff;
        }}
        
        .help-text {{
            font-size: 0.75em;
            color: #888;
            margin-top: 10px;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="control-panel">
        <h1>🎨 Interactive Visualizer</h1>
        <div class="stats">
            <div>Nodes: <strong>{len(nodes)}</strong></div>
            <div>Relationships: <strong>{len(edges)}</strong></div>
        </div>
        
        <div class="filter-section">
            <div class="filter-title">📊 Diagram Mode</div>
            <div class="filter-buttons">
                <button class="filter-btn active" onclick="setMode('all')">All</button>
                <button class="filter-btn" onclick="setMode('calls')">Call Graph</button>
                <button class="filter-btn" onclick="setMode('imports')">Imports</button>
                <button class="filter-btn" onclick="setMode('inherits')">Inheritance</button>
                <button class="filter-btn" onclick="setMode('contains')">Structure</button>
            </div>
        </div>
        
        <div class="filter-section">
            <div class="filter-title">🔍 Node Types</div>
            <div class="filter-buttons">
                <button class="filter-btn active" onclick="toggleNodeType('Function')">Functions</button>
                <button class="filter-btn active" onclick="toggleNodeType('Class')">Classes</button>
                <button class="filter-btn active" onclick="toggleNodeType('Module')">Modules</button>
                <button class="filter-btn active" onclick="toggleNodeType('File')">Files</button>
            </div>
        </div>
        
        <div class="filter-section">
            <div class="filter-title">⚙️ Options</div>
            <div class="filter-buttons">
                <button class="filter-btn active" id="hideUnconnectedBtn" onclick="toggleHideUnconnected()">Hide Unconnected</button>
            </div>
        </div>
        
        <div class="layout-section">
            <div class="filter-title">🎯 Layout</div>
            <select onchange="changeLayout(this.value)">
                <option value="forceAtlas2Based">Force Atlas (Default)</option>
                <option value="hierarchical">Hierarchical</option>
                <option value="barnesHut">Barnes Hut</option>
                <option value="repulsion">Repulsion</option>
            </select>
        </div>
        
        <div class="help-text">
            💡 Drag to move • Scroll to zoom • Click nodes for details
        </div>
    </div>
    
    <div id="mynetwork"></div>

    <script type="text/javascript">
        // Data
        const allNodes = new vis.DataSet({json.dumps(nodes)});
        const allEdges = new vis.DataSet({json.dumps(edges)});
        
        let activeNodeTypes = new Set(['Function', 'Class', 'Module', 'File', 'Repository', 'Variable']);
        let activeMode = 'all';
        let hideUnconnected = true;
        
        // Network instance
        let network;
        
        // Color scheme
        const groupColors = {{
            Repository: {{ background: '#e91e63', border: '#c2185b' }},
            File: {{ background: '#2196f3', border: '#1976d2' }},
            Function: {{ background: '#4caf50', border: '#388e3c' }},
            Class: {{ background: '#ff9800', border: '#f57c00' }},
            Module: {{ background: '#9c27b0', border: '#7b1fa2' }},
            Variable: {{ background: '#607d8b', border: '#455a64' }}
        }};
        
        // Initialize network
        function initNetwork() {{
            const container = document.getElementById('mynetwork');
            
            const options = {{
                nodes: {{
                    shape: 'dot',
                    size: 16,
                    font: {{ color: '#ffffff', size: 12 }},
                    borderWidth: 2,
                    shadow: true
                }},
                edges: {{
                    width: 2,
                    color: {{ color: '#666666', highlight: '#00d4ff' }},
                    font: {{ size: 10, align: 'middle', color: '#aaaaaa' }},
                    smooth: {{ type: 'continuous' }}
                }},
                groups: groupColors,
                physics: {{
                    forceAtlas2Based: {{
                        gravitationalConstant: -26,
                        centralGravity: 0.005,
                        springLength: 230,
                        springConstant: 0.18
                    }},
                    maxVelocity: 146,
                    solver: 'forceAtlas2Based',
                    timestep: 0.35,
                    stabilization: {{ iterations: 150 }}
                }},
                interaction: {{
                    hover: true,
                    tooltipDelay: 100
                }}
            }};
            
            network = new vis.Network(container, {{ nodes: allNodes, edges: allEdges }}, options);
            
            // Event handlers
            network.on('click', function(params) {{
                if (params.nodes.length > 0) {{
                    const nodeId = params.nodes[0];
                    const node = allNodes.get(nodeId);
                    console.log('Clicked node:', node);
                }}
            }});
            
            updateView();
        }}
        
        // Filter functions
        function setMode(mode) {{
            activeMode = mode;
            
            // Update button states
            document.querySelectorAll('.filter-section:first-of-type .filter-btn').forEach(btn => {{
                btn.classList.remove('active');
            }});
            event.target.classList.add('active');
            
            updateView();
        }}
        
        function toggleNodeType(type) {{
            if (activeNodeTypes.has(type)) {{
                activeNodeTypes.delete(type);
                event.target.classList.remove('active');
            }} else {{
                activeNodeTypes.add(type);
                event.target.classList.add('active');
            }}
            updateView();
        }}
        
        function toggleHideUnconnected() {{
            hideUnconnected = !hideUnconnected;
            const btn = document.getElementById('hideUnconnectedBtn');
            if (hideUnconnected) {{
                btn.classList.add('active');
            }} else {{
                btn.classList.remove('active');
            }}
            updateView();
        }}
        
        function changeLayout(solver) {{
            network.setOptions({{
                physics: {{
                    enabled: true,
                    solver: solver,
                    stabilization: {{ iterations: 150 }}
                }}
            }});
        }}
        
        function updateView() {{
            // First, filter edges based on mode
            const visibleEdges = [];
            const connectedNodeIds = new Set();
            
            allEdges.forEach(edge => {{
                let includeEdge = false;
                
                if (activeMode === 'all') {{
                    includeEdge = true;
                }} else if (activeMode === 'calls' && edge.type === 'CALLS') {{
                    includeEdge = true;
                }} else if (activeMode === 'imports' && edge.type === 'IMPORTS') {{
                    includeEdge = true;
                }} else if (activeMode === 'inherits' && edge.type === 'INHERITS') {{
                    includeEdge = true;
                }} else if (activeMode === 'contains' && edge.type === 'CONTAINS') {{
                    includeEdge = true;
                }}
                
                if (includeEdge) {{
                    visibleEdges.push(edge.id);
                    connectedNodeIds.add(edge.from);
                    connectedNodeIds.add(edge.to);
                }}
            }});
            
            // Then filter nodes based on type and connection status
            const visibleNodeIds = new Set();
            allNodes.forEach(node => {{
                // Check if node type is active
                if (!activeNodeTypes.has(node.group)) return;
                
                // If hideUnconnected is true and mode is not 'all', only show connected nodes
                if (hideUnconnected && activeMode !== 'all') {{
                    if (connectedNodeIds.has(node.id)) {{
                        visibleNodeIds.add(node.id);
                    }}
                }} else {{
                    visibleNodeIds.add(node.id);
                }}
            }});
            
            // Filter edges again to only include those with both nodes visible
            const finalVisibleEdges = [];
            visibleEdges.forEach(edgeId => {{
                const edge = allEdges.get(edgeId);
                if (visibleNodeIds.has(edge.from) && visibleNodeIds.has(edge.to)) {{
                    finalVisibleEdges.push(edgeId);
                }}
            }});
            
            // Update network view
            const visibleNodesArray = Array.from(visibleNodeIds);
            network.setData({{
                nodes: new vis.DataSet(allNodes.get(visibleNodesArray)),
                edges: new vis.DataSet(allEdges.get(finalVisibleEdges))
            }});
        }}
        
        // Initialize on load
        initNetwork();
    </script>
</body>
</html>
        """
        
        target_path = Path.cwd() / output_path
        with open(target_path, "w") as f:
            f.write(html_content)
        
        print(f"\n✅ Interactive visualization generated!")
        print(f"👉 Open: file://{target_path.absolute()}")
        return target_path


def main():
    """Generate Option A: Interactive Multi-Mode Visualizer."""
    visualizer = InteractiveVisualizer()
    visualizer.generate_html("option_a_interactive.html")


if __name__ == "__main__":
    main()
