import pytest
from pathlib import Path
import sys
import os

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from codegraphcontext.tools.languages.swift import SwiftTreeSitterParser
from codegraphcontext.tools.graph_builder import TreeSitterParser
from codegraphcontext.utils.tree_sitter_manager import get_tree_sitter_manager

@pytest.fixture
def parser():
    """Returns an instance of the Swift parser via generic wrapper."""
    return TreeSitterParser('swift')

@pytest.fixture
def sample_project_path():
    """Returns the path to the sample Swift project."""
    return Path(__file__).parent / "sample_project_swift"

def test_parse_main_swift(parser, sample_project_path):
    """Test parsing of Main.swift."""
    file_path = sample_project_path / "Main.swift"
    result = parser.parse(file_path, is_dependency=False)

    assert result["file_path"] == str(file_path)
    
    # Check Classes
    classes = {c["name"] for c in result["classes"]}
    assert "Main" in classes
    assert "Calculator" in classes

    # Check Functions in Main
    main_functions = [f for f in result["functions"] if f.get("class_context") == "Main"]
    method_names = {m["name"] for m in main_functions}
    assert "run" in method_names
    
    # Check Calculator functions
    calc_functions = [f for f in result["functions"] if f.get("class_context") == "Calculator"]
    calc_method_names = {m["name"] for m in calc_functions}
    assert "add" in calc_method_names
    assert "subtract" in calc_method_names
    assert "multiply" in calc_method_names

def test_parse_user_swift(parser, sample_project_path):
    """Test parsing of User.swift (Struct and Protocol)."""
    file_path = sample_project_path / "User.swift"
    result = parser.parse(file_path, is_dependency=False)

    # Check Protocol
    protocols = {p["name"] for p in result["protocols"]}
    assert "Greeter" in protocols

    # Check Struct
    structs = {s["name"]: s for s in result["structs"]}
    assert "User" in structs
    user_struct = structs["User"]
    
    # Verify protocol conformance
    assert "Greeter" in user_struct.get("bases", [])

    # Check methods
    user_methods = [f for f in result["functions"] if f.get("class_context") == "User"]
    method_names = {m["name"] for m in user_methods}
    assert "greet" in method_names
    assert "isAdult" in method_names

def test_parse_shapes_swift(parser, sample_project_path):
    """Test parsing of Shapes.swift (Protocol conformance)."""
    file_path = sample_project_path / "Shapes.swift"
    result = parser.parse(file_path, is_dependency=False)
    
    # Check Protocol
    protocols = {p["name"] for p in result["protocols"]}
    assert "Shape" in protocols
    
    # Check Classes
    classes = {c["name"]: c for c in result["classes"]}
    assert "Circle" in classes
    assert "Triangle" in classes
    
    # Check Structs
    structs = {s["name"]: s for s in result["structs"]}
    assert "Rectangle" in structs
    
    # Verify protocol conformance
    assert "Shape" in classes["Circle"].get("bases", [])
    assert "Shape" in structs["Rectangle"].get("bases", [])
    assert "Shape" in classes["Triangle"].get("bases", [])

def test_parse_vehicles_swift(parser, sample_project_path):
    """Test parsing of Vehicles.swift (Enums and Inheritance)."""
    file_path = sample_project_path / "Vehicles.swift"
    result = parser.parse(file_path, is_dependency=False)
    
    # Check Enums
    enums = {e["name"] for e in result["enums"]}
    assert "VehicleType" in enums
    assert "Result" in enums
    
    # Check Classes
    classes = {c["name"]: c for c in result["classes"]}
    assert "Vehicle" in classes
    assert "Car" in classes
    
    # Verify inheritance
    car_class = classes["Car"]
    assert "Vehicle" in car_class.get("bases", [])

def test_parse_generics_swift(parser, sample_project_path):
    """Test parsing of Generics.swift (Generic types and protocols)."""
    file_path = sample_project_path / "Generics.swift"
    result = parser.parse(file_path, is_dependency=False)
    
    # Check Classes
    classes = {c["name"] for c in result["classes"]}
    assert "Stack" in classes
    
    # Check Protocols
    protocols = {p["name"] for p in result["protocols"]}
    assert "Container" in protocols
    
    # Check Structs
    structs = {s["name"] for s in result["structs"]}
    assert "IntCollection" in structs
    
    # Check functions (generic swap function)
    functions = [f for f in result["functions"] if f.get("class_context") is None]
    function_names = {f["name"] for f in functions}
    assert "swap" in function_names

def test_import_resolution(parser, sample_project_path):
    """Test that imports are correctly extracted."""
    file_path = sample_project_path / "Main.swift"
    result = parser.parse(file_path, is_dependency=False)
    
    imports = result.get("imports", [])
    assert len(imports) > 0
    
    # Check for Foundation import
    import_names = {imp.get("name", "") for imp in imports}
    assert "Foundation" in import_names

def test_function_calls(parser, sample_project_path):
    """Test that function calls are detected."""
    file_path = sample_project_path / "Main.swift"
    result = parser.parse(file_path, is_dependency=False)
    
    calls = result.get("function_calls", [])
    assert len(calls) > 0
    
    # Check for specific method calls
    call_names = {c["name"] for c in calls}
    assert "greet" in call_names
    assert "add" in call_names
