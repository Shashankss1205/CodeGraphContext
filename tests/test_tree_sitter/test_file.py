import os
from pathlib import Path
from src.codegraphcontext.tools.languages.python import PythonTreeSitterParser
class MockParser:
    def parse(self, source_bytes):
        class MockTree:
            @property
            def root_node(self):
                return None  # You can mock this deeper if needed
        return MockTree()

class MockQuery:
    def captures(self, node):
        return []  # Simulate no matches for now

class MockLanguage:
    def query(self, query_str):
        return MockQuery()

class MockGenericParserWrapper:
    def __init__(self):
        self.language_name = "python"
        self.language = MockLanguage()
        self.parser = MockParser()


def test_super_resolution():
    # Simulated parsed output from two files
    parsed = [
        {
            "type": "function_call",
            "full_name": "super().greet",
            "class_context": "B",
            "name": "greet"
        },
        {
            "type": "class",
            "name": "B",
            "bases": ["A"]
        },
        {
            "type": "class",
            "name": "A",
            "bases": []
        },
        {
            "type": "function",
            "name": "greet",
            "class_context": "A",
            "file_path": "class_instantiation.py"
        },
        {
            "type": "function",
            "name": "greet",
            "class_context": "Z",
            "file_path": "complex_classes.py"
        }
    ]

    # Find the super().greet() call
    target_call = next(
        (item for item in parsed if item.get("type") == "function_call" and item.get("full_name") == "super().greet"),
        None
    )

    assert target_call is not None, "super().greet() call not found"

    # Simulated resolution logic
    current_class = target_call.get("class_context")
    method_name = target_call.get("name")

    class_map = {
        cls["name"]: cls
        for cls in parsed
        if cls.get("type") == "class"
    }

    resolved = None
    if current_class and current_class in class_map:
        bases = class_map[current_class].get("bases", [])
        for base in bases:
            base_class = class_map.get(base)
            if base_class:
                for item in parsed:
                    if (
                        item.get("type") == "function"
                        and item.get("name") == method_name
                        and item.get("class_context") == base
                    ):
                        resolved = f"{item.get('file_path')}:{base}.{method_name}"
                        break
            if resolved:
                break

    assert resolved is not None, "Resolution failed: no matching method found in base classes"
    assert not resolved.endswith("Z.greet"), f"Bug: super().greet() incorrectly resolved to {resolved}"
