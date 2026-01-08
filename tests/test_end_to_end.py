import subprocess
import json
import os
import time
import pytest
import random
import string

SAMPLE_PROJECT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "sample_project"))

request_id_counter = 1

def call_tool(server_process, tool_name, tool_args):
    global request_id_counter
    request = {
        "jsonrpc": "2.0",
        "id": request_id_counter,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": tool_args}
    }
    request_id_counter += 1
    print(f"--> Sending request: {json.dumps(request)}")
    server_process.stdin.write(json.dumps(request) + "\n")
    server_process.stdin.flush()
    while True:
        response_line = server_process.stdout.readline()
        print(f"<-- Received line: {response_line.strip()}")
        try:
            response = json.loads(response_line)
            if response.get("id") == request["id"]:
                return json.loads(response["result"]["content"][0]["text"])
        except (json.JSONDecodeError, KeyError):
            continue

def run_command(command, shell=False, check=True):
    cmd_str = command if isinstance(command, str) else ' '.join(command)
    print(f"[CMD] {cmd_str}")
    try:
        process = subprocess.run(
            command,
            shell=shell,
            check=check,
            capture_output=True,
            text=True,
            timeout=300,
        )
        return process
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Error executing command: {cmd_str}")
        if e.stdout:
            print(f"[ERROR] STDOUT: {e.stdout}")
        if e.stderr:
            print(f"[ERROR] STDERR: {e.stderr}")
        return None
    except subprocess.TimeoutExpired:
        print(f"[ERROR] Command timed out: {cmd_str}")
        return None

def test_end_to_end_workflow_local_db():
    if not run_command(["docker", "--version"], check=False) or not run_command(["docker", "compose", "version"], check=False):
        pytest.skip("Docker or Docker Compose not found. Skipping test.")

    print("\n--- Setting up local Neo4j database ---")
    password = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(12))
    compose_content = f"""
services:
  neo4j:
    image: neo4j:5.21
    container_name: neo4j-cgc-test
    restart: unless-stopped
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/{password}
      - NEO4J_ACCEPT_LICENSE_AGREEMENT=yes
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs

volumes:
  neo4j_data:
  neo4j_logs:
"""
    compose_file = os.path.join(os.path.dirname(__file__), "..", "docker-compose-test.yml")
    with open(compose_file, "w") as f:
        f.write(compose_content)

    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    server_process = None

    try:
        print("--- Starting Neo4j container ---")
        run_command(["docker", "compose", "-f", compose_file, "up", "-d"])

        print("--- Waiting for Neo4j to be ready ---")
        max_attempts = 24
        for attempt in range(max_attempts):
            time.sleep(5)
            health_check = run_command([
                "docker", "exec", "neo4j-cgc-test", "cypher-shell",
                "-u", "neo4j", "-p", password,
                "RETURN 'Connection successful' as status"
            ], check=False)
            if health_check and health_check.returncode == 0:
                print("--- Neo4j is ready ---")
                break
            if attempt == max_attempts - 1:
                pytest.fail("Neo4j container did not become ready in time.")

        print("--- Creating .env file for server ---")
        env_content = f"""
NEO4J_URI=neo4j://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD={password}
DEFAULT_DATABASE=neo4j
"""
        with open(env_path, "w") as f:
            f.write(env_content)

        print("--- Starting server ---")
        server_process = subprocess.Popen(
            ["cgc", "mcp", "start"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.path.join(os.path.dirname(__file__), "..")
        )
        start_time = time.time()
        timeout_seconds = 60
        server_ready = False
        
        while time.time() - start_time < timeout_seconds:
            line = server_process.stderr.readline()
            if not line:
                # Process might have exited
                if server_process.poll() is not None:
                    break
                time.sleep(0.1)
                continue
                
            print(f"STDERR: {line.strip()}")
            if "MCP Server is running" in line:
                server_ready = True
                break
        
        if not server_ready:
            # If we timed out or process exited without ready message
            if server_process.poll() is not None:
                print(f"Server exited with code {server_process.returncode}")
            pytest.fail(f"Server did not become ready within {timeout_seconds} seconds")
        
        init_request = {"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {}}
        server_process.stdin.write(json.dumps(init_request) + "\n")
        server_process.stdin.flush()
        while True:
            response_line = server_process.stdout.readline()
            try:
                init_response = json.loads(response_line)
                if init_response.get("id") == 0:
                    break
            except json.JSONDecodeError:
                continue

        print("--- Calling tools ---")
        # Try to delete in case it exists from a previous run, but don't fail if it doesn't
        call_tool(server_process, "delete_repository", {"repo_path": SAMPLE_PROJECT_PATH})

        add_result = call_tool(server_process, "add_code_to_graph", {"path": SAMPLE_PROJECT_PATH})
        assert add_result.get("success") is True
        job_id = add_result.get("job_id")
        assert job_id is not None

        while True:
            status_result = call_tool(server_process, "check_job_status", {"job_id": job_id})
            if status_result.get("job", {}).get("status") == "completed":
                break
            time.sleep(2)

        list_result = call_tool(server_process, "list_indexed_repositories", {})
        assert list_result.get("success") is True
        assert SAMPLE_PROJECT_PATH in [repo["path"] for repo in list_result.get("repositories", [])]

    finally:
        print("--- Shutting down server and Neo4j container ---")
        if server_process:
            server_process.terminate()
            server_process.wait()
        run_command(["docker", "compose", "-f", compose_file, "down"])

        if os.path.exists(env_path):
            os.remove(env_path)
        if os.path.exists(compose_file):
            os.remove(compose_file)