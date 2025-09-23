def test_module_b_file_node(indexed_project):
    server = indexed_project
    query = f"MATCH (f:File) WHERE f.path ENDS WITH 'module_b.py' RETURN f"
    result = call_tool(server, "execute_cypher_query", {"cypher_query": query})
    assert len(result.get("results", [])) == 1, "File node for module_b.py not found"

def test_module_b_function_nodes(indexed_project):
    server = indexed_project
    query = f"MATCH (f:Function)-[:CONTAINS]-(file:File) WHERE file.path ENDS WITH 'module_b.py' RETURN f.name as name"
    result = call_tool(server, "execute_cypher_query", {"cypher_query": query})
    functions = [item['name'] for item in result.get("results", [])]
    assert "helper" in functions
    assert "process_data" in functions
    assert "factorial" in functions

def test_module_b_variable_node(indexed_project):
    server = indexed_project
    query = f"MATCH (v:Variable)-[:CONTAINS]-(file:File) WHERE file.path ENDS WITH 'module_b.py' AND v.name = 'value' RETURN v"
    result = call_tool(server, "execute_cypher_query", {"cypher_query": query})
    assert len(result.get("results", [])) == 1, "Variable node for value not found in module_b.py"

def test_module_b_factorial_calls_factorial(indexed_project):
    server = indexed_project
    query = f"MATCH (:Function {{name: 'factorial', file_path: '{os.path.join(SAMPLE_PROJECT_PATH, 'module_b.py')}'}})-[:CALLS]->(:Function {{name: 'factorial'}}) RETURN count(*)"
    result = call_tool(server, "execute_cypher_query", {"cypher_query": query})
    assert result.get("results", [])[0]['count(*)'] == 1