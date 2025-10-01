from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import logging
import ast

logger = logging.getLogger(__name__)

PY_QUERIES = {
    "imports": """
        (import_statement name: (_) @import)
        (import_from_statement) @from_import_stmt
    """,
    "classes": """
        (class_definition
            name: (identifier) @name
            superclasses: (argument_list)? @superclasses
            body: (block) @body)
    """,
    "functions": """
        (function_definition
            name: (identifier) @name
            parameters: (parameters) @parameters
            body: (block) @body
            return_type: (_)? @return_type)
    """,
    "calls": """
        (call
            function: (identifier) @name)
        (call
            function: (attribute attribute: (identifier) @name) @full_call)
    """,
    "variables": """
        (assignment
            left: (identifier) @name)
    """,
    "lambda_assignments": """
        (assignment
            left: (identifier) @name
            right: (lambda) @lambda_node)
    """,
    "docstrings": """
        (expression_statement (string) @docstring)
    """,
}

class PythonTreeSitterParser:
    """A Python-specific parser using tree-sitter, encapsulating language-specific logic."""

    def __init__(self, generic_parser_wrapper):
        self.generic_parser_wrapper = generic_parser_wrapper
        self.language_name = generic_parser_wrapper.language_name
        self.language = generic_parser_wrapper.language
        self.parser = generic_parser_wrapper.parser

        self.queries = {
            name: self.language.query(query_str)
            for name, query_str in PY_QUERIES.items()
        }

    def _get_node_text(self, node) -> str:
        return node.text.decode('utf-8')

    def _get_parent_context(self, node, types=('function_definition', 'class_definition')):
        curr = node.parent
        while curr:
            if curr.type in types:
                name_node = curr.child_by_field_name('name')
                return self._get_node_text(name_node) if name_node else None, curr.type, curr.start_point[0] + 1
            curr = curr.parent
        return None, None, None

    def _calculate_complexity(self, node):
        complexity_nodes = {
            "if_statement", "for_statement", "while_statement", "except_clause",
            "with_statement", "boolean_operator", "list_comprehension", 
            "generator_expression", "case_clause"
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
        if body_node and body_node.child_count > 0:
            first_child = body_node.children[0]
            if first_child.type == 'expression_statement' and first_child.children[0].type == 'string':
                try:
                    return ast.literal_eval(self._get_node_text(first_child.children[0]))
                except (ValueError, SyntaxError):
                    return self._get_node_text(first_child.children[0])
        return None

    def parse(self, file_path: Path, is_dependency: bool = False) -> Dict:
        """Parses a file and returns its structure in a standardized dictionary format."""
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()
        
        tree = self.parser.parse(bytes(source_code, "utf8"))
        root_node = tree.root_node

        functions = self._find_functions(root_node)
        functions.extend(self._find_lambda_assignments(root_node))
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

    def _find_lambda_assignments(self, root_node):
        functions = []
        query = self.queries.get('lambda_assignments')
        if not query: return []

        for match in query.captures(root_node):
            capture_name = match[1]
            node = match[0]

            if capture_name == 'name':
                assignment_node = node.parent
                lambda_node = assignment_node.child_by_field_name('right')
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

    def _find_functions(self, root_node):
        functions = []
        query = self.queries['functions']
        for match in query.captures(root_node):
            capture_name = match[1]
            node = match[0]

            if capture_name == 'name':
                func_node = node.parent
                name = self._get_node_text(node)
                params_node = func_node.child_by_field_name('parameters')
                body_node = func_node.child_by_field_name('body')
                
                decorators = [self._get_node_text(child) for child in func_node.children if child.type == 'decorator']

                context, context_type, _ = self._get_parent_context(func_node)
                class_context, _, _ = self._get_parent_context(func_node, types=('class_definition',))

                args = []
                if params_node:
                    for p in params_node.children:
                        arg_text = None
                        if p.type == 'identifier':
                            arg_text = self._get_node_text(p)
                        elif p.type == 'default_parameter':
                            name_node = p.child_by_field_name('name')
                            if name_node:
                                arg_text = self._get_node_text(name_node)
                        if arg_text:
                            args.append(arg_text)

                func_data = {
                    "name": name,
                    "line_number": node.start_point[0] + 1,
                    "end_line": func_node.end_point[0] + 1,
                    "args": args,
                    "source": self._get_node_text(func_node),
                    "source_code": self._get_node_text(func_node),
                    "docstring": self._get_docstring(body_node),
                    "cyclomatic_complexity": self._calculate_complexity(func_node),
                    "context": context,
                    "context_type": context_type,
                    "class_context": class_context,
                    "decorators": [d for d in decorators if d],
                    "lang": self.language_name,
                    "is_dependency": False,
                }
                functions.append(func_data)
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
                body_node = class_node.child_by_field_name('body')
                superclasses_node = class_node.child_by_field_name('superclasses')
                
                bases = []
                if superclasses_node:
                    bases = [self._get_node_text(child) for child in superclasses_node.children if child.type in ('identifier', 'attribute')]

                decorators = [self._get_node_text(child) for child in class_node.children if child.type == 'decorator']

                context, _, _ = self._get_parent_context(class_node)

                class_data = {
                    "name": name,
                    "line_number": node.start_point[0] + 1,
                    "end_line": class_node.end_point[0] + 1,
                    "bases": [b for b in bases if b],
                    "source": self._get_node_text(class_node),
                    "docstring": self._get_docstring(body_node),
                    "context": context,
                    "decorators": [d for d in decorators if d],
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
            if capture_name in ('import', 'from_import_stmt'):
                # For 'import_statement'
                if capture_name == 'import':
                    node_text = self._get_node_text(node)
                    alias = None
                    if ' as ' in node_text:
                        parts = node_text.split(' as ')
                        full_name = parts[0].strip()
                        alias = parts[1].strip()
                    else:
                        full_name = node_text.strip()

                    if full_name in seen_modules:
                        continue
                    seen_modules.add(full_name)

                    import_data = {
                        "name": full_name,
                        "full_import_name": full_name,
                        "line_number": node.start_point[0] + 1,
                        "alias": alias,
                        "context": self._get_parent_context(node)[:2],
                        "lang": self.language_name,
                        "is_dependency": False,
                    }
                    imports.append(import_data)
                # For 'import_from_statement'
                elif capture_name == 'from_import_stmt':
                    module_name_node = node.child_by_field_name('module_name')
                    if not module_name_node: continue
                    
                    module_name = self._get_node_text(module_name_node)
                    
                    # Handle 'from ... import ...'
                    import_list_node = node.child_by_field_name('name')
                    if import_list_node:
                        for child in import_list_node.children:
                            imported_name = None
                            alias = None
                            if child.type == 'aliased_import':
                                name_node = child.child_by_field_name('name')
                                alias_node = child.child_by_field_name('alias')
                                if name_node: imported_name = self._get_node_text(name_node)
                                if alias_node: alias = self._get_node_text(alias_node)
                            elif child.type == 'dotted_name' or child.type == 'identifier':
                                imported_name = self._get_node_text(child)
                            
                            if imported_name:
                                full_import_name = f"{module_name}.{imported_name}"
                                if full_import_name in seen_modules:                                                                                                
                                    continue                                                                                                                        
                                seen_modules.add(full_import_name) 
                                imports.append({
                                    "name": imported_name,
                                    "full_import_name": full_import_name,
                                    "line_number": child.start_point[0] + 1,
                                    "alias": alias,
                                    "context": self._get_parent_context(child)[:2],
                                    "lang": self.language_name,
                                    "is_dependency": False,
                                })

        return imports

    def _find_calls(self, root_node):
        calls = []
        query = self.queries['calls']
        for node, capture_name in query.captures(root_node):
            if capture_name == 'name':
                call_node = node.parent if node.parent.type == 'call' else node.parent.parent
                full_call_node = call_node.child_by_field_name('function')
                
                args = []
                arguments_node = call_node.child_by_field_name('arguments')
                if arguments_node:
                    for arg in arguments_node.children:
                        arg_text = self._get_node_text(arg)
                        if arg_text is not None:
                            args.append(arg_text)

                call_data = {
                    "name": self._get_node_text(node),
                    "full_name": self._get_node_text(full_call_node),
                    "line_number": node.start_point[0] + 1,
                    "args": args,
                    "inferred_obj_type": None, # Type inference is a complex topic to be added
                    "context": self._get_parent_context(node),
                    "class_context": self._get_parent_context(node, types=('class_definition',))[:2],
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

            if capture_name == 'name':
                assignment_node = node.parent

                # Skip lambda assignments, they are handled by _find_lambda_assignments
                right_node = assignment_node.child_by_field_name('right')
                if right_node and right_node.type == 'lambda':
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

def pre_scan_python(files: list[Path], parser_wrapper) -> dict:
    """Scans Python files to create a map of class/function names to their file paths."""
    imports_map = {}
    query_str = """
        (class_definition name: (identifier) @name)
        (function_definition name: (identifier) @name)
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