#!/usr/bin/env python3
"""
Option B: Static Diagram Generators
Exports graph to PlantUML, Mermaid, and Graphviz DOT formats.
"""

import os
import platform
from pathlib import Path
from typing import List, Dict, Set
from collections import defaultdict

if platform.system() == "Windows":
    raise RuntimeError(
        "CodeGraphContext uses redislite/FalkorDB, which does not support Windows.\n"
        "Please run the project using WSL or Docker."
    )

from redislite import FalkorDB


class DiagramExporter:
    """Export code graph to various diagram formats."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.path.expanduser('~/.codegraphcontext/falkordb.db')
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database not found at {self.db_path}")
        
        print(f"📊 Reading graph from {self.db_path}...")
        self.f = FalkorDB(self.db_path)
        self.g = self.f.select_graph('codegraph')
    
    def export_plantuml_class_diagram(self, output_path: str = "class_diagram.puml"):
        """Export UML class diagram in PlantUML format."""
        print("🎨 Generating PlantUML class diagram...")
        
        # Fetch classes and their relationships
        classes_res = self.g.query("""
            MATCH (c:Class)
            OPTIONAL MATCH (c)-[:CONTAINS]->(m:Function)
            RETURN c.name, c.file_path, collect(m.name) as methods
        """)
        
        inheritance_res = self.g.query("""
            MATCH (child:Class)-[:INHERITS]->(parent:Class)
            RETURN child.name, parent.name
        """)
        
        # Build PlantUML content
        lines = ["@startuml", "!theme vibrant", "skinparam classAttributeIconSize 0", ""]
        
        # Add classes
        for row in classes_res.result_set:
            class_name, file_path, methods = row
            if not class_name:
                continue
            
            lines.append(f"class {class_name} {{")
            
            # Add methods
            if methods:
                for method in methods[:10]:  # Limit to 10 methods
                    if method:
                        lines.append(f"  +{method}()")
            
            if len(methods) > 10:
                lines.append(f"  ... ({len(methods) - 10} more methods)")
            
            lines.append("}")
            lines.append("")
        
        # Add inheritance relationships
        lines.append("' Inheritance relationships")
        for row in inheritance_res.result_set:
            child, parent = row
            if child and parent:
                lines.append(f"{parent} <|-- {child}")
        
        lines.append("")
        lines.append("@enduml")
        
        # Write to file
        target_path = Path.cwd() / output_path
        with open(target_path, "w") as f:
            f.write("\n".join(lines))
        
        print(f"✅ PlantUML class diagram: {target_path}")
        print(f"   View at: https://www.plantuml.com/plantuml/uml/")
        return target_path
    
    def export_mermaid_flowchart(self, function_name: str = None, output_path: str = "flowchart.mmd"):
        """Export call graph as Mermaid flowchart."""
        print(f"🎨 Generating Mermaid flowchart{' for ' + function_name if function_name else ''}...")
        
        if function_name:
            # Get call chain for specific function
            query = f"""
                MATCH path = (f:Function {{name: '{function_name}'}})-[:CALLS*1..3]->(called:Function)
                RETURN f.name, called.name
                UNION
                MATCH (caller:Function)-[:CALLS]->(f:Function {{name: '{function_name}'}})
                RETURN caller.name, f.name
            """
        else:
            # Get all function calls (limited)
            query = """
                MATCH (f:Function)-[:CALLS]->(called:Function)
                RETURN f.name, called.name
                LIMIT 50
            """
        
        calls_res = self.g.query(query)
        
        # Build Mermaid content
        lines = ["```mermaid", "graph TD"]
        
        # Track nodes to avoid duplicates
        nodes = set()
        edges = []
        
        for row in calls_res.result_set:
            caller, callee = row
            if caller and callee:
                # Sanitize names for Mermaid
                caller_id = caller.replace(".", "_").replace("-", "_")
                callee_id = callee.replace(".", "_").replace("-", "_")
                
                nodes.add((caller_id, caller))
                nodes.add((callee_id, callee))
                edges.append((caller_id, callee_id))
        
        # Add node definitions
        for node_id, node_label in sorted(nodes):
            lines.append(f"    {node_id}[{node_label}]")
        
        # Add edges
        for caller_id, callee_id in edges:
            lines.append(f"    {caller_id} --> {callee_id}")
        
        lines.append("```")
        
        # Write to file
        target_path = Path.cwd() / output_path
        with open(target_path, "w") as f:
            f.write("\n".join(lines))
        
        print(f"✅ Mermaid flowchart: {target_path}")
        print(f"   View at: https://mermaid.live/")
        return target_path
    
    def export_graphviz_dot(self, diagram_type: str = "calls", output_path: str = "graph.dot"):
        """Export to Graphviz DOT format."""
        print(f"🎨 Generating Graphviz DOT ({diagram_type})...")
        
        # Query based on diagram type
        if diagram_type == "calls":
            query = """
                MATCH (f:Function)-[r:CALLS]->(called:Function)
                RETURN f.name, called.name, f.file_path, called.file_path
                LIMIT 100
            """
            edge_label = "calls"
        elif diagram_type == "imports":
            query = """
                MATCH (f:File)-[r:IMPORTS]->(m:Module)
                RETURN f.name, m.name, f.path, ''
                LIMIT 100
            """
            edge_label = "imports"
        elif diagram_type == "inherits":
            query = """
                MATCH (child:Class)-[r:INHERITS]->(parent:Class)
                RETURN child.name, parent.name, child.file_path, parent.file_path
            """
            edge_label = "inherits"
        else:
            query = """
                MATCH (a)-[r]->(b)
                RETURN labels(a)[0] + ':' + coalesce(a.name, 'unknown'), 
                       labels(b)[0] + ':' + coalesce(b.name, 'unknown'),
                       type(r), ''
                LIMIT 100
            """
            edge_label = "relates"
        
        result = self.g.query(query)
        
        # Build DOT content with enhanced spacing
        lines = [
            "digraph CodeGraph {",
            "    // Layout settings for better spacing",
            "    rankdir=TB;",
            "    ranksep=1.5;        // Vertical spacing between ranks",
            "    nodesep=0.8;        // Horizontal spacing between nodes",
            "    splines=ortho;      // Orthogonal edges for cleaner look",
            "    ",
            "    // Node styling",
            "    node [",
            "        shape=box,",
            "        style=\"filled,rounded\",",
            "        fillcolor=lightblue,",
            "        fontname=\"Arial\",",
            "        fontsize=12,",
            "        margin=0.3,",
            "        height=0.6",
            "    ];",
            "    ",
            "    // Edge styling",
            "    edge [",
            "        color=gray,",
            "        arrowsize=0.8,",
            "        penwidth=1.5",
            "    ];",
            ""
        ]
        
        # Track nodes
        nodes = set()
        
        for row in result.result_set:
            source, target, source_path, target_path = row
            if source and target:
                # Sanitize names
                source_id = source.replace(".", "_").replace("-", "_").replace("/", "_")
                target_id = target.replace(".", "_").replace("-", "_").replace("/", "_")
                
                nodes.add((source_id, source))
                nodes.add((target_id, target))
                
                lines.append(f'    {source_id} -> {target_id} [label="{edge_label}"];')
        
        # Add node labels
        lines.append("")
        for node_id, node_label in sorted(nodes):
            # Escape quotes in labels
            safe_label = node_label.replace('"', '\\"')
            lines.append(f'    {node_id} [label="{safe_label}"];')
        
        lines.append("}")
        
        # Write to file
        target_path = Path.cwd() / output_path
        with open(target_path, "w") as f:
            f.write("\n".join(lines))
        
        print(f"✅ Graphviz DOT file: {target_path}")
        print(f"   Render with: dot -Tpng {output_path} -o graph.png")
        print(f"   Or view at: https://dreampuf.github.io/GraphvizOnline/")
        return target_path
    
    def export_mermaid_class_diagram(self, output_path: str = "class_diagram.mmd"):
        """Export UML class diagram in Mermaid format."""
        print("🎨 Generating Mermaid class diagram...")
        
        # Fetch classes
        classes_res = self.g.query("""
            MATCH (c:Class)
            OPTIONAL MATCH (c)-[:CONTAINS]->(m:Function)
            RETURN c.name, collect(m.name) as methods
        """)
        
        inheritance_res = self.g.query("""
            MATCH (child:Class)-[:INHERITS]->(parent:Class)
            RETURN child.name, parent.name
        """)
        
        # Build Mermaid content
        lines = ["```mermaid", "classDiagram"]
        
        # Add classes and methods
        for row in classes_res.result_set:
            class_name, methods = row
            if not class_name:
                continue
            
            lines.append(f"    class {class_name} {{")
            
            # Add methods
            if methods:
                for method in methods[:8]:  # Limit to 8 methods
                    if method:
                        lines.append(f"        +{method}()")
            
            lines.append("    }")
        
        # Add inheritance
        for row in inheritance_res.result_set:
            child, parent = row
            if child and parent:
                lines.append(f"    {parent} <|-- {child}")
        
        lines.append("```")
        
        # Write to file
        target_path = Path.cwd() / output_path
        with open(target_path, "w") as f:
            f.write("\n".join(lines))
        
        print(f"✅ Mermaid class diagram: {target_path}")
        print(f"   View at: https://mermaid.live/")
        return target_path
    
    def export_all(self):
        """Export all diagram formats."""
        print("\n" + "="*60)
        print("📦 OPTION B: Exporting to all diagram formats...")
        print("="*60 + "\n")
        
        outputs = []
        
        # PlantUML
        outputs.append(self.export_plantuml_class_diagram("option_b_plantuml_class.puml"))
        print()
        
        # Mermaid Class Diagram
        outputs.append(self.export_mermaid_class_diagram("option_b_mermaid_class.mmd"))
        print()
        
        # Mermaid Flowchart
        outputs.append(self.export_mermaid_flowchart(output_path="option_b_mermaid_calls.mmd"))
        print()
        
        # Graphviz DOT files
        outputs.append(self.export_graphviz_dot("calls", "option_b_graphviz_calls.dot"))
        print()
        outputs.append(self.export_graphviz_dot("imports", "option_b_graphviz_imports.dot"))
        print()
        outputs.append(self.export_graphviz_dot("inherits", "option_b_graphviz_inherits.dot"))
        print()
        
        print("\n" + "="*60)
        print("✅ All exports complete!")
        print("="*60)
        print("\n📁 Generated files:")
        for path in outputs:
            print(f"   • {path.name}")
        
        return outputs


def main():
    """Generate Option B: Static Diagram Exports."""
    exporter = DiagramExporter()
    exporter.export_all()


if __name__ == "__main__":
    main()
