import ast
import json
import sys
import os
print("Current working directory:", os.getcwd())
print("Trying to open:", sys.argv[1])


class GraphBuilder(ast.NodeVisitor):
    def __init__(self):
        self.function_calls = []

    def visit_Call(self, node):
        call_data = {
            "name": getattr(node.func, 'attr', None),
            "full_name": ast.unparse(node.func),
        }
        self.function_calls.append(call_data)
        self.generic_visit(node)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python graph_builder_local.py <path_to_python_file>")
        sys.exit(1)

    filepath = sys.argv[1]
    builder = GraphBuilder()
    with open(filepath, "r") as f:
        tree = ast.parse(f.read())
    builder.visit(tree)

    with open("function_calls.json", "w") as f:
        json.dump(builder.function_calls, f, indent=2)

    print(f"Captured {len(builder.function_calls)} calls and saved to function_calls.json")
