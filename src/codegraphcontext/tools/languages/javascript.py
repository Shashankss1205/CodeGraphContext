from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import logging
import ast # Not strictly needed for JS, but kept for consistency if AST manipulation is added

logger = logging.getLogger(__name__)

JS_QUERIES = {
    "functions": """
        (function_declaration 
            name: (identifier) @name
            parameters: (formal_parameters) @params
        ) @function_node
        
        (variable_declarator 
            name: (identifier) @name 
            value: (function 
                parameters: (formal_parameters) @params
            ) @function_node
        )
        
        (variable_declarator 
            name: (identifier) @name 
            value: (arrow_function 
                parameters: (formal_parameters) @params
            ) @function_node
        )
        
        (variable_declarator 
            name: (identifier) @name 
            value: (arrow_function 
                parameter: (identifier) @single_param
            ) @function_node
        )
        
        (method_definition 
            name: (property_identifier) @name
            parameters: (formal_parameters) @params
        ) @function_node
        
        (assignment_expression
            left: (member_expression 
                property: (property_identifier) @name
            )
            right: (function
                parameters: (formal_parameters) @params
            ) @function_node
        )
        
        (assignment_expression
            left: (member_expression 
                property: (property_identifier) @name
            )
            right: (arrow_function
                parameters: (formal_parameters) @params
            ) @function_node
        )
    """,
    "classes": """
        (class_declaration name: (identifier) @name)
        (class name: (identifier) @name) @class_node
    """,
    "imports": """
        (import_statement
            source: (string) @import_path
        )
        (import_statement
            (import_clause
                (identifier) @default_import_name  ; default import
            )
            source: (string) @import_path
        )
        (import_statement
            (import_clause
                (named_imports
                    (import_specifier (identifier) @imported_name)  ; named import
                    (import_specifier name: (identifier) @imported_name alias: (identifier) @imported_alias) ; named import with alias
                )
            )
            source: (string) @import_path
        )
        (import_statement
            (import_clause
                (namespace_import (identifier) @namespace_name)  ; namespace import
            )
            source: (string) @import_path
        )
        (call_expression
            function: (identifier) @require_call (#eq? @require_call "require")
            arguments: (arguments (string) @require_path)
        )
    """,
    "calls": """
        (call_expression function: (identifier) @name)
        (call_expression function: (member_expression property: (property_identifier) @name))
    """,
    "variables": """
        (variable_declarator name: (identifier) @name)
    """,
    "docstrings": """
        (comment) @docstring_comment
    """,
}

