from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Set
import logging
import re

logger = logging.getLogger(__name__)

C_QUERIES = {
    "functions": """
        (function_definition
            declarator: (function_declarator
                declarator: (identifier) @name
            )
        ) @function_node
        
        (function_definition
            declarator: (function_declarator
                declarator: (pointer_declarator
                    declarator: (identifier) @name
                )
            )
        ) @function_node
    """,
    "structs": """
        (struct_specifier
            name: (type_identifier) @name
        ) @struct
    """,
    "unions": """
        (union_specifier
            name: (type_identifier) @name
        ) @union
    """,
    "enums": """
        (enum_specifier
            name: (type_identifier) @name
        ) @enum
    """,
    "typedefs": """
        (type_definition
            declarator: (type_identifier) @name
        ) @typedef
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
            function: (identifier) @name
        )
    """,
    "variables": """
        (declaration
            declarator: (init_declarator
                declarator: (identifier) @name
            )
        )
        
        (declaration
            declarator: (init_declarator
                declarator: (pointer_declarator
                    declarator: (identifier) @name
                )
            )
        )
        
        (declaration
            declarator: (identifier) @name
        )
        
        (declaration
            declarator: (pointer_declarator
                declarator: (identifier) @name
            )
        )
    """,
    "macros": """
        (preproc_def
            name: (identifier) @name
        ) @macro
    """,
}

