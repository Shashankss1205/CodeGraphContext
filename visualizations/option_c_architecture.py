#!/usr/bin/env python3
"""
Option C: Architectural Analyzer
Generates high-level architectural diagrams by grouping code into logical layers/modules.
"""

import os
import platform
from pathlib import Path
from typing import List, Dict, Set, Tuple
from collections import defaultdict

if platform.system() == "Windows":
    raise RuntimeError(
        "CodeGraphContext uses redislite/FalkorDB, which does not support Windows.\n"
        "Please run the project using WSL or Docker."
    )

from redislite import FalkorDB


class ArchitecturalAnalyzer:
    """Analyze and visualize high-level software architecture."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.path.expanduser('~/.codegraphcontext/falkordb.db')
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database not found at {self.db_path}")
        
        print(f"📊 Reading graph from {self.db_path}...")
        self.f = FalkorDB(self.db_path)
        self.g = self.f.select_graph('codegraph')
    
    def analyze_module_structure(self) -> Dict[str, Dict]:
        """Analyze the module/package structure of the codebase."""
        print("🔍 Analyzing module structure...")
        
        # Get all files and their paths
        files_res = self.g.query("""
            MATCH (f:File)
            RETURN f.path, f.name
        """)
        
        # Group files by directory
        modules = defaultdict(lambda: {"files": [], "functions": 0, "classes": 0})
        
        for row in files_res.result_set:
            file_path, file_name = row
            if not file_path:
                continue
            
            # Extract module/package name (directory)
            path_obj = Path(file_path)
            if len(path_obj.parts) > 1:
                module_name = path_obj.parts[-2]  # Parent directory
            else:
                module_name = "root"
            
            modules[module_name]["files"].append(file_name)
        
        # Count functions and classes per module
        for module_name in modules.keys():
            # Count functions
            func_res = self.g.query(f"""
                MATCH (f:Function)
                WHERE f.file_path CONTAINS '{module_name}'
                RETURN count(f)
            """)
            if func_res.result_set:
                modules[module_name]["functions"] = func_res.result_set[0][0]
            
            # Count classes
            class_res = self.g.query(f"""
                MATCH (c:Class)
                WHERE c.file_path CONTAINS '{module_name}'
                RETURN count(c)
            """)
            if class_res.result_set:
                modules[module_name]["classes"] = class_res.result_set[0][0]
        
        return dict(modules)
    
    def analyze_dependencies(self) -> List[Tuple[str, str, int]]:
        """Analyze inter-module dependencies."""
        print("🔍 Analyzing module dependencies...")
        
        # Get all import relationships
        imports_res = self.g.query("""
            MATCH (f:File)-[:IMPORTS]->(m:Module)
            RETURN f.path, m.name
        """)
        
        # Group by modules
        dependencies = defaultdict(lambda: defaultdict(int))
        
        for row in imports_res.result_set:
            file_path, module_name = row
            if not file_path or not module_name:
                continue
            
            # Extract source module
            path_obj = Path(file_path)
            if len(path_obj.parts) > 1:
                source_module = path_obj.parts[-2]
            else:
                source_module = "root"
            
            # Determine target module (simplified)
            if "/" in module_name or "." in module_name:
                target_module = module_name.split("/")[0].split(".")[0]
            else:
                target_module = module_name
            
            dependencies[source_module][target_module] += 1
        
        # Convert to list of tuples
        dep_list = []
        for source, targets in dependencies.items():
            for target, count in targets.items():
                if source != target:  # Exclude self-dependencies
                    dep_list.append((source, target, count))
        
        return dep_list
    
    def generate_architectural_diagram(self, output_path: str = "architecture.html"):
        """Generate interactive architectural diagram."""
        print("🎨 Generating architectural diagram...")
        
        modules = self.analyze_module_structure()
        dependencies = self.analyze_dependencies()
        
        # Build nodes (modules)
        nodes = []
        for idx, (module_name, info) in enumerate(modules.items()):
            size = 20 + (info["functions"] + info["classes"]) * 2
            nodes.append({
                "id": idx,
                "label": module_name,
                "title": f"Module: {module_name}\\nFiles: {len(info['files'])}\\nFunctions: {info['functions']}\\nClasses: {info['classes']}",
                "value": size,
                "group": "module"
            })
        
        # Create module name to ID mapping
        module_to_id = {name: idx for idx, name in enumerate(modules.keys())}
        
        # Build edges (dependencies)
        edges = []
        for source, target, count in dependencies:
            if source in module_to_id and target in module_to_id:
                edges.append({
                    "from": module_to_id[source],
                    "to": module_to_id[target],
                    "value": count,
                    "title": f"{source} → {target}\\nImports: {count}",
                    "arrows": "to"
                })
        
        # Generate HTML
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Architectural Diagram - CodeGraphContext</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
            color: #ffffff;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            overflow: hidden;
        }}
        
        #network {{
            width: 100vw;
            height: 100vh;
        }}
        
        .info-panel {{
            position: absolute;
            top: 20px;
            left: 20px;
            z-index: 10;
            background: rgba(0, 0, 0, 0.9);
            padding: 25px;
            border-radius: 15px;
            border: 2px solid #4ecdc4;
            box-shadow: 0 10px 40px rgba(78, 205, 196, 0.4);
            max-width: 400px;
        }}
        
        h1 {{
            margin: 0 0 10px 0;
            font-size: 1.6em;
            color: #4ecdc4;
            text-shadow: 0 0 15px rgba(78, 205, 196, 0.6);
        }}
        
        .subtitle {{
            font-size: 0.9em;
            color: #95e1d3;
            margin-bottom: 20px;
        }}
        
        .stats {{
            background: rgba(78, 205, 196, 0.1);
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #4ecdc4;
        }}
        
        .stat-row {{
            display: flex;
            justify-content: space-between;
            margin: 8px 0;
            font-size: 0.9em;
        }}
        
        .stat-label {{
            color: #95e1d3;
        }}
        
        .stat-value {{
            color: #fff;
            font-weight: bold;
        }}
        
        .legend {{
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #444;
        }}
        
        .legend-title {{
            font-size: 0.85em;
            color: #4ecdc4;
            margin-bottom: 10px;
            font-weight: bold;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            margin: 8px 0;
            font-size: 0.8em;
        }}
        
        .legend-circle {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 10px;
            background: #4ecdc4;
        }}
        
        .help-text {{
            font-size: 0.75em;
            color: #888;
            margin-top: 15px;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="info-panel">
        <h1>🏗️ Architecture View</h1>
        <div class="subtitle">High-Level Module Dependencies</div>
        
        <div class="stats">
            <div class="stat-row">
                <span class="stat-label">📦 Modules:</span>
                <span class="stat-value">{len(modules)}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">🔗 Dependencies:</span>
                <span class="stat-value">{len(dependencies)}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">📄 Total Files:</span>
                <span class="stat-value">{sum(len(m['files']) for m in modules.values())}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">⚡ Functions:</span>
                <span class="stat-value">{sum(m['functions'] for m in modules.values())}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">🎯 Classes:</span>
                <span class="stat-value">{sum(m['classes'] for m in modules.values())}</span>
            </div>
        </div>
        
        <div class="legend">
            <div class="legend-title">💡 Understanding the View</div>
            <div class="legend-item">
                <div class="legend-circle"></div>
                <span>Node size = complexity (functions + classes)</span>
            </div>
            <div class="legend-item">
                <div class="legend-circle"></div>
                <span>Edge thickness = number of imports</span>
            </div>
        </div>
        
        <div class="help-text">
            💡 Drag to move • Scroll to zoom • Click for details
        </div>
    </div>
    
    <div id="network"></div>

    <script type="text/javascript">
        const nodes = new vis.DataSet({nodes});
        const edges = new vis.DataSet({edges});
        
        const container = document.getElementById('network');
        const data = {{
            nodes: nodes,
            edges: edges
        }};
        
        const options = {{
            nodes: {{
                shape: 'box',
                margin: 10,
                widthConstraint: {{
                    minimum: 100,
                    maximum: 200
                }},
                font: {{
                    color: '#ffffff',
                    size: 14,
                    face: 'Segoe UI'
                }},
                color: {{
                    background: '#4ecdc4',
                    border: '#2c9a8f',
                    highlight: {{
                        background: '#95e1d3',
                        border: '#4ecdc4'
                    }}
                }},
                borderWidth: 3,
                shadow: {{
                    enabled: true,
                    color: 'rgba(78, 205, 196, 0.5)',
                    size: 10
                }}
            }},
            edges: {{
                color: {{
                    color: 'rgba(149, 225, 211, 0.6)',
                    highlight: '#4ecdc4'
                }},
                width: 2,
                arrows: {{
                    to: {{
                        enabled: true,
                        scaleFactor: 0.5
                    }}
                }},
                smooth: {{
                    type: 'cubicBezier',
                    forceDirection: 'horizontal',
                    roundness: 0.4
                }},
                scaling: {{
                    min: 1,
                    max: 5
                }}
            }},
            layout: {{
                // Use force-directed layout instead of hierarchical for better edge visibility
                randomSeed: 42  // Consistent layout
            }},
            physics: {{
                enabled: true,
                forceAtlas2Based: {{
                    gravitationalConstant: -50,
                    centralGravity: 0.01,
                    springLength: 200,
                    springConstant: 0.08,
                    avoidOverlap: 1
                }},
                maxVelocity: 50,
                solver: 'forceAtlas2Based',
                timestep: 0.35,
                stabilization: {{
                    enabled: true,
                    iterations: 200,
                    updateInterval: 25
                }}
            }},
            interaction: {{
                hover: true,
                tooltipDelay: 100,
                navigationButtons: true,
                keyboard: true
            }}
        }};
        
        const network = new vis.Network(container, data, options);
        
        // Debug: Log edges to console
        console.log('Modules (nodes):', nodes.get());
        console.log('Dependencies (edges):', edges.get());
        console.log('Total edges:', edges.length);
        
        // Event handlers
        network.on('click', function(params) {{
            if (params.nodes.length > 0) {{
                const nodeId = params.nodes[0];
                const node = nodes.get(nodeId);
                console.log('Selected module:', node);
                
                // Highlight connected edges
                const connectedEdges = network.getConnectedEdges(nodeId);
                console.log('Connected edges:', connectedEdges);
            }}
        }});
        
        network.on('stabilizationIterationsDone', function() {{
            console.log('Network stabilized');
            // Keep physics enabled for dragging
            network.setOptions({{ physics: {{ enabled: true, stabilization: false }} }});
        }});
    </script>
</body>
</html>
        """
        
        target_path = Path.cwd() / output_path
        with open(target_path, "w") as f:
            f.write(html_content)
        
        print(f"✅ Architectural diagram: {target_path}")
        print(f"👉 Open: file://{target_path.absolute()}")
        return target_path
    
    def export_architecture_report(self, output_path: str = "architecture_report.md"):
        """Generate a detailed architecture report in Markdown."""
        print("📝 Generating architecture report...")
        
        modules = self.analyze_module_structure()
        dependencies = self.analyze_dependencies()
        
        # Build report
        lines = [
            "# 🏗️ Software Architecture Report",
            "",
            f"**Generated by CodeGraphContext**",
            "",
            "## 📊 Overview",
            "",
            f"- **Total Modules**: {len(modules)}",
            f"- **Total Files**: {sum(len(m['files']) for m in modules.values())}",
            f"- **Total Functions**: {sum(m['functions'] for m in modules.values())}",
            f"- **Total Classes**: {sum(m['classes'] for m in modules.values())}",
            f"- **Inter-Module Dependencies**: {len(dependencies)}",
            "",
            "## 📦 Module Breakdown",
            ""
        ]
        
        # Sort modules by complexity
        sorted_modules = sorted(
            modules.items(),
            key=lambda x: x[1]['functions'] + x[1]['classes'],
            reverse=True
        )
        
        for module_name, info in sorted_modules:
            lines.append(f"### {module_name}")
            lines.append("")
            lines.append(f"- **Files**: {len(info['files'])}")
            lines.append(f"- **Functions**: {info['functions']}")
            lines.append(f"- **Classes**: {info['classes']}")
            lines.append(f"- **Complexity Score**: {info['functions'] + info['classes']}")
            lines.append("")
        
        # Dependency analysis
        lines.append("## 🔗 Module Dependencies")
        lines.append("")
        lines.append("| Source Module | Target Module | Import Count |")
        lines.append("|---------------|---------------|--------------|")
        
        for source, target, count in sorted(dependencies, key=lambda x: x[2], reverse=True):
            lines.append(f"| {source} | {target} | {count} |")
        
        lines.append("")
        lines.append("## 🎯 Architecture Insights")
        lines.append("")
        
        # Find most connected modules
        module_connections = defaultdict(int)
        for source, target, count in dependencies:
            module_connections[source] += count
            module_connections[target] += count
        
        if module_connections:
            most_connected = max(module_connections.items(), key=lambda x: x[1])
            lines.append(f"- **Most Connected Module**: `{most_connected[0]}` ({most_connected[1]} connections)")
        
        # Find largest module
        if sorted_modules:
            largest = sorted_modules[0]
            lines.append(f"- **Largest Module**: `{largest[0]}` ({largest[1]['functions'] + largest[1]['classes']} components)")
        
        lines.append("")
        lines.append("---")
        lines.append("*Generated by CodeGraphContext - Option C: Architectural Analyzer*")
        
        # Write to file
        target_path = Path.cwd() / output_path
        with open(target_path, "w") as f:
            f.write("\n".join(lines))
        
        print(f"✅ Architecture report: {target_path}")
        return target_path
    
    def generate_all(self):
        """Generate all architectural outputs."""
        print("\n" + "="*60)
        print("🏗️  OPTION C: Architectural Analysis")
        print("="*60 + "\n")
        
        outputs = []
        
        # Interactive diagram
        outputs.append(self.generate_architectural_diagram("option_c_architecture.html"))
        print()
        
        # Markdown report
        outputs.append(self.export_architecture_report("option_c_report.md"))
        print()
        
        print("\n" + "="*60)
        print("✅ Architectural analysis complete!")
        print("="*60)
        print("\n📁 Generated files:")
        for path in outputs:
            print(f"   • {path.name}")
        
        return outputs


def main():
    """Generate Option C: Architectural Analysis."""
    analyzer = ArchitecturalAnalyzer()
    analyzer.generate_all()


if __name__ == "__main__":
    main()
