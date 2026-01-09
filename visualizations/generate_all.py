#!/usr/bin/env python3
"""
Master Visualization Script
Runs all three visualization options (A, B, C) and generates comprehensive output.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from option_a_interactive import InteractiveVisualizer
from option_b_export import DiagramExporter
from option_c_architecture import ArchitecturalAnalyzer


def print_banner():
    """Print a fancy banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        📊 CodeGraphContext Visualization Suite 📊           ║
║                                                              ║
║  Transform your code graph into beautiful, useful diagrams  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def main():
    """Run all visualization options."""
    print_banner()
    
    all_outputs = []
    
    try:
        # Option A: Interactive Visualizer
        print("\n" + "🎨 " + "="*58)
        print("OPTION A: Enhanced Interactive Multi-Mode Visualizer")
        print("="*60)
        visualizer = InteractiveVisualizer()
        output_a = visualizer.generate_html("option_a_interactive.html")
        all_outputs.append(output_a)
        
        # Option B: Static Diagram Exports
        print("\n" + "📦 " + "="*58)
        print("OPTION B: Static Diagram Generators")
        print("="*60)
        exporter = DiagramExporter()
        outputs_b = exporter.export_all()
        all_outputs.extend(outputs_b)
        
        # Option C: Architectural Analysis
        print("\n" + "🏗️  " + "="*58)
        print("OPTION C: Architectural Analyzer")
        print("="*60)
        analyzer = ArchitecturalAnalyzer()
        outputs_c = analyzer.generate_all()
        all_outputs.extend(outputs_c)
        
        # Summary
        print("\n" + "="*60)
        print("🎉 ALL VISUALIZATIONS GENERATED SUCCESSFULLY!")
        print("="*60)
        print(f"\n📁 Total files generated: {len(all_outputs)}")
        print("\n📂 Output files:")
        
        for path in all_outputs:
            print(f"   ✓ {path.name}")
        
        print("\n" + "="*60)
        print("📖 Next Steps:")
        print("="*60)
        print("\n🎨 OPTION A - Interactive Visualizer:")
        print(f"   Open: option_a_interactive.html")
        print("   Features: Dynamic filtering, multiple diagram modes, interactive exploration")
        
        print("\n📦 OPTION B - Static Diagrams:")
        print("   • PlantUML: option_b_plantuml_class.puml")
        print("     View at: https://www.plantuml.com/plantuml/uml/")
        print("   • Mermaid: option_b_mermaid_*.mmd")
        print("     View at: https://mermaid.live/")
        print("   • Graphviz: option_b_graphviz_*.dot")
        print("     Render: dot -Tpng file.dot -o output.png")
        
        print("\n🏗️  OPTION C - Architecture:")
        print("   • Interactive: option_c_architecture.html")
        print("   • Report: option_c_report.md")
        print("   Features: High-level module view, dependency analysis")
        
        print("\n" + "="*60)
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Make sure you have indexed your codebase first:")
        print("   cgc index /path/to/your/project")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
