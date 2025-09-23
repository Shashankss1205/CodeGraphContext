import subprocess
import json
import os
import time
import pytest

# Path to the sample project used in tests
SAMPLE_PROJECT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "sample_project"))

# Helper function to call a tool, now shared across all tests
def call_tool(server, name, args):
    request = {
        "jsonrpc": "2.0",
        "id": int(time.time()),
        "method": "tools/call",
        "params": {"name": name, "arguments": args}
    }
    response = server(request)
    
    if "result" in response:
        content = json.loads(response["result"]["content"][0]["text"])
        return content
    elif "error" in response:
        return response
    else:
        raise ValueError(f"Unexpected response format: {response}")

@pytest.fixture(scope="module")
def server():
    """
    A module-scoped fixture that starts the cgc server once for all tests
    in this file and provides a communication helper function.
    """
    print("\n--- Setting up server fixture ---")
    
    env_content = """
NEO4J_URI=neo4j+s://44df5fd5.databases.neo4j.io
NEO4J_USERNAME=44df5fd5
NEO4J_PASSWORD=vSwK0dBCmaaMEQKFvWWFc7bPAdYlMAXFBlND-Tj-OEA
"""
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    with open(env_path, "w") as f:
        f.write(env_content)
    print(f"Created .env file at {env_path}")

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

        print("Waiting for server to be ready...")
        for line in iter(process.stderr.readline, ''):
            print(f"STDERR: {line.strip()}")
            if "MCP Server is running" in line:
                print("Server is ready.")
                break

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
        
        print("Initializing server connection...")
        init_request = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        init_response = send_receive(init_request)
        assert init_response.get("id") == 1 and "result" in init_response, "Initialization failed"
        print("Server connection initialized.")

        yield send_receive

    finally:
        print("\n--- Tearing down server fixture ---")
        if process:
            print("Terminating server process.")
            process.terminate()
            process.wait()
            print("Server process terminated.")
        if os.path.exists(env_path):
            os.remove(env_path)
            print("Removed .env file.")

def pytest_addoption(parser):
    parser.addoption(
        "--no-reindex", action="store_true", default=False, help="Skip re-indexing the project for tests"
    )

@pytest.fixture(scope="module")
def indexed_project(server, request):
    """
    Ensures the sample project is indexed before running tests.
    """
    if not request.config.getoption("--no-reindex"):
        print("\n--- Ensuring project is indexed ---")
        delete_result = call_tool(server, "delete_repository", {"repo_path": SAMPLE_PROJECT_PATH})
        print(f"Delete result: {delete_result}")

        add_result = call_tool(server, "add_code_to_graph", {"path": SAMPLE_PROJECT_PATH})
        assert add_result.get("success") is True, f"add_code_to_graph failed: {add_result.get('error')}"
        job_id = add_result.get("job_id")
        assert job_id is not None, "add_code_to_graph did not return a job_id"
        print(f"Started indexing job with ID: {job_id}")

        start_time = time.time()
        timeout = 180
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
    else:
        print("\n--- Skipping re-indexing as per --no-reindex flag ---")
    
    return server

class CodeGraph:
    """
    A wrapper class that provides a .query() method to execute Cypher
    against the indexed graph, compatible with our tests.
    """
    def __init__(self, server_communicator):
        self.server = server_communicator

    def query(self, cypher_query: str):
        response = call_tool(self.server, "execute_cypher_query", {"cypher_query": cypher_query})
        if response.get("success"):
            return response.get("results", [])
        else:
            error_details = response.get('error', 'Unknown error')
            raise RuntimeError(f"Cypher query failed: {error_details}\nQuery was: {cypher_query}")

@pytest.fixture(scope="module")
def graph(indexed_project):
    """
    Provides a CodeGraph object to query the indexed project.
    Depends on indexed_project to ensure the graph is ready.
    """
    print("\n--- Creating CodeGraph query wrapper ---")
    return CodeGraph(indexed_project)