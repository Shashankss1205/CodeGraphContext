from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import re
from codegraphcontext.utils.debug_log import debug_log, info_logger, error_logger, warning_logger
from codegraphcontext.utils.tree_sitter_manager import execute_query

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
        )
        
        (object_creation_expression
            type: (type_identifier) @name
        )
    """,
}

class JavaTreeSitterParser:
    def __init__(self, generic_parser_wrapper: Any):
        self.generic_parser_wrapper = generic_parser_wrapper
        self.language_name = "java"
        self.language = generic_parser_wrapper.language
        self.parser = generic_parser_wrapper.parser

    def parse(self, file_path: Path, is_dependency: bool = False) -> Dict[str, Any]:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                source_code = f.read()

            if not source_code.strip():
                warning_logger(f"Empty or whitespace-only file: {file_path}")
                return {
                    "file_path": str(file_path),
                    "functions": [],
                    "classes": [],
                    "variables": [],
                    "imports": [],
                    "function_calls": [],
                    "is_dependency": is_dependency,
                    "lang": self.language_name,
                }

            tree = self.parser.parse(bytes(source_code, "utf8"))

            parsed_functions = []
            parsed_classes = []
            parsed_imports = []
            parsed_calls = []

            for capture_name, query in self.queries.items():
                captures = execute_query(self.language, query_str, tree.root_node)

                if capture_name == "functions":
                    parsed_functions = self._parse_functions(captures, source_code, file_path)
                elif capture_name == "classes":
                    parsed_classes = self._parse_classes(captures, source_code, file_path)
                elif capture_name == "imports":
                    parsed_imports = self._parse_imports(captures, source_code)
                elif capture_name == "calls":
                    parsed_calls = self._parse_calls(captures, source_code)

            return {
                "file_path": str(file_path),
                "functions": parsed_functions,
                "classes": parsed_classes,
                "variables": [],
                "imports": parsed_imports,
                "function_calls": parsed_calls,
                "is_dependency": is_dependency,
                "lang": self.language_name,
            }

        except Exception as e:
            error_logger(f"Error parsing Java file {file_path}: {e}")
            return {
                "file_path": str(file_path),
                "functions": [],
                "classes": [],
                "variables": [],
                "imports": [],
                "function_calls": [],
                "is_dependency": is_dependency,
                "lang": self.language_name,
            }

    def _parse_functions(self, captures: list, source_code: str, file_path: Path) -> list[Dict[str, Any]]:
        functions = []
        source_lines = source_code.splitlines()

        for node, capture_name in captures:
            if capture_name == "function_node":
                try:
                    start_line = node.start_point[0] + 1
                    end_line = node.end_point[0] + 1
                    
                    name_captures = [
                        (n, cn) for n, cn in captures 
                        if cn == "name" and n.parent == node
                    ]
                    
                    if name_captures:
                        name_node = name_captures[0][0]
                        func_name = source_code[name_node.start_byte:name_node.end_byte]
                        
                        params_captures = [
                            (n, cn) for n, cn in captures 
                            if cn == "params" and n.parent == node
                        ]
                        
                        parameters = []
                        if params_captures:
                            params_node = params_captures[0][0]
                            params_text = source_code[params_node.start_byte:params_node.end_byte]
                            parameters = self._extract_parameter_names(params_text)
                        # Extract annotations applied to this function
                        annotations = []
                        for n, cn in captures:
                         if cn == "annotation" and n.parent == node:
                            ann_name_node = n.child_by_field_name("name")
                            if ann_name_node:
                                ann_name = source_code[ann_name_node.start_byte:ann_name_node.end_byte]
                                annotations.append(ann_name)

                        source_text = source_code[node.start_byte:node.end_byte]
                        
                        functions.append({
                            "name": func_name,
                            "parameters": parameters,
                            "annotations":annotations,
                            "line_number": start_line,
                            "end_line": end_line,
                            "source": source_text,
                            "file_path": str(file_path),
                            "lang": self.language_name,
                        })
                        
                except Exception as e:
                    error_logger(f"Error parsing function in {file_path}: {e}")
                    continue

        return functions

    def _parse_classes(self, captures: list, source_code: str, file_path: Path) -> list[Dict[str, Any]]:
        classes = []

        for node, capture_name in captures:
            if capture_name == "class":
                try:
                    start_line = node.start_point[0] + 1
                    end_line = node.end_point[0] + 1
                    
                    name_captures = [
                        (n, cn) for n, cn in captures 
                        if cn == "name" and n.parent == node
                    ]
                    
                    if name_captures:
                        name_node = name_captures[0][0]
                        class_name = source_code[name_node.start_byte:name_node.end_byte]
                        
                        source_text = source_code[node.start_byte:node.end_byte]
                        
                        classes.append({
                            "name": class_name,
                            "line_number": start_line,
                            "end_line": end_line,
                            "source": source_text,
                            "file_path": str(file_path),
                            "lang": self.language_name,
                        })
                        
                except Exception as e:
                    error_logger(f"Error parsing class in {file_path}: {e}")
                    continue

        return classes

    def _parse_imports(self, captures: list, source_code: str) -> list[dict]:
        imports = []
        
        for node, capture_name in captures:
            if capture_name == "import":
                try:
                    import_text = source_code[node.start_byte:node.end_byte]
                    import_match = re.search(r'import\s+(?:static\s+)?([^;]+)', import_text)
                    if import_match:
                        import_path = import_match.group(1).strip()
                        
                        import_data = {
                            "name": import_path,
                            "full_import_name": import_path,
                            "line_number": node.start_point[0] + 1,
                            "alias": None,
                            "context": (None, None),
                            "lang": self.language_name,
                            "is_dependency": False,
                        }
                        imports.append(import_data)
                except Exception as e:
                    error_logger(f"Error parsing import: {e}")
                    continue

        return imports

    def _parse_calls(self, captures: list, source_code: str) -> list[dict]:
        calls = []
        seen_calls = set()
        
        for node, capture_name in captures:
            if capture_name == "name":
                try:
                    call_name = source_code[node.start_byte:node.end_byte]
                    line_number = node.start_point[0] + 1
                    
                    # Avoid duplicates
                    call_key = f"{call_name}_{line_number}"
                    if call_key in seen_calls:
                        continue
                    seen_calls.add(call_key)
                    
                    call_data = {
                        "name": call_name,
                        "full_name": call_name,
                        "line_number": line_number,
                        "args": [],
                        "inferred_obj_type": None,
                        "context": (None, None),
                        "class_context": (None, None),
                        "lang": self.language_name,
                        "is_dependency": False,
                    }
                    calls.append(call_data)
                except Exception as e:
                    error_logger(f"Error parsing call: {e}")
                    continue

        return calls
    

    def _extract_parameter_names(self, params_text: str) -> list[str]:
        params = []
        if not params_text or params_text.strip() == "()":
            return params
            
        params_content = params_text.strip("()")
        if not params_content:
            return params
            
        for param in params_content.split(","):
            param = param.strip()
            if param:
                parts = param.split()
                if len(parts) >= 2:
                    param_name = parts[-1]
                    params.append(param_name)
                    
        return params


def pre_scan_java(files: list[Path], parser_wrapper) -> dict:
    name_to_files = {}
    
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            class_matches = re.finditer(r'\b(?:public\s+|private\s+|protected\s+)?(?:static\s+)?(?:abstract\s+)?(?:final\s+)?class\s+(\w+)', content)
            for match in class_matches:
                class_name = match.group(1)
                if class_name not in name_to_files:
                    name_to_files[class_name] = []
                name_to_files[class_name].append(str(file_path))
            
            interface_matches = re.finditer(r'\b(?:public\s+|private\s+|protected\s+)?interface\s+(\w+)', content)
            for match in interface_matches:
                interface_name = match.group(1)
                if interface_name not in name_to_files:
                    name_to_files[interface_name] = []
                name_to_files[interface_name].append(str(file_path))
                
        except Exception as e:
            error_logger(f"Error pre-scanning Java file {file_path}: {e}")
            
    return name_to_files
def _find_annotations(tree):
    # Detect annotation definitions like @interface CustomAnnotation
    annotations = []
    for node in tree.find_all("annotation_type_declaration"):
        name = node.child_by_field_name("name").text
        annotations.append({
            "type": "Annotation",
            "name": name,
            "location": node.start_point
        })
    return annotations

def _find_applied_annotations(tree):
    # Detect usages like @Entity, @Override
    applied = []
    for node in tree.find_all("marker_annotation"):
        name = node.child_by_field_name("name").text
        applied.append({
            "type": "AnnotationUsage",
            "name": name,
            "location": node.start_point
        })
    return applied

