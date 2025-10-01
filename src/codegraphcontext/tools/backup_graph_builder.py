# src/codegraphcontext/tools/graph_builder.py
import asyncio
import ast
import logging
import os
from pathlib import Path
from typing import Any, Coroutine, Dict, Optional, Tuple
from datetime import datetime

from ..core.database import DatabaseManager
from ..core.jobs import JobManager, JobStatus
from ..utils.debug_log import debug_log

logger = logging.getLogger(__name__)

# This is for developers and testers only. It enables detailed debug logging to a file.
# Set to 1 to enable, 0 to disable.
debug_mode = 0

class CyclomaticComplexityVisitor(ast.NodeVisitor):
    """Calculates cyclomatic complexity for a given AST node."""
    def __init__(self):
        self.complexity = 1

    def visit_If(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_For(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_While(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_With(self, node):
        self.complexity += len(node.items)
        self.generic_visit(node)

    def visit_AsyncFor(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_AsyncWith(self, node):
        self.complexity += len(node.items)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        self.complexity += len(node.values) - 1
        self.generic_visit(node)

    def visit_ListComp(self, node):
        self.complexity += len(node.generators)
        self.generic_visit(node)

    def visit_SetComp(self, node):
        self.complexity += len(node.generators)
        self.generic_visit(node)

    def visit_DictComp(self, node):
        self.complexity += len(node.generators)
        self.generic_visit(node)

    def visit_GeneratorExp(self, node):
        self.complexity += len(node.generators)
        self.generic_visit(node)

    def visit_IfExp(self, node):
        self.complexity += 1
        self.generic_visit(node)

    def visit_match_case(self, node):
        self.complexity += 1
        self.generic_visit(node)


class CodeVisitor(ast.NodeVisitor):
    """
    The final, definitive, stateful AST visitor. It correctly maintains
    class-level, local-level, and module-level symbol tables to resolve complex calls.
    """

    def __init__(self, file_path: str, imports_map: dict, is_dependency: bool = False):
        self.file_path = file_path
        self.is_dependency = is_dependency
        self.imports_map = imports_map
        self.functions, self.classes, self.variables, self.imports, self.function_calls = [], [], [], [], []
        self.context_stack, self.current_context, self.current_class = [], None, None
        
        # Stateful Symbol Tables
        self.local_symbol_table = {}
        self.class_symbol_table = {}
        self.module_symbol_table = {}

    def _push_context(self, name, node_type, line_number):
        self.context_stack.append({"name": name, "type": node_type, "line_number": line_number, "previous_context": self.current_context, "previous_class": self.current_class})
        self.current_context = name
        if node_type == "class": self.current_class = name

    def _pop_context(self):
        if self.context_stack:
            prev = self.context_stack.pop()
            self.current_context, self.current_class = prev["previous_context"], prev["previous_class"]

    def get_return_type_from_ast(self, file_path, class_name, method_name):
        if not file_path or not Path(file_path).exists():
            return None
        with open(file_path, 'r', encoding='utf-8') as source_file:
            try:
                tree = ast.parse(source_file.read())
            except (SyntaxError, ValueError):
                return None
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                for method_node in node.body:
                    if isinstance(method_node, (ast.FunctionDef, ast.AsyncFunctionDef)) and method_node.name == method_name:
                        # Case 1: The method has an explicit return type hint
                        if method_node.returns:
                            # Unparse and strip quotes to handle forward references like "'PublicKey'"
                            return ast.unparse(method_node.returns).strip("'\"")

                        # Create a mini symbol table for the scope of this method
                        local_assignments = {}
                        for body_item in method_node.body:
                            if (isinstance(body_item, ast.Assign) and 
                                isinstance(body_item.value, ast.Call) and
                                isinstance(body_item.value.func, ast.Name) and
                                isinstance(body_item.targets[0], ast.Name)):
                                    variable_name = body_item.targets[0].id
                                    class_name_assigned = body_item.value.func.id
                                    local_assignments[variable_name] = class_name_assigned

                        # Now, check the return statements from the bottom up
                        for body_item in reversed(method_node.body):
                            if isinstance(body_item, ast.Return):
                                # Case 2: It returns a direct instantiation (e.g., return MyClass())
                                if (isinstance(body_item.value, ast.Call) and
                                    isinstance(body_item.value.func, ast.Name)):
                                    return body_item.value.func.id
                                
                                # Case 3: It returns a variable that was assigned earlier (e.g., return my_var)
                                if (isinstance(body_item.value, ast.Name) and
                                    body_item.value.id in local_assignments):
                                    return local_assignments[body_item.value.id]
        return None
    def _resolve_type_from_call(self, node: ast.Call):
        if not isinstance(node.func, ast.Attribute): return None
        
        # Case 1: Base of the call is a simple name, e.g., `var.method()`
        if isinstance(node.func.value, ast.Name):
            obj_name = node.func.value.id
            method_name = node.func.attr
            # Check local, then class, then module scopes
            obj_type = (self.local_symbol_table.get(obj_name) or 
                        self.class_symbol_table.get(obj_name) or
                        self.module_symbol_table.get(obj_name))
            if obj_type:
                paths = self.imports_map.get(obj_type, [])
                if paths: return self.get_return_type_from_ast(paths[0], obj_type, method_name)
        
        # Case 2: Base of the call is another call (a chain), e.g., `var.method1().method2()`
        elif isinstance(node.func.value, ast.Call):
            intermediate_type = self._resolve_type_from_call(node.func.value)
            if intermediate_type:
                method_name = node.func.attr
                paths = self.imports_map.get(intermediate_type, [])
                if paths: return self.get_return_type_from_ast(paths[0], intermediate_type, method_name)
        return None

    def visit_ClassDef(self, node):
        self.class_symbol_table = {}
        
        class_data = {"name": node.name, "line_number": node.lineno,
                      "end_line": getattr(node, 'end_lineno', None),
                      "bases": [ast.unparse(b) for b in node.bases],
                      "source": ast.unparse(node), "context": self.current_context,
                      "is_dependency": self.is_dependency, "docstring": ast.get_docstring(node),
                      "decorators": [ast.unparse(d) for d in node.decorator_list]}
        self.classes.append(class_data)

        self._push_context(node.name, "class", node.lineno)

        # Pre-pass to populate class symbol table from __init__ or setUp
        for method_node in node.body:
            if isinstance(method_node, ast.FunctionDef) and method_node.name in ('__init__', 'setUp'):
                self._handle_constructor_assignments(method_node)
        
        # Visit all children of the class now
        self.generic_visit(node)
        self._pop_context()
        self.class_symbol_table = {}

    def _handle_constructor_assignments(self, constructor_node: ast.FunctionDef):
        """
        Infers types for class attributes assigned from constructor arguments.
        This fixes the `self.job_manager = job_manager` case.
        """
        # Get a map of argument names to their type hints (as strings)
        arg_types = {
            arg.arg: ast.unparse(arg.annotation)
            for arg in constructor_node.args.args
            if arg.annotation
        }

        # Scan the body of the constructor for assignments
        for body_node in ast.walk(constructor_node):
            if isinstance(body_node, ast.Assign):
                # Check for assignments like `self.attr = arg`
                if (
                    isinstance(body_node.targets[0], ast.Attribute)
                    and isinstance(body_node.targets[0].value, ast.Name)
                    and body_node.targets[0].value.id == "self"
                    and isinstance(body_node.value, ast.Name)
                ):
                    attr_name = body_node.targets[0].attr
                    arg_name = body_node.value.id
                    
                    if arg_name in arg_types:
                        # We found a match! Infer the type and add it to the symbol table.
                        self.class_symbol_table[attr_name] = arg_types[arg_name]
                        debug_log(f"Inferred type for self.{attr_name}: {arg_types[arg_name]}")


    def visit_FunctionDef(self, node):
        # The class pre-pass will handle setUp/__init__, so we reset the local table here
        if node.name not in ('__init__', 'setUp'):
            self.local_symbol_table = {}
        func_data = {"name": node.name, "line_number": node.lineno,
                     "end_line": getattr(node, 'end_lineno', None),
                     "args": [arg.arg for arg in node.args.args], "source": ast.unparse(node),
                     "context": self.current_context, "class_context": self.current_class,
                     "is_dependency": self.is_dependency, "docstring": ast.get_docstring(node),
                     "decorators": [ast.unparse(d) for d in node.decorator_list],
                     "source_code": ast.unparse(node)} # Add source_code here
        self.functions.append(func_data)
        self.functions.append(func_data)
        self._push_context(node.name, "function", node.lineno)
        # This will trigger visit_Assign and visit_Call for nodes inside the function
        self.generic_visit(node)
        self._pop_context()

    def visit_Assign(self, node):
        assigned_type = None
        # Manual check for nested calls to ensure they are processed
        if isinstance(node.value, ast.Call):
            # Now determine the type for the assignment target
            if isinstance(node.value.func, ast.Name):
                assigned_type = node.value.func.id
            elif isinstance(node.value.func, ast.Attribute):
                assigned_type = self._resolve_type_from_call(node.value)

                # If the main resolver fails, it's likely a class/static method call
                # like `addr = P2shAddress.from_script(...)`. We apply a heuristic:
                # assume the method returns an instance of its own class.
                if not assigned_type and isinstance(node.value.func.value, ast.Name):
                    # `node.value.func.value.id` will be 'P2shAddress' in this case
                    class_name = node.value.func.value.id
                    
                    # We can add a check to be safer: does this name correspond to an import?
                    # This check makes the heuristic much more reliable.
                    if class_name in self.imports_map:
                         assigned_type = class_name
        # Handle assignments from a different variable `var = another_var`
        elif isinstance(node.value, ast.Name):
            assigned_type = (self.local_symbol_table.get(node.value.id) or
                            self.class_symbol_table.get(node.value.id) or
                            self.module_symbol_table.get(node.value.id))
        
        if assigned_type and isinstance(assigned_type, str):
            assigned_type = assigned_type.strip("'\"")

        # Part 1: Populate symbol tables correctly
        if assigned_type:
            for target in node.targets:
                if isinstance(target, ast.Attribute) and hasattr(target.value, 'id') and target.value.id == 'self':
                    self.class_symbol_table[target.attr] = assigned_type
                elif isinstance(target, ast.Name):
                    if self.current_context is None and self.current_class is None:
                        # This is a top-level assignment
                        self.module_symbol_table[target.id] = assigned_type
                    else:
                        # This is a local assignment
                        self.local_symbol_table[target.id] = assigned_type
        
        # Part 2: Collect variable data for the graph
        for target in node.targets:
            # The key change is here: check for both simple names AND 'self.attribute'
            if isinstance(target, ast.Name):
                var_name = target.id
            elif isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'self':
                var_name = f"self.{target.attr}"
            else:
                continue # Currently skips other types of assignments like tuple unpacking

            var_data = {
                "name": var_name,
                "line_number": node.lineno,
                "value": ast.unparse(node.value) if hasattr(ast, "unparse") else "",
                "context": self.current_context,
                "class_context": self.current_class,
                "is_dependency": self.is_dependency,
            }
            self.variables.append(var_data)
        
        # Now call generic_visit to ensure nested nodes (like calls) are processed
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        """Visit async function definitions"""
        self.visit_FunctionDef(node)

    def visit_AnnAssign(self, node):
        """Visit annotated assignments (type hints)"""
        if isinstance(node.target, ast.Name):
            var_data = {
                "name": node.target.id,
                "line_number": node.lineno,
                "value": (
                    ast.unparse(node.value)
                    if node.value and hasattr(ast, "unparse")
                    else ""
                ),
                "context": self.current_context,
                "class_context": self.current_class,
                "is_dependency": self.is_dependency,
            }
            self.variables.append(var_data)
        self.generic_visit(node)

    def visit_Import(self, node):
        """Visit import statements"""
        for name in node.names:
            import_data = {
                "name": name.name.split('.')[0], # Store the top-level package name
                "full_import_name": name.name, # Store the full import name
                "line_number": node.lineno,
                "alias": name.asname,
                "context": self.current_context,
                "is_dependency": self.is_dependency,
            }
            self.imports.append(import_data)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """
        Visit from-import statements, now correctly capturing the relative path.
        """
        # Create the relative path prefix (e.g., '.', '..') based on the level.
        prefix = '.' * node.level

        for alias in node.names:
            # If node.module is None, it's an import like `from . import name`
            # Determine the base module name for the 'name' property
            if node.module:
                # For 'from .module import name', base_module is 'module'
                # For 'from package.module import name', base_module is 'package'
                base_module = node.module.split('.')[0]
                full_import_name = f"{prefix}{node.module}.{alias.name}"
            else:
                # For 'from . import name', base_module is 'name'
                base_module = alias.name
                full_import_name = f"{prefix}{alias.name}"

            import_data = {
                "name": base_module,  # Store the top-level module name
                "full_import_name": full_import_name, # Store the full import path
                "line_number": node.lineno,
                "alias": alias.asname,
                "context": self.current_context,
                "is_dependency": self.is_dependency,
            }
            self.imports.append(import_data)

    def _resolve_attribute_base_type(self, node: ast.Attribute) -> Optional[str]:
        """
        Recursively traverses an attribute chain (e.g., self.manager.db)
        to find the type of the final attribute.
        """
        base_node = node.value
        current_type = None

        # Step 1: Find the type of the initial object in the chain
        if isinstance(base_node, ast.Name):
            obj_name = base_node.id
            if obj_name == 'self':
                current_type = self.current_class
            else:
                # Check local, then class, then module scopes
                current_type = (self.local_symbol_table.get(obj_name) or
                                self.class_symbol_table.get(obj_name) or
                                self.module_symbol_table.get(obj_name))
        
        elif isinstance(base_node, ast.Call):
            current_type = self._resolve_type_from_call(base_node) # You can keep your existing call resolver
        
        elif isinstance(base_node, ast.Attribute):
             # It's a nested attribute, recurse! e.g., self.a.b
            current_type = self._resolve_attribute_base_type(base_node)


        # Step 2: If we found the base type, now find the type of the final attribute
        if current_type:
            paths = self.imports_map.get(current_type, [])
            if paths:
                # This is a simplification; a better implementation would need to
                # parse the class file to find the type of the 'attr'
                # For now, I assume a direct method call on the found type
                return_type = self.get_return_type_from_ast(paths[0], current_type, node.attr)
                # If get_return_type_from_ast finds a return type, that's our new type.
                # If not, we can assume the attribute itself is of a certain type
                # This part is complex and may require parsing the class file for assignments.
                # For the current problem, just knowing the `current_type` is enough.
                # Let's modify the goal to return the type of the object *containing* the method.
                return current_type # Return the type of the object, e.g., 'JobManager'

        return None

    def visit_Call(self, node):
        """Visit function calls with enhanced detection"""
        call_name = None
        full_call_name = None

        try:
            full_call_name = ast.unparse(node.func)
            if isinstance(node.func, ast.Name):
                call_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                call_name = node.func.attr
            else:
                call_name = full_call_name
        except Exception:
            self.generic_visit(node)
            return
        
        try:
            call_args = [ast.unparse(arg) for arg in node.args]
        except Exception:
            call_args = []

        inferred_obj_type = None
        if isinstance(node.func, ast.Attribute):
            base_obj_node = node.func.value

            if isinstance(base_obj_node, ast.Name):
                obj_name = base_obj_node.id
                if obj_name == 'self':
                    # If the base is 'self', find the type of the attribute on the current class
                    inferred_obj_type = self.class_symbol_table.get(node.func.attr)
                    if not inferred_obj_type: # Fallback for method calls directly on self
                        inferred_obj_type = self.current_class
                else:
                    inferred_obj_type = (self.local_symbol_table.get(obj_name) or
                                        self.class_symbol_table.get(obj_name) or
                                        self.module_symbol_table.get(obj_name))
                    # If it's not a variable, it might be a direct call on a Class name.
                    if not inferred_obj_type and obj_name in self.imports_map:
                        inferred_obj_type = obj_name

            elif isinstance(base_obj_node, ast.Call):
                inferred_obj_type = self._resolve_type_from_call(base_obj_node)

            elif isinstance(base_obj_node, ast.Attribute): # e.g., self.job_manager
                # This handles nested attributes
                # The goal is to find the type of `self.job_manager`, which is 'JobManager'

                # Resolve the base of the chain, e.g., get 'self' from 'self.job_manager'
                base = base_obj_node
                while isinstance(base, ast.Attribute):
                    base = base.value

                if isinstance(base, ast.Name) and base.id == 'self':
                    # In self.X.Y... The attribute we care about is the first one, X
                    attr_name = base_obj_node.attr
                    inferred_obj_type = self.class_symbol_table.get(attr_name)

        elif isinstance(node.func, ast.Name):
            inferred_obj_type = (self.local_symbol_table.get(call_name) or
                                self.class_symbol_table.get(call_name) or
                                self.module_symbol_table.get(call_name))
    
        #   there are no CALLS relationships originating from P2pkhAddress.to_address in the graph. This is the root cause of the find_all_callees tool reporting 0
        #   results.

        #   The problem is not with the find_all_callees query itself, but with the GraphBuilder's ability to correctly identify and create CALLS relationships for methods like
        #   P2pkhAddress.to_address.

        #   Specifically, the GraphBuilder._create_function_calls method is likely not correctly processing calls made within methods of a class, especially when those calls are to:
        #    1. self.method(): Internal method calls.
        #    2. Functions imported from other modules (e.g., h_to_b, get_network).
        #    3. Functions from external libraries (e.g., hashlib.sha256, b58encode).

        #   The GraphBuilder.CodeVisitor.visit_Call method is responsible for identifying function calls. It needs to be improved to handle these cases.

        #   Plan:

        #    1. Enhance `CodeVisitor.visit_Call` in `src/codegraphcontext/tools/graph_builder.py`:
        #        * Internal Method Calls (`self.method()`): When node.func is an ast.Attribute and node.func.value.id is self, the call_name should be node.func.attr, and the resolved_path should
        #          be the file_path of the current class.
        #        * Imported Functions: The _create_function_calls method already has some logic for resolving imported functions using imports_map. I need to ensure this logic is robust and
        #          correctly applied within visit_Call to set inferred_obj_type or resolved_path accurately.
        #        * External Library Functions: For now, we might not be able to fully resolve calls to external library functions unless those libraries are also indexed. However, we should at
        #          least capture the full_call_name and call_name for these.
        # inferred_obj_type = None
        # if isinstance(node.func, ast.Attribute):
        #     base_obj_node = node.func.value
            
        #     if isinstance(base_obj_node, ast.Name):
        #         obj_name = base_obj_node.id
        #         if obj_name == 'self':
        #             # If the base is 'self', the call is to a method of the current class
        #             inferred_obj_type = self.current_class
        #         else:
        #             # Try to resolve the type of the object from symbol tables
        #             inferred_obj_type = (self.local_symbol_table.get(obj_name) or
        #                                  self.class_symbol_table.get(obj_name) or
        #                                  self.module_symbol_table.get(obj_name))
        #             # If not found in symbol tables, check if it's a class name from imports
        #             if not inferred_obj_type and obj_name in self.imports_map:
        #                 inferred_obj_type = obj_name

        #     elif isinstance(base_obj_node, ast.Call):
        #         inferred_obj_type = self._resolve_type_from_call(base_obj_node)
            
        #     elif isinstance(base_obj_node, ast.Attribute): # e.g., self.job_manager.method()
        #         # Recursively resolve the type of the base attribute
        #         inferred_obj_type = self._resolve_attribute_base_type(base_obj_node)
            
        # elif isinstance(node.func, ast.Name):
        #     # If it's a direct function call, try to infer its type from symbol tables or imports
        #     inferred_obj_type = (self.local_symbol_table.get(call_name) or
        #                          self.class_symbol_table.get(call_name) or
        #                          self.module_symbol_table.get(call_name))
        #     if not inferred_obj_type and call_name in self.imports_map:
        #         inferred_obj_type = call_name

        if call_name and call_name not in __builtins__:
            call_data = {
                "name": call_name,
                "full_name": full_call_name,
                "line_number": node.lineno,
                "args": call_args,
                "inferred_obj_type": inferred_obj_type,
                "context": self.current_context,
                "class_context": self.current_class,
                "is_dependency": self.is_dependency,
            }
            self.function_calls.append(call_data)
        
        self.generic_visit(node)  

class GraphBuilder:
    """Module for building and managing the Neo4j code graph."""

    def __init__(self, db_manager: DatabaseManager, job_manager: JobManager, loop: asyncio.AbstractEventLoop):
        self.db_manager = db_manager
        self.job_manager = job_manager
        self.loop = loop  # Store the main event loop
        self.driver = self.db_manager.get_driver()
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
                
                # Create a full-text search index for code search
                session.run("""
                    CREATE FULLTEXT INDEX code_search_index IF NOT EXISTS 
                    FOR (n:Function|Class|Variable) 
                    ON EACH [n.name, n.source, n.docstring]
                """)
                
                logger.info("Database schema verified/created successfully")
            except Exception as e:
                logger.warning(f"Schema creation warning: {e}")

    def _pre_scan_for_imports(self, files: list[Path]) -> dict:
        """Scans all files to create a map of class/function names to a LIST of their file paths."""
        imports_map = {}
        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read())
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                            if node.name not in imports_map:
                                imports_map[node.name] = []
                            imports_map[node.name].append(str(file_path.resolve()))
            except Exception as e:
                logger.warning(f"Pre-scan failed for {file_path}: {e}")
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

            # Create/Merge the file node
            session.run("""
                MERGE (f:File {path: $path})
                SET f.name = $name, f.relative_path = $relative_path, f.is_dependency = $is_dependency
            """, path=file_path_str, name=file_name, relative_path=relative_path, is_dependency=is_dependency)

            # Create directory structure and link it
            file_path_obj = Path(file_path_str)
            repo_path_obj = Path(repo_result['path'])
            
            relative_path_to_file = file_path_obj.relative_to(repo_path_obj)
            
            parent_path = str(repo_path_obj)
            parent_label = 'Repository'

            # Create nodes for each directory part of the path
            for part in relative_path_to_file.parts[:-1]: # For each directory in the path
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

            # Link the last directory/repository to the file
            session.run(f"""
                MATCH (p:{parent_label} {{path: $parent_path}})
                MATCH (f:File {{path: $file_path}})
                MERGE (p)-[:CONTAINS]->(f)
            """, parent_path=parent_path, file_path=file_path_str)

            for item_data, label in [(file_data['functions'], 'Function'), (file_data['classes'], 'Class'), (file_data['variables'], 'Variable')]:
                for item in item_data:
                    query = f"""
                        MATCH (f:File {{path: $file_path}})
                        MERGE (n:{label} {{name: $name, file_path: $file_path, line_number: $line_number}})
                        SET n += $props
                        MERGE (f)-[:CONTAINS]->(n)
                    """
                    session.run(query, file_path=file_path_str, name=item['name'], line_number=item['line_number'], props=item)
                    
                    # If it's a function, create parameter nodes and relationships and calculate complexity
                    if label == 'Function':
                        # Calculate cyclomatic complexity
                        try:
                            func_tree = ast.parse(item['source_code'])
                            complexity_visitor = CyclomaticComplexityVisitor()
                            complexity_visitor.visit(func_tree)
                            item['cyclomatic_complexity'] = complexity_visitor.complexity
                        except Exception as e:
                            logger.warning(f"Could not calculate cyclomatic complexity for {item['name']} in {file_path_str}: {e}")
                            item['cyclomatic_complexity'] = 1 # Default to 1 on error

                        for arg_name in item.get('args', []):
                            session.run("""
                                MATCH (fn:Function {name: $func_name, file_path: $file_path, line_number: $line_number})
                                MERGE (p:Parameter {name: $arg_name, file_path: $file_path, function_line_number: $line_number})
                                MERGE (fn)-[:HAS_PARAMETER]->(p)
                            """, func_name=item['name'], file_path=file_path_str, line_number=item['line_number'], arg_name=arg_name)

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

            for class_item in file_data.get('classes', []):
                if class_item.get('bases'):
                    for base_class_name in class_item['bases']:
                        resolved_parent_file_path = self._resolve_class_path(
                            base_class_name,
                            file_path_str,
                            file_data['imports'],
                            imports_map
                        )
                        if resolved_parent_file_path:
                            session.run("""
                                MATCH (child:Class {name: $child_name, file_path: $file_path})
                                MATCH (parent:Class {name: $parent_name, file_path: $resolved_parent_file_path})
                                MERGE (child)-[:INHERITS_FROM]->(parent)
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

        for var in file_data.get('variables', []):
            context = var.get('context')
            class_context = var.get('class_context')
            parent_line = var.get('parent_line')
            
            if class_context:
                session.run("""
                    MATCH (c:Class {name: $class_name, file_path: $file_path})
                    MATCH (v:Variable {name: $var_name, file_path: $file_path, line_number: $var_line})
                    MERGE (c)-[:CONTAINS]->(v)
                """,
                class_name=class_context,
                file_path=file_path,
                var_name=var['name'],
                var_line=var['line_number'])
            elif context and parent_line:
                parent_label = "Function"
                parent_node_data = None
                
                for class_data in file_data.get('classes', []):
                    if class_data['name'] == context and class_data['line_number'] == parent_line:
                        parent_label = "Class"
                        parent_node_data = class_data
                        break
                
                if not parent_node_data:
                    for func_data in file_data.get('functions', []):
                        if func_data['name'] == context and func_data['line_number'] == parent_line:
                            parent_label = "Function"
                            parent_node_data = func_data
                            break
                
                if parent_node_data:
                    session.run(f"""
                        MATCH (p:{parent_label} {{name: $parent_name, file_path: $file_path, line_number: $parent_line}})
                        MATCH (v:Variable {{name: $var_name, file_path: $file_path, line_number: $var_line}})
                        MERGE (p)-[:CONTAINS]->(v)
                    """,
                    parent_name=context,
                    file_path=file_path,
                    parent_line=parent_line,
                    var_name=var['name'],
                    var_line=var['line_number'])
            else:
                session.run("""
                    MATCH (f:File {path: $file_path})
                    MATCH (v:Variable {name: $var_name, file_path: $file_path, line_number: $var_line})
                    MERGE (f)-[:CONTAINS]->(v)
                """,
                file_path=file_path,
                var_name=var['name'],
                var_line=var['line_number'])
    
    def _create_function_calls(self, session, file_data: Dict, imports_map: dict):
        """
        Create CALLS relationships with a unified, prioritized logic flow for all call types.
        """
        caller_file_path = str(Path(file_data['file_path']).resolve())
        local_function_names = {func['name'] for func in file_data.get('functions', [])}
        local_imports = {imp['alias'] or imp['name'].split('.')[-1]: imp['name'] 
                        for imp in file_data.get('imports', [])}
        
        for call in file_data.get('function_calls', []):
            called_name = call['name']
            if called_name in __builtins__: continue

            resolved_path = None
            
            # Priority 1: Handle method calls (var.method(), self.attr.method(), etc.)
            # This is the most specific and reliable information we have.
            if call.get('inferred_obj_type'):
                obj_type = call['inferred_obj_type']
                possible_paths = imports_map.get(obj_type, [])
                if len(possible_paths) > 0:
                    # Simplistic choice for now; assumes the first found definition is correct.
                    resolved_path = possible_paths[0]
            
            # Priority 2: Handle direct calls (func()) and class methods (Class.method())
            else:
                # For class methods, the `called_name` will be the class itself
                lookup_name = call['full_name'].split('.')[0] if '.' in call['full_name'] else called_name
                possible_paths = imports_map.get(lookup_name, [])

                # A) Is it a local function?
                if lookup_name in local_function_names:
                    resolved_path = caller_file_path
                # B) Is it an unambiguous global function/class?
                elif len(possible_paths) == 1:
                    resolved_path = possible_paths[0]
                # C) Is it an ambiguous call we can resolve via this file's imports?
                elif len(possible_paths) > 1 and lookup_name in local_imports:
                    full_import_name = local_imports[lookup_name]
                    for path in possible_paths:
                        if full_import_name.replace('.', '/') in path:
                            resolved_path = path
                            break
            
            # Fallback if no path could be resolved by any of the above rules
            if not resolved_path:
                # If the called name is in the imports map, use its path
                if called_name in imports_map and imports_map[called_name]:
                    resolved_path = imports_map[called_name][0] # Take the first path for now
                else:
                    resolved_path = caller_file_path

            caller_context = call.get('context')
            inferred_type = call.get('inferred_obj_type')
            if debug_mode:
                log_inferred_str = f" (via inferred type {inferred_type})" if inferred_type else ""
                debug_log(f"Resolved call: {caller_context} @ {caller_file_path} calls {called_name} @ {resolved_path}{log_inferred_str}")
            if caller_context:
                session.run("""
                    MATCH (caller:Function {name: $caller_name, file_path: $caller_file_path})
                    MATCH (called:Function {name: $called_name, file_path: $called_file_path})
                    MERGE (caller)-[:CALLS {line_number: $line_number, args: $args, full_call_name: $full_call_name}]->(called)
                """,
                caller_name=caller_context,
                caller_file_path=caller_file_path,
                called_name=called_name,
                called_file_path=resolved_path,
                line_number=call['line_number'],
                args=call.get('args', []),
                full_call_name=call.get('full_name', called_name))
            else:
                # Handle calls from the top-level of a file
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
                
    def _resolve_class_path(self, class_name: str, current_file_path: str, current_file_imports: list, global_imports_map: dict) -> Optional[str]:
        debug_log(f"_resolve_class_path: Resolving '{class_name}' from '{current_file_path}'")
        """
        Resolves the file path of a class based on import resolution priority.
        1. Same file definition
        2. Imports within the current file (direct or aliased)
        3. Global imports map (anywhere in the indexed project)
        """
        # Priority 1: Same file definition
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Class {name: $class_name, file_path: $current_file_path})
                RETURN c.file_path AS file_path
            """, class_name=class_name, current_file_path=current_file_path).single()
            if result:
                debug_log(f"_resolve_class_path: Priority 1 match: {result['file_path']}")
                return result['file_path']

        # Priority 2: Imports within the current file
        with self.driver.session() as session:
            result = session.run("""
                MATCH (f:File {path: $current_file_path})-[:IMPORTS]->(m:Module)
                OPTIONAL MATCH (m)-[:CONTAINS]->(c:Class {name: $class_name})
                RETURN c.file_path AS file_path
            """, current_file_path=current_file_path, class_name=class_name).single()
            if result and result["file_path"]:
                debug_log(f"_resolve_class_path: Priority 2 match: {result['file_path']}")
                return result['file_path']

        # Priority 3: Global imports map (anywhere in the indexed project) - Fallback
        if class_name in global_imports_map:
            debug_log(f"_resolve_class_path: Priority 3 match: {global_imports_map[class_name][0]}")
            return global_imports_map[class_name][0]

        debug_log(f"_resolve_class_path: No path resolved for '{class_name}'")
        return None
                
    def delete_file_from_graph(self, file_path: str):
        """Deletes a file and all its contained elements and relationships."""
        file_path_str = str(Path(file_path).resolve())
        with self.driver.session() as session:
            # Get parent directories
            parents_res = session.run("""
                MATCH (f:File {path: $path})<-[:CONTAINS*]-(d:Directory)
                RETURN d.path as path ORDER BY d.path DESC
            """, path=file_path_str)
            parent_paths = [record["path"] for record in parents_res]

            # Delete the file and its contents
            session.run(
                """
                MATCH (f:File {path: $path})
                OPTIONAL MATCH (f)-[:CONTAINS]->(element)
                DETACH DELETE f, element
                """,
                path=file_path_str,
            )
            logger.info(f"Deleted file and its elements from graph: {file_path_str}")

            # Clean up empty parent directories, starting from the deepest
            for path in parent_paths:
                session.run("""
                    MATCH (d:Directory {path: $path})
                    WHERE NOT (d)-[:CONTAINS]->()
                    DETACH DELETE d
                """, path=path)

    def delete_repository_from_graph(self, repo_path: str):
        """
        Deletes a repository and all its contents from the graph, then cleans up
        any orphaned Module nodes that are no longer referenced.
        """
        repo_path_str = str(Path(repo_path).resolve())
        with self.driver.session() as session:
            # Delete the repository and all its contained elements, including parameters
            session.run("""
                MATCH (r:Repository {path: $path})
                OPTIONAL MATCH (r)-[:CONTAINS*]->(e)
                OPTIONAL MATCH (e)-[:HAS_PARAMETER]->(p)
                DETACH DELETE r, e, p
            """, path=repo_path_str)
            logger.info(f"Deleted repository and its contents from graph: {repo_path_str}")

            # Clean up orphaned Module nodes that are no longer imported by any file
            session.run("""
                MATCH (m:Module)
                WHERE NOT ()-[:IMPORTS]->(m)
                DETACH DELETE m
            """)
            logger.info("Cleaned up orphaned Module nodes.")

    def update_file_in_graph(self, file_path: Path, repo_path: Path, imports_map: dict):
        """
        Updates a single file's nodes in the graph and returns its new parsed data.
        This function does NOT handle re-linking the call graph.
        """
        file_path_str = str(file_path.resolve())
        repo_name = repo_path.name
        
        # --- STEP 1: Delete the old file from the graph ---
        debug_log(f"[update_file_in_graph] Deleting old file data for: {file_path_str}")
        try:
            self.delete_file_from_graph(file_path_str)
            debug_log(f"[update_file_in_graph] Old file data deleted for: {file_path_str}")
        except Exception as e:
            logger.error(f"Error deleting old file data for {file_path_str}: {e}")
            return None # Return None on failure

        # --- STEP 2: Re-parse and re-add the new file ---
        if file_path.exists():
            debug_log(f"[update_file_in_graph] Parsing new file data for: {file_path_str}")
            # Pass imports_map to the parser
            file_data = self.parse_python_file(repo_path, file_path, imports_map)
            
            if "error" not in file_data:
                debug_log(f"[update_file_in_graph] Adding new file data to graph for: {file_path_str}")
                self.add_file_to_graph(file_data, repo_name, imports_map)
                debug_log(f"[update_file_in_graph] New file data added for: {file_path_str}")
                # --- CRITICAL: Return the new data ---
                return file_data
            else:
                logger.error(f"Skipping graph add for {file_path_str} due to parsing error: {file_data['error']}")
                return None # Return None on failure
        else:
            debug_log(f"[update_file_in_graph] File no longer exists: {file_path_str}")
            # Return a special marker for deleted files
            return {"deleted": True, "path": file_path_str}

    def parse_python_file(self, repo_path: Path, file_path: Path, imports_map: dict, is_dependency: bool = False) -> Dict:
        """Parse a Python file and extract code elements"""
        debug_log(f"[parse_python_file] Starting parsing for: {file_path}")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source_code = f.read()
            tree = ast.parse(source_code)
            visitor = CodeVisitor(str(file_path), imports_map, is_dependency)
            visitor.visit(tree)
            if debug_mode:
                debug_log(f"[parse_python_file] Successfully parsed: {file_path}")
            return {
                "repo_path": str(repo_path),
                "file_path": str(file_path),
                "functions": visitor.functions,
                "classes": visitor.classes,
                "variables": visitor.variables,
                "imports": visitor.imports,
                "function_calls": visitor.function_calls,
                "is_dependency": is_dependency,
            }
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            debug_log(f"[parse_python_file] Error parsing {file_path}: {e}")
            return {"file_path": str(file_path), "error": str(e)}

    def estimate_processing_time(self, path: Path) -> Optional[Tuple[int, float]]:
        """Estimate processing time and file count"""
        try:
            if path.is_file():
                files = [path]
            else:
                files = list(path.rglob("*.py"))
            
            total_files = len(files)
            # Simple heuristic: 0.1 seconds per file
            estimated_time = total_files * 0.1
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

            all_function_calls_data = [] # Initialize list to collect all function call data

            processed_count = 0
            for file in files:
                if file.is_file():
                    if job_id:
                        self.job_manager.update_job(job_id, current_file=str(file))
                    repo_path = path.resolve() if path.is_dir() else file.parent.resolve()
                    file_data = self.parse_python_file(repo_path, file, imports_map, is_dependency)
                    if "error" not in file_data:
                        self.add_file_to_graph(file_data, repo_name, imports_map)
                        all_function_calls_data.append(file_data) # Collect for later processing
                    processed_count += 1
                    if job_id:
                        self.job_manager.update_job(job_id, processed_files=processed_count)
                    await asyncio.sleep(0.01)

            # After all files are processed, create function call relationships
            self._create_all_function_calls(all_function_calls_data, imports_map)
            if debug_mode:
                with open("all_function_calls_data.json", "w") as f:
                    import json
                    json.dump(all_function_calls_data, f, indent=4)
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

            # Create the coroutine for the background task
            coro = self.build_graph_from_path_async(path_obj, is_dependency, job_id)
            
            # Safely schedule the coroutine to run on the main event loop from this thread
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