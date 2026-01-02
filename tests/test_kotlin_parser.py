import pytest
from pathlib import Path
import sys
import os

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from codegraphcontext.tools.languages.kotlin import KotlinTreeSitterParser
from codegraphcontext.tools.graph_builder import TreeSitterParser
from codegraphcontext.utils.tree_sitter_manager import get_tree_sitter_manager

@pytest.fixture
def parser():
    """Returns an instance of the Kotlin parser via generic wrapper."""
    return TreeSitterParser('kotlin')

@pytest.fixture
def sample_project_path():
    """Returns the path to the sample Kotlin project."""
    return Path(__file__).parent / "sample_project_kotlin"

def test_parse_main_kt(parser, sample_project_path):
    """Test parsing of Main.kt."""
    file_path = sample_project_path / "Main.kt"
    result = parser.parse(file_path, is_dependency=False)

    assert result["file_path"] == str(file_path)
    
    # Check Classes
    classes = {c["name"] for c in result["classes"]}
    assert "Main" in classes
    assert "Calculator" in classes

    # Check Functions in Main
    # Functions are returned in a flat list with 'class_context'
    main_functions = [f for f in result["functions"] if f.get("class_context") == "Main"]
    method_names = {m["name"] for m in main_functions}
    assert "main" in method_names
    
    # Check Call to User.greet
    # Calls are in result["function_calls"]
    greet_call = next((c for c in result["function_calls"] if c["name"] == "greet"), None)
    assert greet_call is not None, "Should detect call to greet()"
    
    # Verify type inference for the call (user.greet())
    # The variable 'user' is initialized with 'User(...)', so inferred_obj_type should be 'User'
    assert greet_call.get("inferred_obj_type") == "User"

def test_parse_user_kt(parser, sample_project_path):
    """Test parsing of User.kt (Data Class and Interface)."""
    file_path = sample_project_path / "User.kt"
    result = parser.parse(file_path, is_dependency=False)

    # Check Interface
    classes = {c["name"]: c for c in result["classes"]}
    assert "Greeter" in classes

    # Check Data Class
    assert "User" in classes
    user_class = classes["User"]
    
    # Verify inheritance
    assert "Greeter" in user_class.get("bases", [])

    # Check method override
    user_methods = [f for f in result["functions"] if f.get("class_context") == "User"]
    method_names = {m["name"] for m in user_methods}
    assert "greet" in method_names

def test_type_inference_calculator(parser, sample_project_path):
    """Test type inference for a simple local class usage."""
    file_path = sample_project_path / "Main.kt"
    result = parser.parse(file_path, is_dependency=False)
    
    # val calculator = Calculator()
    # println(calculator.add(5, 10))
    
    add_call = next((c for c in result["function_calls"] if c["name"] == "add"), None)
    assert add_call is not None
    assert add_call.get("inferred_obj_type") == "Calculator"

def test_import_resolution_support(parser, sample_project_path):
    """Test that imports are correctly extracted."""
    file_path = sample_project_path / "Main.kt"
    result = parser.parse(file_path, is_dependency=False)
    
    imports = result.get("imports", [])
    assert len(imports) > 0
    
    # Imports have "name" (path) and "full_import_name"
    found = False
    for imp in imports:
        if "com.example.project.User" in imp.get("name", ""):
            found = True
            break
    assert found, "Should find import for User"
