from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Set
import logging
import re

logger = logging.getLogger(__name__)

JAVA_QUERIES = {
    "functions": """
        (method_declaration
            name: (identifier) @name
            parameters: (formal_parameters) @params
        ) @function_node
        
        (constructor_declaration
            name: (identifier) @name
            parameters: (formal_parameters) @params
        ) @function_node
    """,
    "classes": """
        [
            (class_declaration name: (identifier) @name)
            (interface_declaration name: (identifier) @name)
            (enum_declaration name: (identifier) @name)
            (annotation_type_declaration name: (identifier) @name)
        ] @class
    """,
    "imports": """
        (import_declaration) @import
    """,
    "calls": """
        (method_invocation
            name: (identifier) @name
        ) @method_call
        
        (object_creation_expression
            type: (type_identifier) @name
        ) @constructor_call
    """,
    "inheritance": """
        (class_declaration
            name: (identifier) @class_name
            superclass: (superclass) @superclass_node
        )
    """,
    "implements": """
        (class_declaration
            name: (identifier) @class_name
            interfaces: (super_interfaces) @interfaces_node
        )
    """,
}

class JavaTreeSitterParser:
    def __init__(self, generic_parser_wrapper: Any):
        self.generic_parser_wrapper = generic_parser_wrapper
        self.language_name = "java"
        self.language = generic_parser_wrapper.language
        self.parser = generic_parser_wrapper.parser

        self.queries = {
            name: self.language.query(query_str)
            for name, query_str in JAVA_QUERIES.items()
        }
        
        # Track context for better call resolution
        self.current_class = None
        self.current_function = None

    def parse(self, file_path: Path, is_dependency: bool = False) -> Dict[str, Any]:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                source_code = f.read()

            if not source_code.strip():
                logger.warning(f"Empty or whitespace-only file: {file_path}")
                return self._empty_result(file_path, is_dependency)

            tree = self.parser.parse(bytes(source_code, "utf8"))

            parsed_functions = []
            parsed_classes = []
            parsed_imports = []
            parsed_calls = []
            parsed_inheritance = []
            parsed_implementations = []

            for capture_name, query in self.queries.items():
                captures = query.captures(tree.root_node)

                if capture_name == "functions":
                    parsed_functions = self._parse_functions(captures, source_code, file_path)
                elif capture_name == "classes":
                    parsed_classes = self._parse_classes(captures, source_code, file_path)
                elif capture_name == "imports":
                    parsed_imports = self._parse_imports(captures, source_code)
                elif capture_name == "calls":
                    parsed_calls = self._parse_calls(captures, source_code, tree.root_node)
                elif capture_name == "inheritance":
                    parsed_inheritance = self._parse_inheritance(captures, source_code)
                elif capture_name == "implements":
                    parsed_implementations = self._parse_implementations(captures, source_code)

            # Post-process to add context to function calls
            parsed_calls = self._enrich_calls_with_context(
                parsed_calls, parsed_functions, parsed_classes
            )

            logger.info(f"Parsed {file_path}: {len(parsed_classes)} classes, "
                       f"{len(parsed_functions)} functions, {len(parsed_calls)} calls, "
                       f"{len(parsed_inheritance)} inheritance, {len(parsed_implementations)} implementations")

            return {
                "file_path": str(file_path),
                "functions": parsed_functions,
                "classes": parsed_classes,
                "variables": [],
                "imports": parsed_imports,
                "function_calls": parsed_calls,
                "inheritance": parsed_inheritance,
                "implementations": parsed_implementations,
                "is_dependency": is_dependency,
                "lang": self.language_name,
            }

        except Exception as e:
            logger.error(f"Error parsing Java file {file_path}: {e}", exc_info=True)
            return self._empty_result(file_path, is_dependency)

    def _empty_result(self, file_path: Path, is_dependency: bool) -> Dict[str, Any]:
        return {
            "file_path": str(file_path),
            "functions": [],
            "classes": [],
            "variables": [],
            "imports": [],
            "function_calls": [],
            "inheritance": [],
            "implementations": [],
            "is_dependency": is_dependency,
            "lang": self.language_name,
        }

    def _parse_functions(self, captures: list, source_code: str, file_path: Path) -> list[Dict[str, Any]]:
        functions = []
        source_lines = source_code.splitlines()
        seen_functions = set()

        for node, capture_name in captures:
            if capture_name == "function_node":
                try:
                    start_line = node.start_point[0] + 1
                    end_line = node.end_point[0] + 1
                    
                    # Find the function name
                    name_captures = [
                        (n, cn) for n, cn in captures 
                        if cn == "name" and n.parent == node
                    ]
                    
                    if not name_captures:
                        continue
                    
                    name_node = name_captures[0][0]
                    func_name = source_code[name_node.start_byte:name_node.end_byte]
                    
                    # Find containing class
                    class_context = self._find_containing_class(node, source_code)
                    
                    # Create unique identifier
                    func_id = f"{class_context}.{func_name}" if class_context else func_name
                    func_key = f"{func_id}:{start_line}"
                    
                    if func_key in seen_functions:
                        continue
                    seen_functions.add(func_key)
                    
                    # Extract parameters
                    params_captures = [
                        (n, cn) for n, cn in captures 
                        if cn == "params" and n.parent == node
                    ]
                    
                    parameters = []
                    if params_captures:
                        params_node = params_captures[0][0]
                        params_text = source_code[params_node.start_byte:params_node.end_byte]
                        parameters = self._extract_parameter_names(params_text)
                    
                    source_text = source_code[node.start_byte:node.end_byte]
                    
                    # Determine if this is a constructor
                    is_constructor = node.type == "constructor_declaration"
                    
                    functions.append({
                        "name": func_name,
                        "full_name": func_id,
                        "parameters": parameters,
                        "line_number": start_line,
                        "end_line": end_line,
                        "source": source_text,
                        "file_path": str(file_path),
                        "class_context": class_context,
                        "is_constructor": is_constructor,
                        "lang": self.language_name,
                    })
                    
                except Exception as e:
                    logger.error(f"Error parsing function in {file_path}: {e}")
                    continue

        return functions

    def _parse_classes(self, captures: list, source_code: str, file_path: Path) -> list[Dict[str, Any]]:
        classes = []
        seen_classes = set()

        for node, capture_name in captures:
            if capture_name == "class":
                try:
                    start_line = node.start_point[0] + 1
                    end_line = node.end_point[0] + 1
                    
                    # Find class name
                    name_captures = [
                        (n, cn) for n, cn in captures 
                        if cn == "name" and n.parent == node
                    ]
                    
                    if not name_captures:
                        continue
                    
                    name_node = name_captures[0][0]
                    class_name = source_code[name_node.start_byte:name_node.end_byte]
                    
                    # Find containing class (for inner classes)
                    parent_class = self._find_containing_class(node.parent, source_code)
                    
                    # Create full class name
                    full_name = f"{parent_class}.{class_name}" if parent_class else class_name
                    
                    class_key = f"{full_name}:{start_line}"
                    if class_key in seen_classes:
                        continue
                    seen_classes.add(class_key)
                    
                    source_text = source_code[node.start_byte:node.end_byte]
                    
                    # Determine class type
                    class_type = node.type.replace("_declaration", "")
                    
                    classes.append({
                        "name": class_name,
                        "full_name": full_name,
                        "line_number": start_line,
                        "end_line": end_line,
                        "source": source_text,
                        "file_path": str(file_path),
                        "parent_class": parent_class,
                        "class_type": class_type,
                        "lang": self.language_name,
                    })
                    
                except Exception as e:
                    logger.error(f"Error parsing class in {file_path}: {e}")
                    continue

        return classes

    def _parse_imports(self, captures: list, source_code: str) -> list[dict]:
        imports = []
        seen_imports = set()
        
        for node, capture_name in captures:
            if capture_name == "import":
                try:
                    import_text = source_code[node.start_byte:node.end_byte]
                    
                    # Parse static imports
                    static_match = re.search(r'import\s+static\s+([^;]+)', import_text)
                    regular_match = re.search(r'import\s+(?!static)([^;]+)', import_text)
                    
                    if static_match:
                        import_path = static_match.group(1).strip()
                        is_static = True
                    elif regular_match:
                        import_path = regular_match.group(1).strip()
                        is_static = False
                    else:
                        continue
                    
                    if import_path in seen_imports:
                        continue
                    seen_imports.add(import_path)
                    
                    # Extract simple name for easier matching
                    simple_name = import_path.split('.')[-1].rstrip('*')
                    
                    import_data = {
                        "name": simple_name,
                        "full_import_name": import_path,
                        "line_number": node.start_point[0] + 1,
                        "alias": None,
                        "is_static": is_static,
                        "is_wildcard": import_path.endswith('*'),
                        "context": (None, None),
                        "lang": self.language_name,
                        "is_dependency": False,
                    }
                    imports.append(import_data)
                    
                except Exception as e:
                    logger.error(f"Error parsing import: {e}")
                    continue

        return imports

    def _parse_calls(self, captures: list, source_code: str, root_node) -> list[dict]:
        calls = []
        seen_calls = set()
        
        for node, capture_name in captures:
            if capture_name == "name":
                try:
                    call_name = source_code[node.start_byte:node.end_byte]
                    line_number = node.start_point[0] + 1
                    
                    # Find containing function and class
                    func_context = self._find_containing_function(node, source_code)
                    class_context = self._find_containing_class(node, source_code)
                    
                    # Create unique key
                    call_key = f"{class_context}.{func_context}:{call_name}:{line_number}"
                    if call_key in seen_calls:
                        continue
                    seen_calls.add(call_key)
                    
                    # Determine if this is a method call or constructor
                    is_constructor = any(
                        (n, cn) for n, cn in captures 
                        if cn == "constructor_call" and n == node.parent
                    )
                    
                    call_data = {
                        "name": call_name,
                        "full_name": call_name,
                        "line_number": line_number,
                        "args": [],
                        "inferred_obj_type": None,
                        "context": (func_context, class_context),
                        "class_context": (class_context, None),
                        "is_constructor_call": is_constructor,
                        "lang": self.language_name,
                        "is_dependency": False,
                    }
                    calls.append(call_data)
                    
                except Exception as e:
                    logger.error(f"Error parsing call: {e}")
                    continue

        return calls

    def _parse_inheritance(self, captures: list, source_code: str) -> list[dict]:
        """Parse class inheritance (extends) relationships."""
        inheritance = []
        seen = set()
        
        # Group captures by class node
        class_info = {}
        
        for node, capture_name in captures:
            if capture_name == "class_name":
                parent = node.parent
                while parent and parent.type != "class_declaration":
                    parent = parent.parent
                
                if parent and parent not in class_info:
                    class_name = source_code[node.start_byte:node.end_byte]
                    class_info[parent] = {
                        "class": class_name,
                        "superclass": None,
                        "line": node.start_point[0] + 1
                    }
            
            elif capture_name == "superclass_node":
                parent = node.parent
                while parent and parent.type != "class_declaration":
                    parent = parent.parent
                
                if parent and parent in class_info:
                    # Extract superclass name from the superclass node
                    superclass_text = source_code[node.start_byte:node.end_byte]
                    # Remove "extends" keyword if present
                    superclass_name = re.search(r'(\w+)', superclass_text)
                    if superclass_name:
                        class_info[parent]["superclass"] = superclass_name.group(1)

        # Create inheritance records
        for class_node, data in class_info.items():
            if data["superclass"]:
                key = f"{data['class']}->{data['superclass']}"
                if key not in seen:
                    seen.add(key)
                    inheritance.append({
                        "child_class": data["class"],
                        "parent_class": data["superclass"],
                        "line_number": data["line"],
                        "lang": self.language_name,
                    })
                    logger.debug(f"Found inheritance: {data['class']} extends {data['superclass']}")

        return inheritance

    def _parse_implementations(self, captures: list, source_code: str) -> list[dict]:
        """Parse interface implementation (implements) relationships."""
        implementations = []
        seen = set()
        
        # Group captures by class node
        class_info = {}
        
        for node, capture_name in captures:
            if capture_name == "class_name":
                parent = node.parent
                while parent and parent.type != "class_declaration":
                    parent = parent.parent
                
                if parent and parent not in class_info:
                    class_name = source_code[node.start_byte:node.end_byte]
                    class_info[parent] = {
                        "class": class_name,
                        "interfaces": [],
                        "line": node.start_point[0] + 1
                    }
            
            elif capture_name == "interfaces_node":
                parent = node.parent
                while parent and parent.type != "class_declaration":
                    parent = parent.parent
                
                if parent and parent in class_info:
                    # Extract all interface names
                    interfaces_text = source_code[node.start_byte:node.end_byte]
                    # Find all identifiers (interface names)
                    interface_names = re.findall(r'\b([A-Z]\w+)\b', interfaces_text)
                    class_info[parent]["interfaces"].extend(interface_names)

        # Create implementation records
        for class_node, data in class_info.items():
            for interface_name in data["interfaces"]:
                key = f"{data['class']}->{interface_name}"
                if key not in seen:
                    seen.add(key)
                    implementations.append({
                        "class_name": data["class"],
                        "interface_name": interface_name,
                        "line_number": data["line"],
                        "lang": self.language_name,
                    })
                    logger.debug(f"Found implementation: {data['class']} implements {interface_name}")

        return implementations

    def _find_containing_class(self, node, source_code: str) -> Optional[str]:
        """Find the name of the class containing this node."""
        current = node
        while current:
            if current.type in ["class_declaration", "interface_declaration", "enum_declaration"]:
                for child in current.children:
                    if child.type == "identifier":
                        return source_code[child.start_byte:child.end_byte]
            current = current.parent
        return None

    def _find_containing_function(self, node, source_code: str) -> Optional[str]:
        """Find the name of the function/method containing this node."""
        current = node
        while current:
            if current.type in ["method_declaration", "constructor_declaration"]:
                for child in current.children:
                    if child.type == "identifier":
                        return source_code[child.start_byte:child.end_byte]
            current = current.parent
        return None

    def _enrich_calls_with_context(self, calls: list, functions: list, classes: list) -> list:
        """Add additional context to function calls based on parsed functions and classes."""
        # Build lookup maps
        class_map = {cls["name"]: cls for cls in classes}
        func_map = {}
        for func in functions:
            key = f"{func.get('class_context', '')}.{func['name']}"
            func_map[key] = func
        
        # Enrich each call
        for call in calls:
            func_context, class_context = call.get("context", (None, None))
            
            # Try to resolve the called function
            if class_context and call["name"]:
                full_key = f"{class_context}.{call['name']}"
                if full_key in func_map:
                    call["resolved_function"] = full_key
                    call["full_name"] = full_key
        
        return calls

    def _extract_parameter_names(self, params_text: str) -> list[str]:
        """Extract parameter names from parameter list."""
        params = []
        if not params_text or params_text.strip() == "()":
            return params
            
        params_content = params_text.strip("()")
        if not params_content:
            return params
        
        # Split by comma, but be careful with generic types
        depth = 0
        current_param = []
        
        for char in params_content:
            if char in '<[(':
                depth += 1
                current_param.append(char)
            elif char in '>])':
                depth -= 1
                current_param.append(char)
            elif char == ',' and depth == 0:
                param_str = ''.join(current_param).strip()
                if param_str:
                    param_name = self._extract_param_name(param_str)
                    if param_name:
                        params.append(param_name)
                current_param = []
            else:
                current_param.append(char)
        
        # Don't forget the last parameter
        param_str = ''.join(current_param).strip()
        if param_str:
            param_name = self._extract_param_name(param_str)
            if param_name:
                params.append(param_name)
                    
        return params

    def _extract_param_name(self, param_str: str) -> Optional[str]:
        """Extract the parameter name from a parameter declaration."""
        # Remove annotations
        param_str = re.sub(r'@\w+(?:\([^)]*\))?\s*', '', param_str)
        
        # Split by whitespace
        parts = param_str.split()
        if len(parts) >= 2:
            # Last part is typically the parameter name
            # Handle array declarations like "String[] args"
            param_name = parts[-1].split('[')[0]
            return param_name
        
        return None


