from pathlib import Path
from codegraphcontext.utils.tree_sitter_manager import get_tree_sitter_manager

def main():
    manager = get_tree_sitter_manager()
    lang = manager.get_language_safe('php')
    from tree_sitter import Parser
    parser = Parser(lang)
    
    code = """<?php
    class Foo {
        public function bar($a) {
            $this->baz();
            Foo::staticMethod();
            printf("Hello");
            $obj = new ClassName();
        }
    }
    """
    
    tree = parser.parse(bytes(code, "utf8"))
    print(tree.root_node)

if __name__ == "__main__":
    main()