class CTreeSitterParser:
    """A C-specific parser using tree-sitter with improved validation."""

    def __init__(self, generic_parser_wrapper: Any):
        self.generic_parser_wrapper = generic_parser_wrapper
        self.language_name = "c"
        self.language = generic_parser_wrapper.language
        self.parser = generic_parser_wrapper.parser

        self.queries = {
            name: self.language.query(query_str)
            for name, query_str in C_QUERIES.items()
        }

    def _get_node_text(self, node: Any) -> str:
        return node.text.decode("utf-8")

    def parse(self, file_path: Path, is_dependency: bool = False) -> Dict[str, Any]:
        """Parses a C file and returns its structure."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                source_code = f.read()

            if not source_code.strip():
                logger.warning(f"Empty or whitespace-only file: {file_path}")
                return self._empty_result(file_path, is_dependency)

            tree = self.parser.parse(bytes(source_code, "utf8"))
            root_node = tree.root_node

            functions = self._find_functions(root_node)
            classes = self._find_structs_unions_enums(root_node)
            imports = self._find_imports(root_node, source_code)
            function_calls = self._find_calls(root_node)
            variables = self._find_variables(root_node)
            macros = self._find_macros(root_node)

            logger.info(f"Parsed {file_path}: {len(functions)} functions, "
                       f"{len(classes)} structs/unions/enums, {len(function_calls)} calls")

            return {
                "file_path": str(file_path),
                "functions": functions,
                "classes": classes,
                "variables": variables,
                "imports": imports,
                "function_calls": function_calls,
                "macros": macros,
                "is_dependency": is_dependency,
                "lang": self.language_name,
            }
        except Exception as e:
            logger.error(f"Error parsing C file {file_path}: {e}", exc_info=True)
            return self._empty_result(file_path, is_dependency)

    def _empty_result(self, file_path: Path, is_dependency: bool) -> Dict[str, Any]:
        return {
            "file_path": str(file_path),
            "functions": [],
            "classes": [],
            "variables": [],
            "imports": [],
            "function_calls": [],
            "macros": [],
            "is_dependency": is_dependency,
            "lang": self.language_name,
        }

    def _get_parent_context(self, node: Any, types: tuple = ('function_definition', 'struct_specifier', 'union_specifier', 'enum_specifier')) -> tuple:
        """Get parent context for nested constructs."""
        curr = node.parent
        while curr:
            if curr.type in types:
                name_node = curr.child_by_field_name('name')
                if name_node:
                    return self._get_node_text(name_node), curr.type, curr.start_point[0] + 1
                # For function_definition, look for declarator
                if curr.type == 'function_definition':
                    for child in curr.children:
                        if child.type == 'function_declarator':
                            declarator = child.child_by_field_name('declarator')
                            if declarator:
                                if declarator.type == 'identifier':
                                    return self._get_node_text(declarator), curr.type, curr.start_point[0] + 1
                                elif declarator.type == 'pointer_declarator':
                                    inner = declarator.child_by_field_name('declarator')
                                    if inner and inner.type == 'identifier':
                                        return self._get_node_text(inner), curr.type, curr.start_point[0] + 1
            curr = curr.parent
        return None, None, None

    def _find_containing_function(self, node: Any) -> Optional[str]:
        """Find the function that contains this node."""
        curr = node.parent
        while curr:
            if curr.type == 'function_definition':
                for child in curr.children:
                    if child.type == 'function_declarator':
                        declarator = child.child_by_field_name('declarator')
                        if declarator:
                            if declarator.type == 'identifier':
                                return self._get_node_text(declarator)
                            elif declarator.type == 'pointer_declarator':
                                inner = declarator.child_by_field_name('declarator')
                                if inner and inner.type == 'identifier':
                                    return self._get_node_text(inner)
            curr = curr.parent
        return None

    def _calculate_complexity(self, node: Any) -> int:
        """Calculate cyclomatic complexity for C functions."""
        complexity_nodes = {
            "if_statement", "for_statement", "while_statement", "do_statement",
            "switch_statement", "case_statement", "conditional_expression",
            "logical_expression", "binary_expression", "goto_statement"
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
        """Extract comments as documentation."""
        if node.parent:
            for child in node.parent.children:
                if child.type == 'comment' and child.start_point[0] < node.start_point[0]:
                    return self._get_node_text(child)
        return None

    def _parse_function_args(self, params_node: Any) -> list[Dict[str, Any]]:
        """Enhanced helper to parse function arguments from a (parameter_list) node."""
        args = []
        if not params_node:
            return args
            
        for param in params_node.named_children:
            if param.type == "parameter_declaration":
                arg_info: Dict[str, Any] = {"name": "", "type": None, "is_pointer": False, "is_array": False}
                
                # Find the declarator (variable name)
                declarator = param.child_by_field_name("declarator")
                if declarator:
                    if declarator.type == "identifier":
                        arg_info["name"] = self._get_node_text(declarator)
                    elif declarator.type == "pointer_declarator":
                        arg_info["is_pointer"] = True
                        inner_declarator = declarator.child_by_field_name("declarator")
                        if inner_declarator and inner_declarator.type == "identifier":
                            arg_info["name"] = self._get_node_text(inner_declarator)
                    elif declarator.type == "array_declarator":
                        arg_info["is_array"] = True
                        inner_declarator = declarator.child_by_field_name("declarator")
                        if inner_declarator and inner_declarator.type == "identifier":
                            arg_info["name"] = self._get_node_text(inner_declarator)
                
                # Find the type
                type_node = param.child_by_field_name("type")
                if type_node:
                    arg_info["type"] = self._get_node_text(type_node)
                
                args.append(arg_info)
            
            # Handle variadic arguments
            elif param.type == "variadic_parameter":
                args.append({
                    "name": "...",
                    "type": "variadic",
                    "is_pointer": False,
                    "is_array": False
                })
        
        return args

    def _find_functions(self, root_node: Any) -> list[Dict[str, Any]]:
        functions = []
        seen_functions = set()
        query = self.queries["functions"]
        
        for match in query.captures(root_node):
            capture_name = match[1]
            node = match[0]
            if capture_name == 'name':
                func_node = node.parent.parent.parent
                name = self._get_node_text(node)
                
                # Create unique key
                func_key = f"{name}:{node.start_point[0]}"
                if func_key in seen_functions:
                    continue
                seen_functions.add(func_key)
                
                # Check for static keyword
                is_static = False
                return_type = None
                for child in func_node.children:
                    if child.type == 'storage_class_specifier':
                        if self._get_node_text(child) == 'static':
                            is_static = True
                    elif child.type in ['primitive_type', 'type_identifier', 'sized_type_specifier']:
                        return_type = self._get_node_text(child)
                
                # Find parameters
                params_node = None
                body_node = None
                for child in func_node.children:
                    if child.type == "function_declarator":
                        params_node = child.child_by_field_name("parameters")
                    elif child.type == "compound_statement":
                        body_node = child
                
                args = self._parse_function_args(params_node) if params_node else []
                context, context_type, _ = self._get_parent_context(func_node)

                functions.append({
                    "name": name,
                    "full_name": name,
                    "line_number": node.start_point[0] + 1,
                    "end_line": func_node.end_point[0] + 1,
                    "args": [arg["name"] for arg in args if arg["name"]],
                    "source": self._get_node_text(func_node),
                    "source_code": self._get_node_text(func_node),
                    "docstring": self._get_docstring(func_node),
                    "cyclomatic_complexity": self._calculate_complexity(func_node) if body_node else 1,
                    "context": context,
                    "context_type": context_type,
                    "class_context": None,
                    "decorators": [],
                    "lang": self.language_name,
                    "is_dependency": False,
                    "is_static": is_static,
                    "return_type": return_type,
                    "detailed_args": args,
                })
        return functions

    def _find_structs_unions_enums(self, root_node: Any) -> list[Dict[str, Any]]:
        """Find structs, unions, and enums (treated as classes in C)."""
        classes = []
        seen_classes = set()
        
        # Find structs
        query = self.queries["structs"]
        for match in query.captures(root_node):
            capture_name = match[1]
            node = match[0]
            if capture_name == 'name':
                struct_node = node.parent
                name = self._get_node_text(node)
                
                # Deduplication
                class_key = f"struct:{name}:{node.start_point[0]}"
                if class_key in seen_classes:
                    continue
                seen_classes.add(class_key)
                
                context, context_type, _ = self._get_parent_context(struct_node)
                
                classes.append({
                    "name": name,
                    "full_name": name,
                    "line_number": node.start_point[0] + 1,
                    "end_line": struct_node.end_point[0] + 1,
                    "bases": [],
                    "source": self._get_node_text(struct_node),
                    "docstring": self._get_docstring(struct_node),
                    "context": context,
                    "decorators": [],
                    "lang": self.language_name,
                    "is_dependency": False,
                    "type": "struct",
                })

        # Find unions
        query = self.queries["unions"]
        for match in query.captures(root_node):
            capture_name = match[1]
            node = match[0]
            if capture_name == 'name':
                union_node = node.parent
                name = self._get_node_text(node)
                
                class_key = f"union:{name}:{node.start_point[0]}"
                if class_key in seen_classes:
                    continue
                seen_classes.add(class_key)
                
                context, context_type, _ = self._get_parent_context(union_node)
                
                classes.append({
                    "name": name,
                    "full_name": name,
                    "line_number": node.start_point[0] + 1,
                    "end_line": union_node.end_point[0] + 1,
                    "bases": [],
                    "source": self._get_node_text(union_node),
                    "docstring": self._get_docstring(union_node),
                    "context": context,
                    "decorators": [],
                    "lang": self.language_name,
                    "is_dependency": False,
                    "type": "union",
                })

        # Find enums
        query = self.queries["enums"]
        for match in query.captures(root_node):
            capture_name = match[1]
            node = match[0]
            if capture_name == 'name':
                enum_node = node.parent
                name = self._get_node_text(node)
                
                class_key = f"enum:{name}:{node.start_point[0]}"
                if class_key in seen_classes:
                    continue
                seen_classes.add(class_key)
                
                context, context_type, _ = self._get_parent_context(enum_node)
                
                classes.append({
                    "name": name,
                    "full_name": name,
                    "line_number": node.start_point[0] + 1,
                    "end_line": enum_node.end_point[0] + 1,
                    "bases": [],
                    "source": self._get_node_text(enum_node),
                    "docstring": self._get_docstring(enum_node),
                    "context": context,
                    "decorators": [],
                    "lang": self.language_name,
                    "is_dependency": False,
                    "type": "enum",
                })

        return classes

    def _find_imports(self, root_node: Any, source_code: str) -> list[Dict[str, Any]]:
        imports = []
        seen_imports = set()
        query = self.queries["imports"]
        
        for match in query.captures(root_node):
            capture_name = match[1]
            node = match[0]
            if capture_name == 'path':
                import_node = node.parent
                path = self._get_node_text(node).strip('"<>')
                
                # Deduplication
                if path in seen_imports:
                    continue
                seen_imports.add(path)
                
                # Determine if system include (angle brackets) or local (quotes)
                import_text = self._get_node_text(import_node)
                is_system = '<' in import_text
                
                context, context_type, _ = self._get_parent_context(node)
                
                imports.append({
                    "name": path,
                    "full_import_name": path,
                    "line_number": node.start_point[0] + 1,
                    "alias": None,
                    "is_system": is_system,
                    "context": context,
                    "lang": self.language_name,
                    "is_dependency": is_system,  # System includes are dependencies
                })
        return imports

    def _find_calls(self, root_node: Any) -> list[Dict[str, Any]]:
        """Enhanced function call detection with context and deduplication."""
        calls = []
        seen_calls = set()
        query = self.queries["calls"]
        
        for match in query.captures(root_node):
            capture_name = match[1]
            node = match[0]
            if capture_name == "name":
                call_node = node.parent if node.parent.type == "call_expression" else node.parent.parent
                call_name = self._get_node_text(node)
                
                # Get containing function for context
                func_context = self._find_containing_function(call_node)
                
                # Create unique key to prevent duplicates
                call_key = f"{func_context}:{call_name}:{node.start_point[0]}"
                if call_key in seen_calls:
                    continue
                seen_calls.add(call_key)
                
                # Extract arguments
                args = []
                args_node = call_node.child_by_field_name("arguments")
                if args_node:
                    for child in args_node.children:
                        if child.type not in ['(', ')', ',']:
                            args.append(self._get_node_text(child))
                
                context, context_type, _ = self._get_parent_context(call_node)
                
                calls.append({
                    "name": call_name,
                    "full_name": call_name,
                    "line_number": node.start_point[0] + 1,
                    "args": args,
                    "inferred_obj_type": None,
                    "context": (func_context, None),  # (function, class)
                    "class_context": (None, None),
                    "lang": self.language_name,
                    "is_dependency": False,
                })
        return calls

    def _find_variables(self, root_node: Any) -> list[Dict[str, Any]]:
        """Enhanced variable declaration detection."""
        variables = []
        seen_variables = set()
        query = self.queries["variables"]
        
        for match in query.captures(root_node):
            capture_name = match[1]
            node = match[0]
            if capture_name == "name":
                var_name = self._get_node_text(node)
                
                # Find the declaration node
                decl_node = node.parent
                while decl_node and decl_node.type != "declaration":
                    decl_node = decl_node.parent
                
                # Skip if inside function (local variables)
                func_context = self._find_containing_function(node)
                if func_context:
                    continue  # Only capture global variables
                
                # Deduplication
                var_key = f"{var_name}:{node.start_point[0]}"
                if var_key in seen_variables:
                    continue
                seen_variables.add(var_key)
                
                # Extract type information
                var_type = None
                is_pointer = False
                is_array = False
                is_static = False
                is_extern = False
                is_const = False
                value = None
                
                if decl_node:
                    # Check for storage class and type qualifiers
                    for child in decl_node.children:
                        if child.type == "storage_class_specifier":
                            spec = self._get_node_text(child)
                            if spec == "static":
                                is_static = True
                            elif spec == "extern":
                                is_extern = True
                        elif child.type == "type_qualifier":
                            if self._get_node_text(child) == "const":
                                is_const = True
                        elif child.type in ["primitive_type", "type_identifier", "sized_type_specifier"]:
                            var_type = self._get_node_text(child)
                        elif child.type == "init_declarator":
                            # Check for pointer/array
                            if child.child_by_field_name("declarator"):
                                declarator = child.child_by_field_name("declarator")
                                if declarator.type == "pointer_declarator":
                                    is_pointer = True
                                elif declarator.type == "array_declarator":
                                    is_array = True
                            
                            # Check for initial value
                            if child.child_by_field_name("value"):
                                value = self._get_node_text(child.child_by_field_name("value"))
                
                context, context_type, _ = self._get_parent_context(node)
                class_context, _, _ = self._get_parent_context(node, types=('struct_specifier', 'union_specifier', 'enum_specifier'))
                
                variables.append({
                    "name": var_name,
                    "line_number": node.start_point[0] + 1,
                    "value": value,
                    "type": var_type,
                    "context": context,
                    "class_context": class_context,
                    "lang": self.language_name,
                    "is_dependency": False,
                    "is_pointer": is_pointer,
                    "is_array": is_array,
                    "is_static": is_static,
                    "is_extern": is_extern,
                    "is_const": is_const,
                })
        return variables

    def _find_macros(self, root_node: Any) -> list[Dict[str, Any]]:
        """Enhanced preprocessor macro detection."""
        macros = []
        seen_macros = set()
        query = self.queries["macros"]
        
        for match in query.captures(root_node):
            capture_name = match[1]
            node = match[0]
            if capture_name == 'name':
                macro_node = node.parent
                name = self._get_node_text(node)
                
                # Deduplication
                macro_key = f"{name}:{node.start_point[0]}"
                if macro_key in seen_macros:
                    continue
                seen_macros.add(macro_key)
                
                # Extract macro value
                value = None
                if macro_node.child_by_field_name("value"):
                    value = self._get_node_text(macro_node.child_by_field_name("value"))
                
                # Extract parameters for function-like macros
                params = []
                if macro_node.child_by_field_name("parameters"):
                    params_node = macro_node.child_by_field_name("parameters")
                    for child in params_node.children:
                        if child.type == "identifier":
                            params.append(self._get_node_text(child))
                
                context, context_type, _ = self._get_parent_context(macro_node)
                
                macros.append({
                    "name": name,
                    "line_number": node.start_point[0] + 1,
                    "end_line": macro_node.end_point[0] + 1,
                    "source": self._get_node_text(macro_node),
                    "value": value,
                    "params": params,
                    "is_function_like": len(params) > 0,
                    "context": context,
                    "lang": self.language_name,
                    "is_dependency": False,
                })
        return macros


def pre_scan_c(files: list[Path], parser_wrapper) -> dict:
    """Scans C files to create a map of function/struct/union/enum names to their file paths."""
    imports_map = {}
    query_str = """
        (function_definition
            declarator: (function_declarator
                declarator: (identifier) @name
            )
        )
        
        (function_definition
            declarator: (function_declarator
                declarator: (pointer_declarator
                    declarator: (identifier) @name
                )
            )
        )
        
        (struct_specifier
            name: (type_identifier) @name
        )
        
        (union_specifier
            name: (type_identifier) @name
        )
        
        (enum_specifier
            name: (type_identifier) @name
        )
        
        (type_definition
            declarator: (type_identifier) @name
        )
        
        (preproc_def
            name: (identifier) @name
        )
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
    
    logger.info(f"Pre-scanned {len(files)} C files, found {len(imports_map)} symbols")
    return imports_map