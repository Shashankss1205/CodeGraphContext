
# src/codegraphcontext/tools/graph_builder.py
import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Coroutine, Dict, Optional, Tuple
from datetime import datetime
import ast

from ..core.database import DatabaseManager
from ..core.jobs import JobManager, JobStatus
from ..utils.debug_log import debug_log

# New imports for tree-sitter
from tree_sitter import Language, Parser
from tree_sitter_languages import get_language

logger = logging.getLogger(__name__)

# This is for developers and testers only. It enables detailed debug logging to a file.
# Set to 1 to enable, 0 to disable.
debug_mode = 0

# Define tree-sitter queries for Python
PY_QUERIES = {
    "imports": """
        (import_statement name: (_) @import)
        (import_from_statement module_name: (_) @from_import)
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
            left: (identifier) @name
            right: _ @value)
    """,
    "lambda_assignments": """
        (assignment
            left: (identifier) @name
            right: (lambda) @lambda_node)
    """, # <<< MY NEW QUERY
    "docstrings": """
        (expression_statement (string) @docstring)
    """,
}

class TreeSitterParser:
    """A parser for a specific language using tree-sitter."""

    def __init__(self, language_name: str):
        self.language: Language = get_language(language_name)
        self.parser = Parser()
        self.parser.set_language(self.language)

        if language_name == 'python':
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
        functions.extend(self._find_lambda_assignments(root_node)) # <<< MY CHANGE
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
        }

    # <<< MY NEW METHOD
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
                    "is_dependency": False,
                }
                functions.append(func_data)
        return functions
    # >>> END OF NEW METHOD

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
                    "is_dependency": False,
                }
                classes.append(class_data)
        return classes

    def _find_imports(self, root_node):
        imports = []
        seen_modules = set()
        query = self.queries['imports']
        for node, capture_name in query.captures(root_node):
            if capture_name in ('import', 'from_import'):
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
                    "is_dependency": False,
                }
                imports.append(import_data)
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
                name = self._get_node_text(node)
                value_node = assignment_node.child_by_field_name('right')
                value = self._get_node_text(value_node) if value_node else None
                
                context, _, _ = self._get_parent_context(node)
                class_context, _, _ = self._get_parent_context(node, types=('class_definition',))

                variable_data = {
                    "name": name,
                    "line_number": node.start_point[0] + 1,
                    "value": value,
                    "context": context,
                    "class_context": class_context,
                    "is_dependency": False,
                }
                variables.append(variable_data)
        return variables

