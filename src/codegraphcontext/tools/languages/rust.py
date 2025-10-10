
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import logging
import re

logger = logging.getLogger(__name__)

RUST_QUERIES = {
    "functions": """
        (function_item
            name: (identifier) @name
            parameters: (parameters) @params
        ) @function_node
    """,
    "classes": """
        [
            (struct_item name: (type_identifier) @name)
            (enum_item name: (type_identifier) @name)
        ] @class
    """,
    "traits": """
        (trait_item name: (type_identifier) @name) @trait
    """,
    "imports": """
        (use_declaration) @import
    """,
    "calls": """
        (call_expression
            function: [
                (identifier) @name
                (field_expression field: (field_identifier) @name)
                (scoped_identifier name: (identifier) @name)
            ]
        )
    """,
}


class RustTreeSitterParser:
    """A Rust-specific parser using tree-sitter."""

    def __init__(self, generic_parser_wrapper: Any):
        self.generic_parser_wrapper = generic_parser_wrapper
        self.language_name = "rust"
        self.language = generic_parser_wrapper.language
        self.parser = generic_parser_wrapper.parser

        self.queries = {
            name: self.language.query(query_str)
            for name, query_str in RUST_QUERIES.items()
        }

    def _get_node_text(self, node: Any) -> str:
        return node.text.decode("utf-8")

    def parse(self, file_path: Path, is_dependency: bool = False) -> Dict[str, Any]:
        """Parses a Rust file and returns its structure."""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            source_code = f.read()

        tree = self.parser.parse(bytes(source_code, "utf8"))
        root_node = tree.root_node

        functions = self._find_functions(root_node)
        classes = self._find_structs(root_node)
        traits = self._find_traits(root_node)
        imports = self._find_imports(root_node)
        function_calls = self._find_calls(root_node)

        return {
            "file_path": str(file_path),
            "functions": functions,
            "classes": classes,
            "traits": traits,
            "variables": [],  # Placeholder
            "imports": imports,
            "function_calls": function_calls,
            "is_dependency": is_dependency,
            "lang": self.language_name,
        }

    def _parse_function_args(self, params_node: Any) -> list[Dict[str, Any]]:
        """Helper to parse function arguments from a (parameters) node."""
        args = []
        for param in params_node.named_children:
            arg_info: Dict[str, Any] = {"name": "", "type": None}
            if param.type == "parameter":
                pattern_node = param.child_by_field_name("pattern")
                type_node = param.child_by_field_name("type")
                if pattern_node:
                    arg_info["name"] = self._get_node_text(pattern_node)
                if type_node:
                    arg_info["type"] = self._get_node_text(type_node)
                args.append(arg_info)
            elif param.type == "self_parameter":
                arg_info["name"] = self._get_node_text(param)
                arg_info["type"] = "self"
                args.append(arg_info)
        return args

    def _find_functions(self, root_node: Any) -> list[Dict[str, Any]]:
        functions = []
        query = self.queries["functions"]
        for match in query.matches(root_node):
            captures = {name: node for node, name in match.captures}

            func_node = captures.get("function_node")
            name_node = captures.get("name")
            params_node = captures.get("params")

            if func_node and name_node:
                name = self._get_node_text(name_node)
                args = self._parse_function_args(params_node) if params_node else []

                functions.append(
                    {
                        "name": name,
                        "line_number": name_node.start_point[0] + 1,
                        "end_line": func_node.end_point[0] + 1,
                        "source_code": self._get_node_text(func_node),
                        "args": args,
                    }
                )
        return functions

    def _find_structs(self, root_node: Any) -> list[Dict[str, Any]]:
        structs = []
        query = self.queries["classes"]
        for match in query.matches(root_node):
            captures = {name: node for node, name in match.captures}
            class_node = captures.get("class")
            name_node = captures.get("name")

            if class_node and name_node:
                name = self._get_node_text(name_node)
                structs.append(
                    {
                        "name": name,
                        "line_number": name_node.start_point[0] + 1,
                        "end_line": class_node.end_point[0] + 1,
                        "source_code": self._get_node_text(class_node),
                        "bases": [],  # Placeholder
                    }
                )
        return structs

    def _find_traits(self, root_node: Any) -> list[Dict[str, Any]]:
        traits: list[Dict[str, Any]] = []
        query = self.queries["traits"]
        for node, capture_name in query.captures(root_node):
            if capture_name != "trait":
                continue
            name_node = node.child_by_field_name("name") if hasattr(node, 'child_by_field_name') else None
            # For trait_item the capture already targets the item, and name is a child captured separately above in query
            # But to keep consistent, derive name by scanning children if needed
            name: Optional[str] = None
            for child in node.children:
                if child.type in ("type_identifier", "identifier"):
                    name = self._get_node_text(child)
                    break
            if not name:
                # Fallback: try query's named capture 'name' if present in match context
                pass
            traits.append({
                "name": name if name else "<anonymous_trait>",
                "line_number": node.start_point[0] + 1,
                "end_line": node.end_point[0] + 1,
                "source_code": self._get_node_text(node),
            })
        return traits

    def _find_imports(self, root_node: Any) -> list[Dict[str, Any]]:
        imports = []
        query = self.queries["imports"]
        for node, _ in query.captures(root_node):
            full_import_name = self._get_node_text(node)
            alias = None

            alias_match = re.search(r"as\s+(\w+)\s*;?$", full_import_name)
            if alias_match:
                alias = alias_match.group(1)
                name = alias
            else:
                cleaned_path = re.sub(r";$", "", full_import_name).strip()
                last_part = cleaned_path.split("::")[-1]
                if last_part.strip() == "*":
                    name = "*"
                else:
                    name_match = re.findall(r"(\w+)", last_part)
                    name = name_match[-1] if name_match else last_part

            imports.append(
                {
                    "name": name,
                    "full_import_name": full_import_name,
                    "line_number": node.start_point[0] + 1,
                    "alias": alias,
                }
            )
        return imports

    def _find_calls(self, root_node: Any) -> list[Dict[str, Any]]:
        """Finds all function and method calls."""
        calls = []
        query = self.queries["calls"]
        for node, capture_name in query.captures(root_node):
            if capture_name == "name":
                call_name = self._get_node_text(node)
                calls.append(
                    {
                        "name": call_name,
                        "line_number": node.start_point[0] + 1,
                    }
                )
        return calls

def pre_scan_rust(files: list[Path], parser_wrapper) -> dict:
    """Scans Rust files to create a map of function/struct/enum/trait names to their file paths."""
    imports_map = {}
    query_str = """
        (function_item name: (identifier) @name)
        (struct_item name: (type_identifier) @name)
        (enum_item name: (type_identifier) @name)
        (trait_item name: (type_identifier) @name)
    """
    query = parser_wrapper.language.query(query_str)

    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                tree = parser_wrapper.parser.parse(bytes(f.read(), "utf8"))

            for capture, _ in query.captures(tree.root_node):
                name = capture.text.decode('utf-8')
                if name not in imports_map:
                    imports_map[name] = []
                imports_map[name].append(str(file_path.resolve()))
        except Exception as e:
            logger.warning(f"Tree-sitter pre-scan failed for {file_path}: {e}")
    return imports_map