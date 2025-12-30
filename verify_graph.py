
import os
import json
from pathlib import Path
from typing import Dict, List, Any
from neo4j import GraphDatabase
from codegraphcontext.tools.graph_builder import TreeSitterParser

EXT_TO_LANG = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".java": "java",
    ".cs": "c_sharp",
    ".rs": "rust",
    ".go": "go",
    ".rb": "ruby",
    ".php": "php",
    ".cpp": "cpp",
    ".h": "cpp"
}

# Credentials
URI = "neo4j://localhost:7687"
USER = "neo4j"
PASSWORD = "12345678"

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

def get_node_counts(file_path: str):
    with driver.session() as session:
        result = session.run("""
            MATCH (f:File {path: $path})
            OPTIONAL MATCH (f)-[:CONTAINS*]->(c:Class)
            OPTIONAL MATCH (f)-[:CONTAINS*]->(fu:Function)
            OPTIONAL MATCH (f)-[:CONTAINS*]->(v:Variable)
            RETURN count(DISTINCT c) as class_count, 
                   count(DISTINCT fu) as func_count, 
                   count(DISTINCT v) as var_count
        """, path=file_path)
        return result.single()

def get_all_calls(file_path: str):
    with driver.session() as session:
        result = session.run("""
            MATCH (f:File {path: $path})
            MATCH (f)-[:CONTAINS*]->(caller)
            WHERE caller:Function OR caller:File
            MATCH (caller)-[r:CALLS]->(called)
            RETURN DISTINCT caller.name as caller_name, called.name as called_name, r.line_number as line_number
        """, path=file_path)
        return [dict(record) for record in result]

def verify_file(file_path: Path):
    print(f"\n--- Verifying File: {file_path.name} ---")
    lang = EXT_TO_LANG.get(file_path.suffix)
    if not lang:
        print(f"Skipping unknown extension: {file_path.suffix}")
        return

    parser = TreeSitterParser(lang)
    parsed_data = parser.language_specific_parser.parse(file_path)
    
    abs_path = str(file_path.resolve())
    db_counts = get_node_counts(abs_path)
    
    # Check Functions
    expected_funcs = sorted([(f['name'], f['line_number']) for f in parsed_data.get('functions', [])])
    with driver.session() as session:
        result = session.run("MATCH (f:File {path: $path})-[:CONTAINS*]->(fu:Function) RETURN DISTINCT fu.name as name, fu.line_number as line", path=abs_path)
        db_funcs = sorted([(record['name'], record['line']) for record in result])
    
    print(f"Functions (Source): {len(expected_funcs)}")
    print(f"  Names: {expected_funcs}")
    print(f"Functions (DB):     {len(db_funcs)}")
    print(f"  Names: {db_funcs}")
    
    # Check Classes
    expected_classes = sorted([(c['name'], c['line_number']) for c in parsed_data.get('classes', [])])
    with driver.session() as session:
        result = session.run("MATCH (f:File {path: $path})-[:CONTAINS*]->(c:Class) RETURN DISTINCT c.name as name, c.line_number as line", path=abs_path)
        db_classes = sorted([(record['name'], record['line']) for record in result])
    print(f"Classes (Source): {len(expected_classes)} | (DB): {len(db_classes)}")
    if expected_classes != db_classes:
        print(f"!!! MISMATCH in classes for {file_path.name}")

    # Check Variables
    expected_vars = sorted([(v['name'], v['line_number']) for v in parsed_data.get('variables', [])])
    with driver.session() as session:
        result = session.run("MATCH (f:File {path: $path})-[:CONTAINS*]->(v:Variable) RETURN DISTINCT v.name as name, v.line_number as line", path=abs_path)
        db_vars = sorted([(record['name'], record['line']) for record in result])
    print(f"Variables (Source): {len(expected_vars)} | (DB): {len(db_vars)}")
    if expected_vars != db_vars:
        print(f"!!! MISMATCH in variables for {file_path.name}")
    
    # Check Calls
    expected_calls = sorted([(c['name'], c['line_number']) for c in parsed_data.get('function_calls', [])])
    db_calls_raw = get_all_calls(abs_path)
    db_calls = sorted([(c['called_name'], c['line_number']) for c in db_calls_raw])
    
    print(f"Calls (Source): {len(expected_calls)} | (DB): {len(db_calls)}")
    
    # Note: Variable counts might differ because we skip some in DB but parser might still list them 
    # (actually I updated the parser to skip them now, so they should match).

def main():
    # Test Python
    # Test C++
    base_dir = Path('/home/shashank/Desktop/CodeGraphContext/tests/sample_project_cpp')
    files = []
    # Verify cpp files
    files.extend(list(base_dir.rglob('*.cpp')))
    files.extend(list(base_dir.rglob('*.h')))
    files.sort()
    
    for f in files:
        verify_file(f)

if __name__ == "__main__":
    main()
    driver.close()
