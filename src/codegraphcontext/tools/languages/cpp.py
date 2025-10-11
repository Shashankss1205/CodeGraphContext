
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
            )
        ) @function_node
    """,
    "classes": """
        (class_specifier
            name: (type_identifier) @name
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
            function: (identifier) @name
        )
    """,
    "enums":"""
        (enum_specifier
            name: (type_identifier) @name
            body: (enumerator_list
                (enumerator
                    name: (identifier) @value
                    )*
                )? @body
        ) @enum
    """,
    "structs":"""
        (struct_specifier
            name: (type_identifier) @name
            body: (field_declaration_list)? @body
        ) @struct
    """,
    "unions": """
    (union_specifier
    name: (type_identifier)? @name
    body: (field_declaration_list
        (field_declaration
            declarator: [
                (field_identifier) @value
                (pointer_declarator (field_identifier) @value)
                (array_declarator (field_identifier) @value)
                ]
            )*
        )? @body
    ) @union
  
    """,
    "macros": """
        (preproc_def
            name: (identifier) @name
        ) @macro
    """,
    "templates": """
        (template_declaration
            parameters: (template_parameter_list) @params 
        )@template
    """,
    "variables": """
    (declaration
        declarator: (init_declarator
                        declarator: (identifier) @name))

    (declaration
        declarator: (init_declarator
                        declarator: (pointer_declarator
                            declarator: (identifier) @name)))
    """,
    "lambda_assignments": """
    ; Match a lambda assigned to a variable
    (declaration
        declarator: (init_declarator
            declarator: (identifier) @name
            value: (lambda_expression) @lambda_node))
    """
    
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

    def parse(self, file_path: Path, is_dependency: bool = False, **kwargs) -> Dict:
        """Parses a C++ file and returns its structure."""
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            source_code = f.read()

        tree = self.parser.parse(bytes(source_code, "utf8"))
        root_node = tree.root_node

        functions = self._find_functions(root_node)
        functions.extend(self._find_lambda_assignments(root_node))
        classes = self._find_classes(root_node)
        imports = self._find_imports(root_node)
        structs = self._find_structs(root_node)
        enums = self._find_enums(root_node)
        unions = self._find_unions(root_node)
        macros = self._find_macros(root_node)
        templates = self._find_templates(root_node)
        variables = self._find_variables(root_node)
        
        return {
            "file_path": str(file_path),
            "functions": functions,
            "classes": classes,
            "structs": structs,
            "enums": enums,
            "unions": unions,
            "macros": macros,
            "variables": variables,  
            "declarations": [], # Placeholder
            "imports": imports,
            "function_calls": [],  # Placeholder
            "is_dependency": is_dependency,
            "lang": self.language_name,
            "templates": templates,
        }

    def _find_functions(self, root_node):
        functions = []
        query = self.queries['functions']
        for match in query.captures(root_node):
            capture_name = match[1]
            node = match[0]
            if capture_name == 'name':
                func_node = node.parent.parent.parent
                name = self._get_node_text(node)
                functions.append({
                    "name": name,
                    "line_number": node.start_point[0] + 1,
                    "end_line": func_node.end_point[0] + 1,
                    "source_code": self._get_node_text(func_node),
                    "args": [], # Placeholder
                })
        return functions

    def _find_classes(self, root_node):
        classes = []
        query = self.queries['classes']
        for match in query.captures(root_node):
            capture_name = match[1]
            node = match[0]
            if capture_name == 'name':
                class_node = node.parent
                name = self._get_node_text(node)
                classes.append({
                    "name": name,
                    "line_number": node.start_point[0] + 1,
                    "end_line": class_node.end_point[0] + 1,
                    "source_code": self._get_node_text(class_node),
                    "bases": [], # Placeholder
                })
        return classes

    def _find_imports(self, root_node):
        imports = []
        query = self.queries['imports']
        for match in query.captures(root_node):
            capture_name = match[1]
            node = match[0]
            if capture_name == 'path':
                path = self._get_node_text(node).strip('<>')
                imports.append({
                    "name": path,
                    "full_import_name": path,
                    "line_number": node.start_point[0] + 1,
                    "alias": None,
                })
        return imports
    
    def _find_enums(self, root_node):
        enums = []
        query = self.queries['enums']
        for node, capture_name in query.captures(root_node):
            if capture_name == 'name':
                name = self._get_node_text(node)
                enum_node = node.parent
                enums.append({
                    "name": name,
                    "line_number": node.start_point[0] + 1,
                    "end_line": enum_node.end_point[0] + 1,
                    "source_code": self._get_node_text(enum_node),
                })
        return enums
 
    def _find_structs(self, root_node):
        structs = []
        query = self.queries['structs']
        for node, capture_name in query.captures(root_node):
            if capture_name == 'name':
                name = self._get_node_text(node)
                struct_node = node.parent
                structs.append({
                    "name": name,
                    "line_number": node.start_point[0] + 1,
                    "end_line": struct_node.end_point[0] + 1,
                    "source_code": self._get_node_text(struct_node),
                })
        return structs

    def _find_unions(self, root_node):
        unions = []
        query = self.queries['unions']
        for node, capture_name in query.captures(root_node):
            if capture_name == 'name':
                name = self._get_node_text(node)
                union_node = node.parent
                unions.append({
                    "name": name,
                    "line_number": node.start_point[0] + 1,
                    "end_line": union_node.end_point[0] + 1,
                    "source_code": self._get_node_text(union_node),
                })
        return unions

    def _find_macros(self, root_node):
        macros = []
        query = self.queries['macros']
        for match in query.captures(root_node):
            capture_name = match[1]
            node = match[0]
            if capture_name == 'name':
                macro_node = node.parent
                name = self._get_node_text(node)
                macros.append({
                    "name": name,
                    "line_number": node.start_point[0] + 1,
                    "end_line": macro_node.end_point[0] + 1,
                    "source_code": self._get_node_text(macro_node),
                })
        return macros
    
    def _find_templates(self, root_node):
        templates = []
        query = self.queries['templates']
        for match in query.captures(root_node):
            capture_name = match[1]
            node = match[0]
            if capture_name == 'template':  
                name = self._extract_template_name(node)
                templates.append({
                    "name": name,
                    "line_number": node.start_point[0] + 1,
                    "end_line": node.end_point[0] + 1,
                    "source_code": self._get_node_text(node),
                })
        return  templates
    
    def _extract_template_name(self, template_node):
        """Extract the name from a template declaration."""
        for child in template_node.children:
            if child.type == 'function_definition':
                 for descendent in child.children:
                     if descendent.type == 'function_declarator':
                         for node in descendent.children:
                             if node.type == 'identifier':
                                 return self._get_node_text(node)
            elif child.type == 'class_specifier':
                 for node in child.children:
                     if node.type == 'type_identifier':
                         return self._get_node_text(node)
            elif child.type == 'struct-specifier':
                for node in child.children :
                    if node.type == 'type_identifier':
                        return self._get_node_text(node)
                    
        return "unnamed_template"
    def _find_lambda_assignments(self, root_node):
        functions = []
        query = self.queries.get('lambda_assignments')
        if not query: return []

        for match in query.captures(root_node):
            capture_name = match[1]
            node = match[0]

            if capture_name == 'name':
                assignment_node = node.parent
                lambda_node = assignment_node.child_by_field_name('value')
            if lambda_node is None or lambda_node.type != 'lambda_expression':
                continue

            params_node = lambda_node.child_by_field_name('declarator')
            if params_node:
                params_node = params_node.child_by_field_name('parameters')
                name = self._get_node_text(node)
                params_node = lambda_node.child_by_field_name('parameters')
                
                context, context_type, _ = self._get_parent_context(assignment_node)
                class_context, _, _ = self._get_parent_context(assignment_node, types=('class_definition',))

                func_data = {
                    "name": name,
                    "line_number": node.start_point[0] + 1,
                    "end_line": assignment_node.end_point[0] + 1,
                    "args": [p for p in [self._get_node_text(p) for p in params_node.children if p.type == 'identifier'] if p] if params_node else [],
                    "source": self._get_node_text(assignment_node),
                    "source_code": self._get_node_text(assignment_node),
                    "docstring": None,
                    "cyclomatic_complexity": 1,
                    "context": context,
                    "context_type": context_type,
                    "class_context": class_context,
                    "decorators": [],
                    "lang": self.language_name,
                    "is_dependency": False,
                }
                functions.append(func_data)
        return functions
    
    def _find_variables(self, root_node):
        variables = []
        query = self.queries['variables']
        for match in query.captures(root_node):
            capture_name = match[1]
            node = match[0]

            if capture_name == 'name':
                assignment_node = node.parent

                # Skip lambda assignments, they are handled by _find_lambda_assignments
                right_node = assignment_node.child_by_field_name('value')
                if right_node and right_node.type == 'lambda_expression':
                    continue

                name = self._get_node_text(node)
                value = self._get_node_text(right_node) if right_node else None
                
                type_node = assignment_node.child_by_field_name('type')
                type_text = self._get_node_text(type_node) if type_node else None

                context, _, _ = self._get_parent_context(node)
                class_context, _, _ = self._get_parent_context(node, types=('class_definition',))

                variable_data = {
                    "name": name,
                    "line_number": node.start_point[0] + 1,
                    "value": value,
                    "type": type_text,
                    "context": context,
                    "class_context": class_context,
                    "lang": self.language_name,
                    "is_dependency": False,
                }
                variables.append(variable_data)
        return variables
    
    def _get_parent_context(self, node, types=('function_definition', 'class_definition')):
        curr = node.parent
        while curr:
            if curr.type in types:
                name_node = curr.child_by_field_name('name')
                return self._get_node_text(name_node) if name_node else None, curr.type, curr.start_point[0] + 1
            curr = curr.parent
        return None, None, None

def pre_scan_cpp(files: list[Path], parser_wrapper) -> dict:
    """
    Quickly scans C++ files to build a map of top-level class, struct, and function names
    to their file paths.
    """
    imports_map = {}

    query_str = """
        (class_specifier name: (type_identifier) @name)
        (struct_specifier name: (type_identifier) @name)
        (function_definition declarator: (function_declarator declarator: (identifier) @name))
    """
    query = parser_wrapper.language.query(query_str)

    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                source_bytes = f.read().encode("utf-8")
                tree = parser_wrapper.parser.parse(source_bytes)

            for node, capture_name in query.captures(tree.root_node):
                if capture_name == "name":
                    name = node.text.decode("utf-8")
                    imports_map.setdefault(name, []).append(str(file_path.resolve()))
        except Exception as e:
            logger.warning(f"Tree-sitter pre-scan failed for {file_path}: {e}")

    return imports_map
