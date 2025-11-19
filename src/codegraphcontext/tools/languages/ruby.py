from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from codegraphcontext.utils.debug_log import debug_log, info_logger, error_logger, warning_logger, debug_logger

RUBY_QUERIES = {
    "functions": """
        (method
            name: (identifier) @name
        ) @function_node
    """,
    "classes": """
        (class
            name: (constant) @name
        ) @class
    """,
    "modules": """
        (module
            name: (constant) @name
        ) @module_node
    """,
    "imports": """
        (call
            method: (identifier) @method_name
            arguments: (argument_list
                (string) @path
            )
        ) @import
    """,
    "calls": """
        (call
            method: (identifier) @name
        )
    """,
    "variables": """
        (assignment
            left: (identifier) @name
            right: (_) @value
        )
        (assignment
            left: (instance_variable) @name
            right: (_) @value
        )
    """,
    "comments": """
        (comment) @comment
    """,
    "module_includes": """
        (call
          method: (identifier) @method
          arguments: (argument_list (constant) @module)
        ) @include_call
    """,
}


class RubyTreeSitterParser:
    """A Ruby-specific parser using tree-sitter."""

    def __init__(self, generic_parser_wrapper: Any):
        self.generic_parser_wrapper = generic_parser_wrapper
        self.language_name = "ruby"
        self.language = generic_parser_wrapper.language
        self.parser = generic_parser_wrapper.parser

        self.queries = {
            name: self.language.query(query_str)
            for name, query_str in RUBY_QUERIES.items()
        }

    def _get_node_text(self, node: Any) -> str:
        return node.text.decode("utf-8")
    
    def _enclosing_class_name(self, node: Any) -> Optional[str]:
        name, typ, _ = self._get_parent_context(node, ('class',))
        return name
    
    def _find_modules(self, root_node: Any) -> list[Dict[str, Any]]:
        modules = []
        query = self.queries["modules"]
        # name via captures
        captures = list(query.captures(root_node))
        for node, cap in captures:
            if cap == "module_node":
                name = None
                for n, c in captures:
                    if c == "name":
                        if n.start_byte >= node.start_byte and n.end_byte <= node.end_byte:
                            name = self._get_node_text(n)
                            break
                if name:
                    modules.append({
                        "name": name,
                        "line_number": node.start_point[0] + 1,
                        "end_line": node.end_point[0] + 1,
                        "source": self._get_node_text(node),
                        "source_code": self._get_node_text(node),
                        "lang": self.language_name,
                        "is_dependency": False,
                    })
        return modules

    def _find_module_inclusions(self, root_node: Any) -> list[Dict[str, Any]]:
        includes = []
        query = self.queries["module_includes"]
        for node, cap in query.captures(root_node):
            if cap == "method":
                method_name = self._get_node_text(node)
                if method_name != "include":
                    continue
            if cap == "include_call":
                method = None
                module = None
                for n, c in query.captures(node):
                    if c == "method":
                        method = self._get_node_text(n)
                    elif c == "module":
                        module = self._get_node_text(n)
                if method == "include" and module:
                    cls = self._enclosing_class_name(node)
                    if cls:
                        includes.append({
                            "class": cls,
                            "module": module,
                            "line_number": node.start_point[0] + 1,
                            "lang": self.language_name,
                            "is_dependency": False,
                        })
        return includes


    def _get_parent_context(self, node: Any, types: Tuple[str, ...] = ('class', 'module', 'method')):
        """Find parent context for Ruby constructs."""
        curr = node.parent
        while curr:
            if curr.type in types:
                name_node = curr.child_by_field_name('name')
                if name_node:
                    return self._get_node_text(name_node), curr.type, curr.start_point[0] + 1
            curr = curr.parent
        return None, None, None

    def _calculate_complexity(self, node: Any) -> int:
        """Calculate cyclomatic complexity for Ruby constructs."""
        complexity_nodes = {
            "if", "unless", "case", "when", "while", "until", "for", "rescue", "ensure",
            "and", "or", "&&", "||", "?", "ternary"
        }
        count = 1

        def traverse(n):
            nonlocal count
            if n.type in complexity_nodes:
                count += 1
            for child in n.children:
                traverse(child)

        traverse(node)
        return count

    def _get_docstring(self, node: Any) -> Optional[str]:
        """Extract comments as docstrings for Ruby constructs."""
        # Look for comments before the node
        prev_sibling = node.prev_sibling
        while prev_sibling and prev_sibling.type in ('comment', '\n', ' '):
            if prev_sibling.type == 'comment':
                comment_text = self._get_node_text(prev_sibling)
                if comment_text.startswith('#') and not comment_text.startswith('#!'):
                    return comment_text.strip()
            prev_sibling = prev_sibling.prev_sibling
        return None

    def _parse_method_parameters(self, method_node: Any) -> list[str]:
        """Parse method parameters from a method node."""
        params = []
        # Look for parameters in the method node
        for child in method_node.children:
            if child.type == 'identifier' and child != method_node.child_by_field_name('name'):
                # This is likely a parameter
                params.append(self._get_node_text(child))
        return params

    def parse(self, file_path: Path, is_dependency: bool = False) -> Dict[str, Any]:
        """Parses a Ruby file and returns its structure."""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            source_code = f.read()

        tree = self.parser.parse(bytes(source_code, "utf8"))
        root_node = tree.root_node

        functions = self._find_functions(root_node)
        classes = self._find_classes(root_node)
        imports = self._find_imports(root_node)
        function_calls = self._find_calls(root_node)
        variables = self._find_variables(root_node)
        modules = self._find_modules(root_node)
        module_inclusions = self._find_module_inclusions(root_node)

        return {
            "file_path": str(file_path),
            "functions": functions,
            "classes": classes,
            "variables": variables,
            "imports": imports,
            "function_calls": function_calls,
            "is_dependency": is_dependency,
            "lang": self.language_name,
            "modules": modules,
            "module_inclusions": module_inclusions,
        }

    def _find_functions(self, root_node: Any) -> list[Dict[str, Any]]:
        """Find all function/method definitions."""
        functions = []
        query = self.queries["functions"]
        
        # Collect all captures first
        all_captures = list(query.captures(root_node))
        
        # Group captures by function node using a different approach
        captures_by_function = {}
        for node, capture_name in all_captures:
            if capture_name == 'function_node':
                captures_by_function[id(node)] = {'node': node, 'name': None}
        
        # Now find names for each function
        for node, capture_name in all_captures:
            if capture_name == 'name':
                # Find which function this name belongs to
                for func_id, func_data in captures_by_function.items():
                    func_node = func_data['node']
                    # Check if this name node is within the function node
                    if (node.start_byte >= func_node.start_byte and 
                        node.end_byte <= func_node.end_byte):
                        captures_by_function[func_id]['name'] = self._get_node_text(node)
                        break

        # Build function entries
        for func_data in captures_by_function.values():
            func_node = func_data['node']
            name = func_data['name']
            
            if name:
                args = self._parse_method_parameters(func_node)

                # Get context and docstring
                context, context_type, _ = self._get_parent_context(func_node)
                class_context = context if context_type in ('class', 'module') else None
                docstring = self._get_docstring(func_node)

                functions.append({
                    "name": name,
                    "line_number": func_node.start_point[0] + 1,
                    "end_line": func_node.end_point[0] + 1,
                    "args": args,
                    "source": self._get_node_text(func_node),
                    "source_code": self._get_node_text(func_node),
                    "docstring": docstring,
                    "cyclomatic_complexity": self._calculate_complexity(func_node),
                    "context": context,
                    "context_type": context_type,
                    "class_context": class_context,
                    "decorators": [],
                    "lang": self.language_name,
                    "is_dependency": False,
                })

        return functions

    def _find_classes(self, root_node: Any) -> list[Dict[str, Any]]:
        """Find all class and module definitions."""
        classes = []
        query = self.queries["classes"]
        
        # Collect all captures first
        all_captures = list(query.captures(root_node))
        
        # Group captures by class node using a different approach
        captures_by_class = {}
        for node, capture_name in all_captures:
            if capture_name == 'class':
                captures_by_class[id(node)] = {'node': node, 'name': None}
        
        # Now find names for each class
        for node, capture_name in all_captures:
            if capture_name == 'name':
                # Find which class this name belongs to
                for class_id, class_data in captures_by_class.items():
                    class_node = class_data['node']
                    # Check if this name node is within the class node
                    if (node.start_byte >= class_node.start_byte and 
                        node.end_byte <= class_node.end_byte):
                        captures_by_class[class_id]['name'] = self._get_node_text(node)
                        break

        # Build class entries
        for class_data in captures_by_class.values():
            class_node = class_data['node']
            name = class_data['name']
            
            if name:
                # Get superclass for inheritance (simplified)
                bases = []

                # Get docstring
                docstring = self._get_docstring(class_node)

                classes.append({
                    "name": name,
                    "line_number": class_node.start_point[0] + 1,
                    "end_line": class_node.end_point[0] + 1,
                    "bases": bases,
                    "source": self._get_node_text(class_node),
                    "source_code": self._get_node_text(class_node),
                    "docstring": docstring,
                    "context": None,
                    "decorators": [],
                    "lang": self.language_name,
                    "is_dependency": False,
                })

        return classes

    def _find_imports(self, root_node: Any) -> list[Dict[str, Any]]:
        """Find all require/load statements."""
        imports = []
        query = self.queries["imports"]
        
        # Collect all captures first
        all_captures = list(query.captures(root_node))
        
        # Group captures by import node using a different approach
        captures_by_import = {}
        for node, capture_name in all_captures:
            if capture_name == 'import':
                captures_by_import[id(node)] = {'node': node, 'method_name': None, 'path': None}
        
        # Now find method names and paths for each import
        for node, capture_name in all_captures:
            if capture_name == 'method_name':
                # Find which import this method name belongs to
                for import_id, import_data in captures_by_import.items():
                    import_node = import_data['node']
                    # Check if this method name node is within the import node
                    if (node.start_byte >= import_node.start_byte and 
                        node.end_byte <= import_node.end_byte):
                        captures_by_import[import_id]['method_name'] = self._get_node_text(node)
                        break
            elif capture_name == 'path':
                # Find which import this path belongs to
                for import_id, import_data in captures_by_import.items():
                    import_node = import_data['node']
                    # Check if this path node is within the import node
                    if (node.start_byte >= import_node.start_byte and 
                        node.end_byte <= import_node.end_byte):
                        captures_by_import[import_id]['path'] = self._get_node_text(node)
                        break

        # Build import entries
        for import_data in captures_by_import.values():
            import_node = import_data['node']
            method_name = import_data['method_name']
            path = import_data['path']
            
            if method_name and path:
                path = path.strip('\'"')
                
                # Only process require/load statements
                if method_name in ('require', 'require_relative', 'load'):
                    imports.append({
                        "name": path,
                        "full_import_name": f"{method_name} '{path}'",
                        "line_number": import_node.start_point[0] + 1,
                        "alias": None,
                        "lang": self.language_name,
                        "is_dependency": False,
                    })

        return imports

    def _find_calls(self, root_node: Any) -> list[Dict[str, Any]]:
        """Find all function and method calls."""
        calls = []
        query = self.queries["calls"]
        
        for node, capture_name in query.captures(root_node):
            if capture_name == 'name':
                name = self._get_node_text(node)
                full_name = name

                calls.append({
                    "name": name,
                    "full_name": full_name,
                    "line_number": node.start_point[0] + 1,
                    "args": [],  # Placeholder - could be enhanced to extract arguments
                    "inferred_obj_type": None,
                    "context": None,  # Placeholder
                    "class_context": None,  # Placeholder
                    "lang": self.language_name,
                    "is_dependency": False,
                })

        return calls

    def _find_variables(self, root_node: Any) -> list[Dict[str, Any]]:
        """Find all variable assignments."""
        variables = []
        query = self.queries["variables"]
        
        # Group captures by assignment node
        captures_by_assignment = {}
        for node, capture_name in query.captures(root_node):
            if capture_name == 'name':
                # Find the parent assignment node
                current = node.parent
                while current and current.type != 'assignment':
                    current = current.parent
                if current:
                    assignment_id = id(current)
                    if assignment_id not in captures_by_assignment:
                        captures_by_assignment[assignment_id] = {'node': current, 'name': None, 'value': None}
                    captures_by_assignment[assignment_id]['name'] = self._get_node_text(node)
            elif capture_name == 'value':
                # Find the parent assignment node
                current = node.parent
                while current and current.type != 'assignment':
                    current = current.parent
                if current:
                    assignment_id = id(current)
                    if assignment_id not in captures_by_assignment:
                        captures_by_assignment[assignment_id] = {'node': current, 'name': None, 'value': None}
                    captures_by_assignment[assignment_id]['value'] = self._get_node_text(node)

        # Build variable entries
        for var_data in captures_by_assignment.values():
            name = var_data['name']
            value = var_data['value']
            
            if name:
                # Determine variable type based on name prefix
                var_type = "local"
                if name.startswith("@"):
                    var_type = "instance"
                elif name.startswith("@@"):
                    var_type = "class"
                elif name.startswith("$"):
                    var_type = "global"

                variables.append({
                    "name": name,
                    "line_number": var_data['node'].start_point[0] + 1,
                    "value": value,
                    "type": var_type,
                    "context": None,  # Placeholder
                    "class_context": None,  # Placeholder
                    "lang": self.language_name,
                    "is_dependency": False,
                })

        return variables


def pre_scan_ruby(files: list[Path], parser_wrapper) -> dict:
    """Scans Ruby files to create a map of class/method names to their file paths."""
    imports_map = {}
    query_str = """
        (class
            name: (constant) @name
        )
        (module
            name: (constant) @name
        )
        (method
            name: (identifier) @name
        )
    """
    query = parser_wrapper.language.query(query_str)

    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                tree = parser_wrapper.parser.parse(bytes(f.read(), "utf8"))

            for capture, _ in query.captures(tree.root_node):
                name = capture.text.decode('utf-8')
                if name not in imports_map:
                    imports_map[name] = []
                imports_map[name].append(str(file_path.resolve()))
        except Exception as e:
            warning_logger(f"Tree-sitter pre-scan failed for {file_path}: {e}")
    
    return imports_map
