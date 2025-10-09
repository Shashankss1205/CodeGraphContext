from flask import Flask, request, jsonify
import uuid

app = Flask(__name__)

# A registry of tools the server supports
# Each tool is a Python function taking params and returning result
TOOLS = {
    "add_numbers": lambda params: params["a"] + params["b"]
}

def make_jsonrpc_response(result=None, error=None, id=None):
    resp = {"jsonrpc": "2.0", "id": id}
    if error is not None:
        resp["error"] = error
    else:
        resp["result"] = result
    return resp

@app.route("/mcp", methods=["POST"])
def mcp_endpoint():
    """
    Expect JSON-RPC 2.0 requests. Handle tool invocation.
    """
    body = request.get_json()
    # Basic validation
    if body is None or "jsonrpc" not in body or body["jsonrpc"] != "2.0":
        return jsonify(make_jsonrpc_response(
            error={"code": -32600, "message": "Invalid Request"}, id=body.get("id", None)
        ))

    method = body.get("method")
    params = body.get("params", {})
    req_id = body.get("id")

    # A method for capability discovery, e.g. list tools
    if method == "mcp.discover_tools":
        # Return the list of tools and their parameter schemas (simplified)
        tools_info = { name: {"params": list(func.__code__.co_varnames)} for name, func in TOOLS.items() }
        return jsonify(make_jsonrpc_response(result=tools_info, id=req_id))

    # If method corresponds to a tool
    if method in TOOLS:
        try:
            tool_fn = TOOLS[method]
            result = tool_fn(params)
            return jsonify(make_jsonrpc_response(result=result, id=req_id))
        except Exception as e:
            return jsonify(make_jsonrpc_response(
                error={"code": -32000, "message": f"Tool execution error: {e}"}, id=req_id
            ))

    # Method not found
    return jsonify(make_jsonrpc_response(
        error={"code": -32601, "message": "Method not found"}, id=req_id
    ))

if __name__ == "__main__":
    app.run(port=5000)