class JavascriptTreeSitterParser:
    """A JavaScript-specific parser using tree-sitter, encapsulating language-specific logic."""

    def __init__(self, generic_parser_wrapper):
        self.generic_parser_wrapper = generic_parser_wrapper
        self.language_name = generic_parser_wrapper.language_name
        self.language = generic_parser_wrapper.language
        self.parser = generic_parser_wrapper.parser

        self.queries = {
            name: self.language.query(query_str)
            for name, query_str in JS_QUERIES.items()
        }

    def _get_node_text(self, node) -> str:
        return node.text.decode('utf-8')

    def _get_parent_context(self, node, types=('function_declaration', 'class_declaration')):
        # JS specific context types
        curr = node.parent
        while curr:
            if curr.type in types:
                name_node = curr.child_by_field_name('name')
                return self._get_node_text(name_node) if name_node else None, curr.type, curr.start_point[0] + 1
            curr = curr.parent
        return None, None, None

    def _calculate_complexity(self, node):
        # JS specific complexity nodes
        complexity_nodes = {
            "if_statement", "for_statement", "while_statement", "do_statement",
            "switch_statement", "case_statement", "conditional_expression",
            "logical_expression", "binary_expression", "catch_clause"
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

    def _get_docstring(self, body_node):
        # JS specific docstring extraction (e.g., JSDoc comments)
        # This is a placeholder and needs more sophisticated logic
        return None

    def parse(self, file_path: Path, is_dependency: bool = False) -> Dict:
        """Parses a file and returns its structure in a standardized dictionary format."""
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()
        
        tree = self.parser.parse(bytes(source_code, "utf8"))
        root_node = tree.root_node

        functions = self._find_functions(root_node)
        classes = self._find_classes(root_node)
        imports = self._find_imports(root_node)
        function_calls = self._find_calls(root_node)
        variables = self._find_variables(root_node)

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
        
        # Collect all captures and group them by the function they belong to
        captures_by_function = {}
        
        for node, capture_name in query.captures(root_node):
            if capture_name == 'function_node':
                func_id = id(node)
                if func_id not in captures_by_function:
                    captures_by_function[func_id] = {
                        'node': node,
                        'name': None,
                        'params': None,
                        'single_param': None
                    }
            elif capture_name == 'name':
                # Find which function this name belongs to
                func_node = self._find_function_node_for_name(node)
                if func_node:
                    func_id = id(func_node)
                    if func_id not in captures_by_function:
                        captures_by_function[func_id] = {
                            'node': func_node,
                            'name': None,
                            'params': None,
                            'single_param': None
                        }
                    captures_by_function[func_id]['name'] = self._get_node_text(node)
            elif capture_name == 'params':
                # Find which function these params belong to
                func_node = self._find_function_node_for_params(node)
                if func_node:
                    func_id = id(func_node)
                    if func_id not in captures_by_function:
                        captures_by_function[func_id] = {
                            'node': func_node,
                            'name': None,
                            'params': None,
                            'single_param': None
                        }
                    captures_by_function[func_id]['params'] = node
            elif capture_name == 'single_param':
                # Find which function this single param belongs to
                func_node = self._find_function_node_for_params(node)
                if func_node:
                    func_id = id(func_node)
                    if func_id not in captures_by_function:
                        captures_by_function[func_id] = {
                            'node': func_node,
                            'name': None,
                            'params': None,
                            'single_param': None
                        }
                    captures_by_function[func_id]['single_param'] = node
        
        # Process each function
        for func_id, data in captures_by_function.items():
            if data['name']:  # Only process if we have a name
                func_node = data['node']
                name = data['name']
                
                # Extract parameters
                args = []
                if data['params']:
                    args = self._extract_parameters(data['params'])
                elif data['single_param']:
                    args = [self._get_node_text(data['single_param'])]
                
                # Get context information
                context, context_type, context_line = self._get_parent_context(func_node)
                class_context = context if context_type == 'class_declaration' else None
                
                # Extract JSDoc comment if available
                docstring = self._get_jsdoc_comment(func_node)
                
                func_data = {
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
                    "decorators": [],  # JS doesn't have decorators like Python
                    "lang": self.language_name,
                    "is_dependency": False,
                }
                functions.append(func_data)
        
        return functions
    
    def _find_function_node_for_name(self, name_node):
        """Find the function node that contains this name node."""
        current = name_node.parent
        while current:
            if current.type in ('function_declaration', 'function', 'arrow_function', 'method_definition'):
                return current
            elif current.type in ('variable_declarator', 'assignment_expression'):
                # Check if this declarator/assignment contains a function
                for child in current.children:
                    if child.type in ('function', 'arrow_function'):
                        return child
            current = current.parent
        return None
    
    def _find_function_node_for_params(self, params_node):
        """Find the function node that contains this parameters node."""
        current = params_node.parent
        while current:
            if current.type in ('function_declaration', 'function', 'arrow_function', 'method_definition'):
                return current
            current = current.parent
        return None
    
    def _extract_parameters(self, params_node):
        """Extract parameter names from formal_parameters node."""
        params = []
        if params_node.type == 'formal_parameters':
            for child in params_node.children:
                if child.type == 'identifier':
                    params.append(self._get_node_text(child))
                elif child.type == 'assignment_pattern':
                    # Default parameter: param = defaultValue
                    left_child = child.child_by_field_name('left')
                    if left_child and left_child.type == 'identifier':
                        params.append(self._get_node_text(left_child))
                elif child.type == 'rest_pattern':
                    # Rest parameter: ...args
                    argument = child.child_by_field_name('argument')
                    if argument and argument.type == 'identifier':
                        params.append(f"...{self._get_node_text(argument)}")
        return params
    
    def _get_jsdoc_comment(self, func_node):
        """Extract JSDoc comment preceding the function."""
        # Look for comments before the function
        prev_sibling = func_node.prev_sibling
        while prev_sibling and prev_sibling.type in ('comment', '\n', ' '):
            if prev_sibling.type == 'comment':
                comment_text = self._get_node_text(prev_sibling)
                if comment_text.startswith('/**') and comment_text.endswith('*/'):
                    return comment_text.strip()
            prev_sibling = prev_sibling.prev_sibling
        return None

    def _find_classes(self, root_node):
        classes = []
        query = self.queries['classes']
        for match in query.captures(root_node):
            capture_name = match[1]
            node = match[0]

            # Placeholder for JS class extraction logic
            if capture_name == 'name':
                class_node = node.parent
                name = self._get_node_text(node)
                
                # Simplified bases extraction for now
                bases = []
                # Need to find extends clause for JS classes

                class_data = {
                    "name": name,
                    "line_number": node.start_point[0] + 1,
                    "end_line": class_node.end_point[0] + 1,
                    "bases": bases,
                    "source": self._get_node_text(class_node),
                    "docstring": self._get_docstring(class_node), # Placeholder
                    "context": None, # Placeholder
                    "decorators": [],
                    "lang": self.language_name,
                    "is_dependency": False,
                }
                classes.append(class_data)
        return classes

    def _find_imports(self, root_node):
        imports = []
        seen_modules = set()
        query = self.queries['imports']
        for node, capture_name in query.captures(root_node):
            # Placeholder for JS import extraction logic
            # This will need to handle ES6 imports and CommonJS requires
            if capture_name in ('import_path', 'imported_name', 'namespace_name', 'default_name', 'require_path'):
                module_name = self._get_node_text(node)
                if module_name not in seen_modules:
                    seen_modules.add(module_name)
                    imports.append({
                        "name": module_name,
                        "full_import_name": module_name,
                        "line_number": node.start_point[0] + 1,
                        "alias": None,
                        "context": None, # Placeholder
                        "lang": self.language_name,
                        "is_dependency": False,
                    })
        return imports

    def _find_calls(self, root_node):
        calls = []
        query = self.queries['calls']
        for node, capture_name in query.captures(root_node):
            # Placeholder for JS call extraction logic
            if capture_name == 'name':
                call_node = node.parent
                name = self._get_node_text(node)
                
                # Simplified args extraction for now
                args = []

                call_data = {
                    "name": name,
                    "full_name": self._get_node_text(call_node), # This might need refinement
                    "line_number": node.start_point[0] + 1,
                    "args": args,
                    "inferred_obj_type": None,
                    "context": None, # Placeholder
                    "class_context": None, # Placeholder
                    "lang": self.language_name,
                    "is_dependency": False,
                }
                calls.append(call_data)
        return calls

    def _find_variables(self, root_node):
        variables = []
        query = self.queries['variables']
        for match in query.captures(root_node):
            capture_name = match[1]
            node = match[0]

            # Placeholder for JS variable extraction logic
            if capture_name == 'name':
                var_node = node.parent
                name = self._get_node_text(node)
                value = None # Placeholder
                type_text = None # Placeholder

                variable_data = {
                    "name": name,
                    "line_number": node.start_point[0] + 1,
                    "value": value,
                    "type": type_text,
                    "context": None, # Placeholder
                    "class_context": None, # Placeholder
                    "lang": self.language_name,
                    "is_dependency": False,
                }
                variables.append(variable_data)
        return variables

def pre_scan_javascript(files: list[Path], parser_wrapper) -> dict:
    """Scans JavaScript files to create a map of class/function names to their file paths."""
    imports_map = {}
    query_str = """
        (class_declaration name: (identifier) @name)
        (function_declaration name: (identifier) @name)
        (variable_declarator name: (identifier) @name value: (function))
        (variable_declarator name: (identifier) @name value: (arrow_function))
        (method_definition name: (property_identifier) @name)
        (assignment_expression
            left: (member_expression 
                property: (property_identifier) @name
            )
            right: (function)
        )
        (assignment_expression
            left: (member_expression 
                property: (property_identifier) @name
            )
            right: (arrow_function)
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
            logger.warning(f"Tree-sitter pre-scan failed for {file_path}: {e}")
    return imports_map