def pre_scan_java(files: list[Path], parser_wrapper) -> dict:
    """Pre-scan Java files to build a name-to-files mapping."""
    name_to_files = {}
    
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Match classes with various modifiers
            class_matches = re.finditer(
                r'\b(?:public\s+|private\s+|protected\s+)?'
                r'(?:static\s+)?(?:abstract\s+)?(?:final\s+)?'
                r'class\s+(\w+)',
                content
            )
            for match in class_matches:
                class_name = match.group(1)
                if class_name not in name_to_files:
                    name_to_files[class_name] = []
                name_to_files[class_name].append(str(file_path))
            
            # Match interfaces
            interface_matches = re.finditer(
                r'\b(?:public\s+|private\s+|protected\s+)?'
                r'interface\s+(\w+)',
                content
            )
            for match in interface_matches:
                interface_name = match.group(1)
                if interface_name not in name_to_files:
                    name_to_files[interface_name] = []
                name_to_files[interface_name].append(str(file_path))
            
            # Match enums
            enum_matches = re.finditer(
                r'\b(?:public\s+|private\s+|protected\s+)?'
                r'enum\s+(\w+)',
                content
            )
            for match in enum_matches:
                enum_name = match.group(1)
                if enum_name not in name_to_files:
                    name_to_files[enum_name] = []
                name_to_files[enum_name].append(str(file_path))
                
        except Exception as e:
            logger.error(f"Error pre-scanning Java file {file_path}: {e}")
    
    logger.info(f"Pre-scanned {len(files)} Java files, found {len(name_to_files)} types")
    return name_to_files