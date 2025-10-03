import json
import sys

def load_function_calls(path="function_calls.json"):
    """Load captured function calls from a JSON file."""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading function calls: {e}")
        return []

def find_all_callees(caller_name, class_context=None):
    """Find all callees invoked by a given function."""
    calls = load_function_calls()
    callees = []

    for call in calls:
        if call.get("context") == caller_name and (
            not class_context or call.get("class_context") == class_context
        ):
            callees.append(call.get("name"))

    if callees:
        print(f"\nFound {len(callees)} callees for {caller_name}:")
        for callee in callees:
            print(f"- {callee}")
    else:
        print(f"\nNo callees found for {caller_name}.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python graph_query.py <caller_name> [class_context]")
    else:
        caller = sys.argv[1]
        cls = sys.argv[2] if len(sys.argv) > 2 else None
        find_all_callees(caller, cls)
