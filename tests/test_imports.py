import subprocess
import json
import os
import time
import pytest

# Path to the sample project used in tests
SAMPLE_PROJECT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "sample_project"))

# Helper function to call a tool
def call_tool(server, name, args):
    request = {
        "jsonrpc": "2.0",
        "id": int(time.time()),
        "method": "tools/call",
        "params": {"name": name, "arguments": args}
    }
    response = server(request)
    content = json.loads(response["result"]["content"][0]["text"])
    return content

@pytest.fixture(scope="module")
def server():
    """
    A module-scoped fixture that starts the cgc server once for all tests
    in this file and provides a communication helper function.
    """
    print("\n--- Setting up server fixture ---")
    
    # 1. Create .env file with credentials
    env_content = """
NEO4J_URI=neo4j+s://44df5fd5.databases.neo4j.io
NEO4J_USERNAME=44df5fd5
NEO4J_PASSWORD=vSwK0dBCmaaMEQKFvWWFc7bPAdYlMAXFBlND-Tj-OEA
"""
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    with open(env_path, "w") as f:
        f.write(env_content)
    print(f"Created .env file at {env_path}")

    # 2. Start the server process
    process = None
    try:
        print("Starting cgc server process...")
        process = subprocess.Popen(
            ["cgc", "start"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.path.join(os.path.dirname(__file__), ".."))

        # 3. Wait for the server to be ready
        print("Waiting for server to be ready...")
        for line in iter(process.stderr.readline, ''):
            print(f"STDERR: {line.strip()}")
            if "MCP Server is running" in line:
                print("Server is ready.")
                break

        # 4. Define the communication helper
        def send_receive(request):
            print(f"--> Sending request: {json.dumps(request)}")
            process.stdin.write(json.dumps(request) + "\n")
            process.stdin.flush()
            while True:
                response_line = process.stdout.readline()
                print(f"<-- Received line: {response_line.strip()}")
                try:
                    return json.loads(response_line)
                except json.JSONDecodeError:
                    continue
        
        # 5. Initialize the server connection
        print("Initializing server connection...")
        init_request = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        init_response = send_receive(init_request)
        assert init_response.get("id") == 1 and "result" in init_response, "Initialization failed"
        print("Server connection initialized.")

        # 6. Yield the helper to the tests
        yield send_receive

    # 7. Teardown: Stop the server and remove .env
    finally:
        print("\n--- Tearing down server fixture ---")
        if process:
            print("Terminating server process.")
            process.terminate()
            process.wait()
            print("Server process terminated.")
        os.remove(env_path)
        print("Removed .env file.")

@pytest.fixture(scope="module")
def indexed_project(server):
    """
    A module-scoped fixture that ensures the sample project is indexed before running tests.
    """
    print("\n--- Ensuring project is indexed ---")
    # 1. Delete repository to ensure a clean state
    delete_result = call_tool(server, "delete_repository", {"repo_path": SAMPLE_PROJECT_PATH})
    print(f"Delete result: {delete_result}")

    # 2. Add the sample project to the graph
    add_result = call_tool(server, "add_code_to_graph", {"path": SAMPLE_PROJECT_PATH})
    assert add_result.get("success") is True, f"add_code_to_graph failed: {add_result.get('error')}"
    job_id = add_result.get("job_id")
    assert job_id is not None, "add_code_to_graph did not return a job_id"
    print(f"Started indexing job with ID: {job_id}")

    # 3. Wait for the indexing job to complete
    start_time = time.time()
    timeout = 180  # 180 seconds
    while True:
        if time.time() - start_time > timeout:
            pytest.fail(f"Job {job_id} did not complete within {timeout} seconds.")
        status_result = call_tool(server, "check_job_status", {"job_id": job_id})
        job_status = status_result.get("job", {}).get("status")
        print(f"Current job status: {job_status}")
        if job_status == "completed":
            print("Job completed successfully.")
            break
        assert job_status not in ["failed", "cancelled"], f"Job failed with status: {job_status}"
        time.sleep(2)
    
    return server

def test_import_with_alias(indexed_project):
    """
    Tests resolving a function call from a module imported with an alias.
    """
    server = indexed_project
    print("\n--- Testing import with alias ---")
    analysis_result = call_tool(server, "analyze_code_relationships", {
        "query_type": "find_callees",
        "target": "foo",
        "context": os.path.join(SAMPLE_PROJECT_PATH, "module_a.py")
    })
    assert analysis_result.get("success") is True, f"analyze_code_relationships failed: {analysis_result.get('error')}"
    results = analysis_result.get("results", {}).get("results", [])
    
    assert len(results) >= 1, f"Expected at least 1 callee for foo, but found {len(results)}."
    callee_names = {r['called_function'] for r in results}
    assert 'helper' in callee_names
    print("Successfully verified that find_callees finds the correct callee from aliased import.")

def test_circular_import(indexed_project):
    """
    Tests resolving a function call in a circular import scenario.
    """
    server = indexed_project
    print("\n--- Testing circular import ---")
    analysis_result = call_tool(server, "analyze_code_relationships", {
        "query_type": "find_callees",
        "target": "func1",
        "context": os.path.join(SAMPLE_PROJECT_PATH, "circular1.py")
    })
    assert analysis_result.get("success") is True, f"analyze_code_relationships failed: {analysis_result.get('error')}"
    results = analysis_result.get("results", {}).get("results", [])
    
    assert len(results) >= 1
    callee_names = {r['called_function'] for r in results}
    assert 'func2' in callee_names
    print("Successfully verified that find_callees handles circular imports.")

@pytest.mark.skip(reason="CodeGraphContext does not currently store CALLS relationships for standard library functions like random.randint in a queryable way, even after indexing the package. The internal debug log shows resolution, but it's not exposed via the tool's API or direct Cypher queries.")
def test_conditional_import(indexed_project):
    """
    Tests resolving a function call from a conditionally imported module.
    """
    server = indexed_project
    print("\n--- Testing conditional import ---")
    analysis_result = call_tool(server, "analyze_code_relationships", {
        "query_type": "find_callees",
        "target": "use_random",
        "context": os.path.join(SAMPLE_PROJECT_PATH, "advanced_imports.py")
    })
    assert analysis_result.get("success") is True, f"analyze_code_relationships failed: {analysis_result.get('error')}"
    results = analysis_result.get("results", {}).get("results", [])
    
    assert len(results) >= 1
    callee_names = {r['called_function'] for r in results}
    assert 'randint' in callee_names
    print("Verified that find_callees handles conditional imports.")

def test_cross_module_function_calls(indexed_project):
    """testing a function call from one module to the other """
    server=indexed_project
    print("\n---Testing cross module function calls---")
    analysis_result=call_tool(server,"analyzing_code_relationships" ,{
        "query_type":"find_callees",
        "target":"caller_functions",
        "context":os.path.join(SAMPLE_PROJECT_PATH,"module_b.py")
    })

    assert analysis_result.get("success") is True or f"Analysis failed: {analysis_result.get('error')}"
    results = analysis_result.get("results", {}).get("results", [])
    assert len(results) >= 1
    callee_names = {i['called_function'] for i in results}
    assert 'callee_func' in callee_names
    print("Verified cross-module function resolution.")


def test_class_method_calls(indexed_project):
    """Testing the method calls inside a class."""
    server = indexed_project
    print("\n---Testing class method calls---")
    analysis_result = call_tool(server, "analyzing_code_relationships", {
        "query_type": "find_callees",
        "target": "MyClass.method_a",
        "context": os.path.join(SAMPLE_PROJECT_PATH, "classes.py")
    })
    assert analysis_result.get("success") is True, f"Analysis failed: {analysis_result.get('error')}"
    results = analysis_result.get("results", {}).get("results", [])
    callee_names = {j['called_function'] for j in results}
    assert 'method_b' in callee_names
    print("Verified that method_a calls method_b inside the class.")


def test_unused_import(indexed_project):
    """Ensures unused imports are not incorrectly reported as callees."""
    server = indexed_project
    print("\n--- Testing unused import ---")
    analysis_result = call_tool(server, "analyze_code_relationships", {
        "query_type": "find_callees",
        "target": "do_nothing",
        "context": os.path.join(SAMPLE_PROJECT_PATH, "unused_imports.py")
    })
    assert analysis_result.get("success") is True
    results = analysis_result.get("results", {}).get("results", [])
    callee_names = {r['called_function'] for r in results}
    assert 'random_function' not in callee_names
    print("Verified that unused imports do not create false positives.")

