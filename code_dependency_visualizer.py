"""
Author: Dhruv Patni
Repository: CodeGraphContext
File: code_dependency_visualizer.py

Description:
-------------
This script scans through all Python files in a given project directory,
extracts module import relationships, and builds a directed dependency graph.

Libraries used:
- os: for directory traversal
- re: for parsing import statements
- networkx: for building and visualizing the dependency graph

Usage:
$ python code_dependency_visualizer.py /path/to/project
"""

import os
import re
import sys
import networkx as nx
import matplotlib.pyplot as plt

def extract_imports(file_path):
    """Extracts imported modules from a Python file."""
    imports = set()
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            match = re.match(r'^(?:from|import)\s+([a-zA-Z0-9_\.]+)', line)
            if match:
                imports.add(match.group(1).split('.')[0])
    return imports


def build_dependency_graph(root_dir):
    """Scans directory and builds dependency graph."""
    graph = nx.DiGraph()

    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                module_name = os.path.splitext(file)[0]
                imports = extract_imports(full_path)

                for imp in imports:
                    graph.add_edge(module_name, imp)

    return graph


def visualize_graph(graph):
    """Visualizes the dependency graph using matplotlib."""
    plt.figure(figsize=(10, 7))
    nx.draw_networkx(graph, with_labels=True, node_color="skyblue", font_size=10, edge_color="gray")
    plt.title("📦 Python Project Dependency Graph", fontsize=14)
    plt.show()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python code_dependency_visualizer.py <project_directory>")
        sys.exit(1)

    directory = sys.argv[1]
    if not os.path.exists(directory):
        print("❌ Directory not found.")
        sys.exit(1)

    print(f"🔍 Scanning Python files in: {directory}")
    dep_graph = build_dependency_graph(directory)

    print(f"✅ Found {len(dep_graph.nodes())} modules and {len(dep_graph.edges())} dependencies.")
    visualize_graph(dep_graph)
