
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import logging
import re

logger = logging.getLogger(__name__)

CPP_QUERIES = {
    "functions": """
        (function_definition
            declarator: (function_declarator
                declarator: (identifier) @name
                parameters: (parameter_list) @params
            )
        ) @function_node
    """,
    "classes": """
        (class_specifier
            name: (type_identifier) @name
            (base_class_clause (base_class (type_identifier) @base))?
        ) @class
    """,
    "imports": """
        (preproc_include
            path: [
                (string_literal) @path
                (system_lib_string) @path
            ]
        ) @import
    """,
    "calls": """
        (call_expression
            function: [
                (identifier) @name
                (scoped_identifier) @name
                (field_expression) @member_call
            ]
        )
    """,
    "variables": """
        [
            (declaration
                type: (_)
                declarator: (init_declarator
                    declarator: (identifier) @name
                )
            )
            (field_declaration
                type: (_)
                declarator: (field_declarator
                    declarator: (field_identifier) @member
                )
            )
        ]
    """,
}

class CppTreeSitterParser:
    """A C++-specific parser using tree-sitter."""

    def __init__(self, generic_parser_wrapper):
        self.generic_parser_wrapper = generic_parser_wrapper
        self.language_name = "cpp"
        self.language = generic_parser_wrapper.language
        self.parser = generic_parser_wrapper.parser

        self.queries = {
            name: self.language.query(query_str)
            for name, query_str in CPP_QUERIES.items()
        }

    def _get_node_text(self, node) -> str:
        return node.text.decode('utf-8')

    def parse(self, file_path: Path, is_dependency: bool = False) -> Dict:
        """Parses a C++ file and returns its structure."""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            source_code = f.read()

        tree = self.parser.parse(bytes(source_code, "utf8"))
        root_node = tree.root_node

        functions = self._find_functions(root_node)
        classes = self._find_classes(root_node)
        imports = self._find_imports(root_node)
        variables = self._find_variables(root_node)
        function_calls = self._find_calls(root_node)
        
        return {
            "file_path": str(file_path),
            "functions": functions,
            "classes": classes,
            "variables": variables,
            "imports": imports,
            "function_calls": function_calls,
            "is_dependency": is_dependency,
            "lang": self.language_name,
        }

    def _find_functions(self, root_node):
        functions = []
        query = self.queries['functions']
        current = {"func_node": None, "name": None, "params": None}
        for node, cap in query.captures(root_node):
            if cap == 'function_node':
                current = {"func_node": node, "name": None, "params": None}
            elif cap == 'name':
                current["name"] = self._get_node_text(node)
                # function_node is three levels up from name in this query shape
                if current.get("func_node") is None:
                    current["func_node"] = node.parent.parent.parent if node.parent and node.parent.parent and node.parent.parent.parent else node
            elif cap == 'params':
                current["params"] = node
            # When we have name and func_node, emit (params optional)
            if current.get("func_node") is not None and current.get("name") is not None:
                param_list = self._extract_parameters(current.get("params")) if current.get("params") is not None else []
                fn_node = current["func_node"]
                functions.append({
                    "name": current["name"],
                    "line_number": fn_node.start_point[0] + 1,
                    "end_line": fn_node.end_point[0] + 1,
                    "source_code": self._get_node_text(fn_node),
                    "args": param_list,
                })
                current = {"func_node": None, "name": None, "params": None}
        return functions

    def _find_classes(self, root_node):
        classes = []
        query = self.queries['classes']
        current = {"class_node": None, "name": None, "bases": []}
        for node, cap in query.captures(root_node):
            if cap == 'class':
                # Emit previous if pending
                if current["class_node"] is not None and current["name"] is not None:
                    classes.append({
                        "name": current["name"],
                        "line_number": current["class_node"].start_point[0] + 1,
                        "end_line": current["class_node"].end_point[0] + 1,
                        "source_code": self._get_node_text(current["class_node"]),
                        "bases": current["bases"],
                    })
                current = {"class_node": node, "name": None, "bases": []}
            elif cap == 'name':
                current["name"] = self._get_node_text(node)
                if current.get("class_node") is None:
                    current["class_node"] = node.parent
            elif cap == 'base':
                current["bases"].append(self._get_node_text(node))
        # flush last
        if current["class_node"] is not None and current["name"] is not None:
            classes.append({
                "name": current["name"],
                "line_number": current["class_node"].start_point[0] + 1,
                "end_line": current["class_node"].end_point[0] + 1,
                "source_code": self._get_node_text(current["class_node"]),
                "bases": current["bases"],
            })
        return classes

    def _find_imports(self, root_node):
        imports = []
        query = self.queries['imports']
        for node, cap in query.captures(root_node):
            if cap == 'path':
                raw = self._get_node_text(node)
                path = raw.strip('<>"')
                imports.append({
                    "name": path,
                    "full_import_name": path,
                    "line_number": node.start_point[0] + 1,
                    "alias": None,
                })
        return imports

    def _extract_parameters(self, params_node):
        params = []
        if params_node is None:
            return params
        # parameter_list: "(" (parameter_declaration ("," parameter_declaration)*)? ")"
        for child in params_node.children:
            if child.type == 'parameter_declaration':
                params.append(self._summarize_parameter(child))
        return params

    def _summarize_parameter(self, param_node):
        # Heuristic: use full text and try to split into type and name where possible
        text = self._get_node_text(param_node).strip()
        name = None
        # Try to find identifier child for name
        for desc in param_node.children:
            if desc.type in ('identifier', 'field_identifier'):
                name = self._get_node_text(desc)
                break
        return {"name": name, "text": text}

    def _find_variables(self, root_node):
        variables = []
        query = self.queries['variables']
        for node, cap in query.captures(root_node):
            if cap == 'name' or cap == 'member':
                variables.append({
                    "name": self._get_node_text(node),
                    "line_number": node.start_point[0] + 1,
                })
        return variables

    def _find_calls(self, root_node):
        calls = []
        query = self.queries['calls']
        for node, cap in query.captures(root_node):
            if cap == 'name':
                calls.append({
                    "name": self._get_node_text(node),
                    "line_number": node.start_point[0] + 1,
                })
            elif cap == 'member_call':
                # field_expression like obj.method -> record full text
                calls.append({
                    "name": self._get_node_text(node),
                    "line_number": node.start_point[0] + 1,
                })
        return calls
