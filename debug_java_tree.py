from tree_sitter_language_pack import get_language
from tree_sitter import Parser

JAVA_LANGUAGE = get_language("java")
parser = Parser(JAVA_LANGUAGE)

source = """
public class Test {
    void main() {
        new com.example.app.misc.Outer("outer");
        System.out.println("Hello");
    }
}
"""

tree = parser.parse(bytes(source, "utf8"))

def print_tree(node, indent=0):
    print("  " * indent + f"{node.type} ({node.start_point} - {node.end_point})")
    for child in node.children:
        print_tree(child, indent + 1)

print_tree(tree.root_node)