class GraphBuilder:
    """Module for building and managing the Neo4j code graph."""

    def __init__(self, db_manager: DatabaseManager, job_manager: JobManager, loop: asyncio.AbstractEventLoop):
        self.db_manager = db_manager
        self.job_manager = job_manager
        self.loop = loop
        self.driver = self.db_manager.get_driver()
        # --- NEW: Instantiate the parser for Python ---
        self.py_parser = TreeSitterParser('python')
        self.create_schema()

    def create_schema(self):
        """Create constraints and indexes in Neo4j."""
        with self.driver.session() as session:
            try:
                session.run("CREATE CONSTRAINT repository_path IF NOT EXISTS FOR (r:Repository) REQUIRE r.path IS UNIQUE")
                session.run("CREATE CONSTRAINT file_path IF NOT EXISTS FOR (f:File) REQUIRE f.path IS UNIQUE")
                session.run("CREATE CONSTRAINT directory_path IF NOT EXISTS FOR (d:Directory) REQUIRE d.path IS UNIQUE")
                session.run("CREATE CONSTRAINT function_unique IF NOT EXISTS FOR (f:Function) REQUIRE (f.name, f.file_path, f.line_number) IS UNIQUE")
                session.run("CREATE CONSTRAINT class_unique IF NOT EXISTS FOR (c:Class) REQUIRE (c.name, c.file_path, c.line_number) IS UNIQUE")
                session.run("CREATE CONSTRAINT variable_unique IF NOT EXISTS FOR (v:Variable) REQUIRE (v.name, v.file_path, v.line_number) IS UNIQUE")
                session.run("CREATE CONSTRAINT module_name IF NOT EXISTS FOR (m:Module) REQUIRE m.name IS UNIQUE")
                
                session.run("""
                    CREATE FULLTEXT INDEX code_search_index IF NOT EXISTS 
                    FOR (n:Function|Class|Variable) 
                    ON EACH [n.name, n.source, n.docstring]
                """)
                
                logger.info("Database schema verified/created successfully")
            except Exception as e:
                logger.warning(f"Schema creation warning: {e}")

    def _pre_scan_for_imports(self, files: list[Path]) -> dict:
        """--- REWRITTEN with tree-sitter ---
        Scans all files to create a map of class/function names to their file paths."""
        imports_map = {}
        query_str = """
            (class_definition name: (identifier) @name)
            (function_definition name: (identifier) @name)
        """
        query = self.py_parser.language.query(query_str)

        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    tree = self.py_parser.parser.parse(bytes(f.read(), "utf8"))
                
                for capture, _ in query.captures(tree.root_node):
                    name = capture.text.decode('utf-8')
                    if name not in imports_map:
                        imports_map[name] = []
                    imports_map[name].append(str(file_path.resolve()))
            except Exception as e:
                logger.warning(f"Tree-sitter pre-scan failed for {file_path}: {e}")
        return imports_map

    def add_repository_to_graph(self, repo_path: Path, is_dependency: bool = False):
        """Adds a repository node using its absolute path as the unique key."""
        repo_name = repo_path.name
        repo_path_str = str(repo_path.resolve())
        with self.driver.session() as session:
            session.run(
                """
                MERGE (r:Repository {path: $path})
                SET r.name = $name, r.is_dependency = $is_dependency
                """,
                path=repo_path_str,
                name=repo_name,
                is_dependency=is_dependency,
            )

    def add_file_to_graph(self, file_data: Dict, repo_name: str, imports_map: dict):
        logger.info("Executing add_file_to_graph with my change!")
        """Adds a file and its contents within a single, unified session."""
        file_path_str = str(Path(file_data['file_path']).resolve())
        file_name = Path(file_path_str).name
        is_dependency = file_data.get('is_dependency', False)

        with self.driver.session() as session:
            try:
                repo_result = session.run("MATCH (r:Repository {name: $repo_name}) RETURN r.path as path", repo_name=repo_name).single()
                relative_path = str(Path(file_path_str).relative_to(Path(repo_result['path']))) if repo_result else file_name
            except ValueError:
                relative_path = file_name

            session.run("""
                MERGE (f:File {path: $path})
                SET f.name = $name, f.relative_path = $relative_path, f.is_dependency = $is_dependency
            """, path=file_path_str, name=file_name, relative_path=relative_path, is_dependency=is_dependency)

            file_path_obj = Path(file_path_str)
            repo_path_obj = Path(repo_result['path'])
            
            relative_path_to_file = file_path_obj.relative_to(repo_path_obj)
            
            parent_path = str(repo_path_obj)
            parent_label = 'Repository'

            for part in relative_path_to_file.parts[:-1]:
                current_path = Path(parent_path) / part
                current_path_str = str(current_path)
                
                session.run(f"""
                    MATCH (p:{parent_label} {{path: $parent_path}})
                    MERGE (d:Directory {{path: $current_path}})
                    SET d.name = $part
                    MERGE (p)-[:CONTAINS]->(d)
                """, parent_path=parent_path, current_path=current_path_str, part=part)

                parent_path = current_path_str
                parent_label = 'Directory'

            session.run(f"""
                MATCH (p:{parent_label} {{path: $parent_path}})
                MATCH (f:File {{path: $file_path}})
                MERGE (p)-[:CONTAINS]->(f)
            """, parent_path=parent_path, file_path=file_path_str)

            for item_data, label in [(file_data['functions'], 'Function'), (file_data['classes'], 'Class'), (file_data['variables'], 'Variable')]:
                for item in item_data:
                    # Ensure cyclomatic_complexity is set for functions
                    if label == 'Function' and 'cyclomatic_complexity' not in item:
                        item['cyclomatic_complexity'] = 1 # Default value

                    query = f"""
                        MATCH (f:File {{path: $file_path}})
                        MERGE (n:{label} {{name: $name, file_path: $file_path, line_number: $line_number}})
                        SET n += $props
                        MERGE (f)-[:CONTAINS]->(n)
                    """
                    session.run(query, file_path=file_path_str, name=item['name'], line_number=item['line_number'], props=item)
                    
                    if label == 'Function':
                        for arg_name in item.get('args', []):
                            session.run("""
                                MATCH (fn:Function {name: $func_name, file_path: $file_path, line_number: $line_number})
                                MERGE (p:Parameter {name: $arg_name, file_path: $file_path, function_line_number: $line_number})
                                MERGE (fn)-[:HAS_PARAMETER]->(p)
                            """, func_name=item['name'], file_path=file_path_str, line_number=item['line_number'], arg_name=arg_name)

            for item in file_data.get('functions', []):
                if item.get("context_type") == "function_definition":
                    session.run("""
                        MATCH (outer:Function {name: $context, file_path: $file_path})
                        MATCH (inner:Function {name: $name, file_path: $file_path, line_number: $line_number})
                        MERGE (outer)-[:CONTAINS]->(inner)
                    """, context=item["context"], file_path=file_path_str, name=item["name"], line_number=item["line_number"])

            for imp in file_data['imports']:
                set_clauses = ["m.alias = $alias"]
                if 'full_import_name' in imp:
                    set_clauses.append("m.full_import_name = $full_import_name")
                set_clause_str = ", ".join(set_clauses)

                session.run(f"""
                    MATCH (f:File {{path: $file_path}})
                    MERGE (m:Module {{name: $name}})
                    SET {set_clause_str}
                    MERGE (f)-[:IMPORTS]->(m)
                """, file_path=file_path_str, **imp)

            local_class_names = {c['name'] for c in file_data.get('classes', [])}
            for class_item in file_data.get('classes', []):
                if class_item.get('bases'):
                    for base_class_name in class_item['bases']:
                        resolved_parent_file_path = self._resolve_class_path(
                            base_class_name,
                            file_path_str,
                            local_class_names,
                            file_data['imports'],
                            imports_map
                        )
                        if resolved_parent_file_path:
                            session.run("""
                                MATCH (child:Class {name: $child_name, file_path: $file_path})
                                MATCH (parent:Class {name: $parent_name, file_path: $resolved_parent_file_path})
                                MERGE (child)-[:INHERITS]->(parent)
                            """, 
                            child_name=class_item['name'], 
                            file_path=file_path_str, 
                            parent_name=base_class_name,
                            resolved_parent_file_path=resolved_parent_file_path)

            self._create_class_method_relationships(session, file_data)
            self._create_contextual_relationships(session, file_data)
    
    def _create_contextual_relationships(self, session, file_data: Dict):
        """Create CONTAINS relationships from functions/classes to their children."""
        file_path = str(Path(file_data['file_path']).resolve())
        
        for func in file_data.get('functions', []):
            if func.get('class_context'):
                session.run("""
                    MATCH (c:Class {name: $class_name, file_path: $file_path})
                    MATCH (fn:Function {name: $func_name, file_path: $file_path, line_number: $func_line})
                    MERGE (c)-[:CONTAINS]->(fn)
                """, 
                class_name=func['class_context'],
                file_path=file_path,
                func_name=func['name'],
                func_line=func['line_number'])

    def _create_function_calls(self, session, file_data: Dict, imports_map: dict):
        """Create CALLS relationships with a unified, prioritized logic flow for all call types."""
        caller_file_path = str(Path(file_data['file_path']).resolve())
        local_function_names = {func['name'] for func in file_data.get('functions', [])}
        local_imports = {imp.get('alias') or imp['name'].split('.')[-1]: imp['name'] 
                        for imp in file_data.get('imports', [])}
        
        for call in file_data.get('function_calls', []):
            called_name = call['name']
            if called_name in __builtins__: continue

            resolved_path = None
            
            if call.get('inferred_obj_type'):
                obj_type = call['inferred_obj_type']
                possible_paths = imports_map.get(obj_type, [])
                if len(possible_paths) > 0:
                    resolved_path = possible_paths[0]
            
            else:
                lookup_name = call['full_name'].split('.')[0] if '.' in call['full_name'] else called_name
                possible_paths = imports_map.get(lookup_name, [])

                if lookup_name in local_function_names:
                    resolved_path = caller_file_path
                elif len(possible_paths) == 1:
                    resolved_path = possible_paths[0]
                elif len(possible_paths) > 1 and lookup_name in local_imports:
                    full_import_name = local_imports[lookup_name]
                    for path in possible_paths:
                        if full_import_name.replace('.', '/') in path:
                            resolved_path = path
                            break
            
            if not resolved_path:
                if called_name in imports_map and imports_map[called_name]:
                    resolved_path = imports_map[called_name][0]
                else:
                    resolved_path = caller_file_path

            caller_context = call.get('context')
            if caller_context and len(caller_context) == 3 and caller_context[0] is not None:
                caller_name, _, caller_line_number = caller_context
                session.run("""
                    MATCH (caller:Function {name: $caller_name, file_path: $caller_file_path, line_number: $caller_line_number})
                    MATCH (called:Function {name: $called_name, file_path: $called_file_path})
                    MERGE (caller)-[:CALLS {line_number: $line_number, args: $args, full_call_name: $full_call_name}]->(called)
                """,
                caller_name=caller_name,
                caller_file_path=caller_file_path,
                caller_line_number=caller_line_number,
                called_name=called_name,
                called_file_path=resolved_path,
                line_number=call['line_number'],
                args=call.get('args', []),
                full_call_name=call.get('full_name', called_name))
            else:
                session.run("""
                    MATCH (caller:File {path: $caller_file_path})
                    MATCH (called:Function {name: $called_name, file_path: $called_file_path})
                    MERGE (caller)-[:CALLS {line_number: $line_number, args: $args, full_call_name: $full_call_name}]->(called)
                """,
                caller_file_path=caller_file_path,
                called_name=called_name,
                called_file_path=resolved_path,
                line_number=call['line_number'],
                args=call.get('args', []),
                full_call_name=call.get('full_name', called_name))

    def _create_all_function_calls(self, all_file_data: list[Dict], imports_map: dict):
        """Create CALLS relationships for all functions after all files have been processed."""
        with self.driver.session() as session:
            for file_data in all_file_data:
                self._create_function_calls(session, file_data, imports_map)
    
    def _create_class_method_relationships(self, session, file_data: Dict):
        """Create CONTAINS relationships from classes to their methods"""
        file_path = str(Path(file_data['file_path']).resolve())
        
        for func in file_data.get('functions', []):
            class_context = func.get('class_context')
            if class_context:
                session.run("""
                    MATCH (c:Class {name: $class_name, file_path: $file_path})
                    MATCH (fn:Function {name: $func_name, file_path: $file_path, line_number: $func_line})
                    MERGE (c)-[:CONTAINS]->(fn)
                """, 
                class_name=class_context,
                file_path=file_path,
                func_name=func['name'],
                func_line=func['line_number'])
                
    def _resolve_class_path(self, class_name: str, current_file_path: str, local_class_names: set, current_file_imports: list, global_imports_map: dict) -> Optional[str]:
        """Resolves the file path of a class based on import resolution priority."""
        # Priority 1: Class is defined in the current file.
        if class_name in local_class_names:
            return current_file_path

        # This method now relies more heavily on the global_imports_map provided by the pre-scan
        if class_name in global_imports_map:
            # In a multi-file project, there could be multiple definitions.
            # A more robust solution would use local import context to disambiguate.
            return global_imports_map[class_name][0]
        return None
                
    def delete_file_from_graph(self, file_path: str):
        """Deletes a file and all its contained elements and relationships."""
        file_path_str = str(Path(file_path).resolve())
        with self.driver.session() as session:
            parents_res = session.run("""
                MATCH (f:File {path: $path})<-[:CONTAINS*]-(d:Directory)
                RETURN d.path as path ORDER BY d.path DESC
            """, path=file_path_str)
            parent_paths = [record["path"] for record in parents_res]

            session.run(
                """
                MATCH (f:File {path: $path})
                OPTIONAL MATCH (f)-[:CONTAINS]->(element)
                DETACH DELETE f, element
                """,
                path=file_path_str,
            )
            logger.info(f"Deleted file and its elements from graph: {file_path_str}")

            for path in parent_paths:
                session.run("""
                    MATCH (d:Directory {path: $path})
                    WHERE NOT (d)-[:CONTAINS]->()
                    DETACH DELETE d
                """, path=path)

    def delete_repository_from_graph(self, repo_path: str):
        """Deletes a repository and all its contents from the graph."""
        repo_path_str = str(Path(repo_path).resolve())
        with self.driver.session() as session:
            session.run("""MATCH (r:Repository {path: $path})
                          OPTIONAL MATCH (r)-[:CONTAINS*]->(e)
                          DETACH DELETE r, e""", path=repo_path_str)
            logger.info(f"Deleted repository and its contents from graph: {repo_path_str}")

    def update_file_in_graph(self, file_path: Path, repo_path: Path, imports_map: dict):
        """Updates a single file's nodes in the graph."""
        file_path_str = str(file_path.resolve())
        repo_name = repo_path.name
        
        self.delete_file_from_graph(file_path_str)

        if file_path.exists():
            file_data = self.parse_python_file(repo_path, file_path, imports_map)
            
            if "error" not in file_data:
                self.add_file_to_graph(file_data, repo_name, imports_map)
                return file_data
            else:
                logger.error(f"Skipping graph add for {file_path_str} due to parsing error: {file_data['error']}")
                return None
        else:
            return {"deleted": True, "path": file_path_str}

    def parse_python_file(self, repo_path: Path, file_path: Path, imports_map: dict, is_dependency: bool = False) -> Dict:
        """--- REWRITTEN with tree-sitter ---
        Parse a Python file and extract code elements using TreeSitterParser."""
        debug_log(f"[parse_python_file] Starting tree-sitter parsing for: {file_path}")
        try:
            file_data = self.py_parser.parse(file_path, is_dependency)
            file_data['repo_path'] = str(repo_path)
            if debug_mode:
                debug_log(f"[parse_python_file] Successfully parsed with tree-sitter: {file_path}")
            return file_data
        except Exception as e:
            logger.error(f"Error parsing {file_path} with tree-sitter: {e}")
            debug_log(f"[parse_python_file] Error parsing {file_path} with tree-sitter: {e}")
            return {"file_path": str(file_path), "error": str(e)}

    def estimate_processing_time(self, path: Path) -> Optional[Tuple[int, float]]:
        """Estimate processing time and file count"""
        try:
            if path.is_file():
                files = [path]
            else:
                files = list(path.rglob("*.py"))
            
            total_files = len(files)
            estimated_time = total_files * 0.05 # tree-sitter is faster
            return total_files, estimated_time
        except Exception as e:
            logger.error(f"Could not estimate processing time for {path}: {e}")
            return None

    async def build_graph_from_path_async(
        self, path: Path, is_dependency: bool = False, job_id: str = None
    ):
        """Builds graph from a directory or file path."""
        try:
            if job_id:
                self.job_manager.update_job(job_id, status=JobStatus.RUNNING)
            
            self.add_repository_to_graph(path, is_dependency)
            repo_name = path.name

            files = list(path.rglob("*.py")) if path.is_dir() else [path]
            if job_id:
                self.job_manager.update_job(job_id, total_files=len(files))
            
            debug_log("Starting pre-scan to build imports map...")
            imports_map = self._pre_scan_for_imports(files)
            debug_log(f"Pre-scan complete. Found {len(imports_map)} definitions.")

            all_file_data = []

            processed_count = 0
            for file in files:
                if file.is_file():
                    if job_id:
                        self.job_manager.update_job(job_id, current_file=str(file))
                    repo_path = path.resolve() if path.is_dir() else file.parent.resolve()
                    file_data = self.parse_python_file(repo_path, file, imports_map, is_dependency)
                    if "error" not in file_data:
                        self.add_file_to_graph(file_data, repo_name, imports_map)
                        all_file_data.append(file_data)
                    processed_count += 1
                    if job_id:
                        self.job_manager.update_job(job_id, processed_files=processed_count)
                    await asyncio.sleep(0.01)

            self._create_all_function_calls(all_file_data, imports_map)
            
            if job_id:
                self.job_manager.update_job(job_id, status=JobStatus.COMPLETED, end_time=datetime.now())
        except Exception as e:
            logger.error(f"Failed to build graph for path {path}: {e}", exc_info=True)
            if job_id:
                self.job_manager.update_job(
                    job_id, status=JobStatus.FAILED, end_time=datetime.now(), errors=[str(e)]
                )

    def add_code_to_graph_tool(
        self, path: str, is_dependency: bool = False
    ) -> Dict[str, Any]:
        """Tool to add code to Neo4j graph with background processing"""
        try:
            path_obj = Path(path).resolve()
            if not path_obj.exists():
                return {"error": f"Path {path} does not exist"}

            estimation = self.estimate_processing_time(path_obj)
            if estimation is None:
                return {"error": f"Could not analyze path {path}."}
            total_files, estimated_time = estimation

            job_id = self.job_manager.create_job(str(path_obj), is_dependency)
            self.job_manager.update_job(
                job_id, total_files=total_files, estimated_duration=estimated_time
            )

            coro = self.build_graph_from_path_async(path_obj, is_dependency, job_id)
            asyncio.run_coroutine_threadsafe(coro, self.loop)

            debug_log(f"Started background job {job_id} for path: {str(path_obj)}")

            return {
                "success": True,
                "job_id": job_id,
                "message": f"Background processing started for {path_obj}",
                "estimated_files": total_files,
                "estimated_duration_seconds": round(estimated_time, 2),
            }
        except Exception as e:
            debug_log(f"Error creating background job: {str(e)}")
            return {
                "error": f"Failed to start background processing: {e.__class__.__name__}: {e}"
            }
