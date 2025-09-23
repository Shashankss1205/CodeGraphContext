
import pytest
import os

from .conftest import SAMPLE_PROJECT_PATH

# ==============================================================================
# == EXPECTED RELATIONSHIPS
# ==============================================================================

EXPECTED_STRUCTURE = [
    ("module_a.py", "foo", "Function"),
    ("module_a.py", "bar", "Function"),
    ("module_a.py", "outer", "Function"),
    ("module_b.py", "helper", "Function"),
    ("module_b.py", "process_data", "Function"),
    ("module_b.py", "factorial", "Function"),
    ("advanced_classes.py", "A", "Class"),
    ("advanced_classes.py", "B", "Class"),
    ("advanced_classes.py", "C", "Class"),
    ("module_a.py", "nested", "Function"),
    ("advanced_calls.py", "square", "Function"),
    ("advanced_calls.py", "calls", "Function"),
    ("advanced_calls.py", "Dummy", "Class"),
    ("advanced_classes2.py", "Base", "Class"),
    ("advanced_classes2.py", "Mid", "Class"),
    ("advanced_classes2.py", "Final", "Class"),
    ("advanced_classes2.py", "Mixin1", "Class"),
    ("advanced_classes2.py", "Mixin2", "Class"),
    ("advanced_classes2.py", "Combined", "Class"),
    ("advanced_classes2.py", "Point", "Class"),
    ("advanced_classes2.py", "Color", "Class"),
    ("advanced_classes2.py", "handle", "Function"),
    ("advanced_functions.py", "with_defaults", "Function"),
    ("advanced_functions.py", "with_args_kwargs", "Function"),
    ("advanced_functions.py", "higher_order", "Function"),
    ("advanced_functions.py", "return_function", "Function"),
    ("advanced_imports.py", "outer_import", "Function"),
    ("advanced_imports.py", "use_random", "Function"),
    ("async_features.py", "fetch_data", "Function"),
    ("async_features.py", "main", "Function"),
    ("callbacks_decorators.py", "executor", "Function"),
    ("callbacks_decorators.py", "square", "Function"),
    ("callbacks_decorators.py", "log_decorator", "Function"),
    ("callbacks_decorators.py", "hello", "Function"),
    ("class_instantiation.py", "A", "Class"),
    ("class_instantiation.py", "B", "Class"),
    ("class_instantiation.py", "Fluent", "Class"),
]

EXPECTED_INHERITANCE = [
    pytest.param("C", "advanced_classes.py", "A", "advanced_classes.py", id="C inherits from A"),
    pytest.param("C", "advanced_classes.py", "B", "advanced_classes.py", id="C inherits from B"),
    pytest.param("ConcreteThing", "advanced_classes.py", "AbstractThing", "advanced_classes.py", id="ConcreteThing inherits from AbstractThing"),
    pytest.param("Mid", "advanced_classes2.py", "Base", "advanced_classes2.py", id="Mid inherits from Base"),
    pytest.param("Final", "advanced_classes2.py", "Mid", "advanced_classes2.py", id="Final inherits from Mid"),
    pytest.param("Combined", "advanced_classes2.py", "Mixin1", "advanced_classes2.py", id="Combined inherits from Mixin1"),
    pytest.param("Combined", "advanced_classes2.py", "Mixin2", "advanced_classes2.py", id="Combined inherits from Mixin2"),
    pytest.param("B", "class_instantiation.py", "A", "class_instantiation.py", id="B inherits from A"),
    pytest.param("B", "class_instantiation.py", "A", "class_instantiation.py", marks=pytest.mark.skip(reason="Indexer does not support inheritance via super() calls"), id="B inherits from A via super()"),
    pytest.param("Child", "complex_classes.py", "Base", "complex_classes.py", marks=pytest.mark.skip(reason="Indexer does not support inheritance via super() calls"), id="Child inherits from Base via super()"),
]

EXPECTED_CALLS = [
    pytest.param("foo", "module_a.py", None, "helper", "module_b.py", None, id="module_a.foo->module_b.helper"),
    pytest.param("foo", "module_a.py", None, "process_data", "module_b.py", None, id="module_a.foo->module_b.process_data"),
    pytest.param("factorial", "module_b.py", None, "factorial", "module_b.py", None, id="module_b.factorial->recursive"),
    pytest.param("calls", "advanced_calls.py", None, "square", "advanced_calls.py", None, id="advanced_calls.calls->square"),
    pytest.param("call_helper_twice", "module_c/submodule1.py", None, "helper", "module_b.py", None, id="submodule1.call_helper_twice->module_b.helper"),
    pytest.param("wrapper", "module_c/submodule2.py", None, "call_helper_twice", "module_c/submodule1.py", None, id="submodule2.wrapper->submodule1.call_helper_twice"),
    pytest.param("main", "async_features.py", None, "fetch_data", "async_features.py", None, id="async.main->fetch_data"),
    pytest.param("func1", "circular1.py", None, "func2", "circular2.py", None, id="circular1.func1->circular2.func2"),
    pytest.param("run", "cli_and_dunder.py", None, "with_defaults", "advanced_functions.py", None, id="cli.run->with_defaults"),
    pytest.param("use_dispatcher", "mapping_calls.py", None, "call", "mapping_calls.py", None, id="mapping.use_dispatcher->call"),
    pytest.param("calls", "advanced_calls.py", None, "method", "advanced_calls.py", "Dummy", marks=pytest.mark.skip(reason="Dynamic call with getattr is not supported"), id="advanced_calls.calls->Dummy.method"),
    pytest.param("both", "advanced_classes2.py", "Combined", "m1", "advanced_classes2.py", "Mixin1", id="advanced_classes2.both->m1"),
    pytest.param("both", "advanced_classes2.py", "Combined", "m2", "advanced_classes2.py", "Mixin2", id="advanced_classes2.both->m2"),
    pytest.param("executor", "callbacks_decorators.py", None, "square", "callbacks_decorators.py", None, marks=pytest.mark.skip(reason="Dynamic call passing function as argument is not supported"), id="callbacks.executor->square"),
    pytest.param("reexport", "import_reexports.py", None, "core_function", "import_reexports.py", None, id="reexport->core_function"),
    pytest.param("greet", "class_instantiation.py", "B", "greet", "class_instantiation.py", "A", marks=pytest.mark.skip(reason="super() calls are not supported yet"), id="B.greet->A.greet"),
]

EXPECTED_IMPORTS = [
    pytest.param("module_a.py", "math", id="module_a imports math"),
    pytest.param("module_a.py", "module_b", id="module_a imports module_b"),
    pytest.param("advanced_imports.py", "math", id="advanced_imports imports math"),
    pytest.param("advanced_imports.py", "random", id="advanced_imports imports random"),
    pytest.param("advanced_imports.py", "sys", id="advanced_imports imports sys"),
    pytest.param("async_features.py", "asyncio", id="async_features imports asyncio"),
    pytest.param("circular1.py", "circular2", id="circular1 imports circular2"),
    pytest.param("circular2.py", "circular1", id="circular2 imports circular1"),
]

EXPECTED_PARAMETERS = [
    pytest.param("foo", "module_a.py", "x", id="foo has parameter x"),
    pytest.param("helper", "module_b.py", "x", id="helper has parameter x"),
    pytest.param("process_data", "module_b.py", "data", id="process_data has parameter data"),
    pytest.param("factorial", "module_b.py", "n", id="factorial has parameter n"),
    pytest.param("square", "advanced_calls.py", "x", id="square has parameter x"),
    pytest.param("method", "advanced_calls.py", "x", id="Dummy.method has parameter x"),
    pytest.param("with_defaults", "advanced_functions.py", "a", id="with_defaults has parameter a"),
    pytest.param("with_defaults", "advanced_functions.py", "b", id="with_defaults has parameter b"),
    pytest.param("with_defaults", "advanced_functions.py", "c", id="with_defaults has parameter c"),
    pytest.param("higher_order", "advanced_functions.py", "func", id="higher_order has parameter func"),
    pytest.param("higher_order", "advanced_functions.py", "data", id="higher_order has parameter data"),
    pytest.param("return_function", "advanced_functions.py", "x", id="return_function has parameter x"),
    pytest.param("executor", "callbacks_decorators.py", "func", id="executor has parameter func"),
    pytest.param("executor", "callbacks_decorators.py", "val", id="executor has parameter val"),
    pytest.param("square", "callbacks_decorators.py", "x", id="square has parameter x"),
    pytest.param("log_decorator", "callbacks_decorators.py", "fn", id="log_decorator has parameter fn"),
    pytest.param("hello", "callbacks_decorators.py", "name", id="hello has parameter name"),
    pytest.param("greet", "class_instantiation.py", "self", id="A.greet has parameter self"),
    pytest.param("greet", "class_instantiation.py", "self", id="B.greet has parameter self"),
    pytest.param("step1", "class_instantiation.py", "self", id="Fluent.step1 has parameter self"),
    pytest.param("step2", "class_instantiation.py", "self", id="Fluent.step2 has parameter self"),
    pytest.param("step3", "class_instantiation.py", "self", id="Fluent.step3 has parameter self"),
]

EXPECTED_CLASS_METHODS = [
    pytest.param("A", "advanced_classes.py", "foo", id="A contains foo"),
    pytest.param("B", "advanced_classes.py", "foo", id="B contains foo"),
    pytest.param("C", "advanced_classes.py", "bar", id="C contains bar"),
    pytest.param("AbstractThing", "advanced_classes.py", "do", id="AbstractThing contains do"),
    pytest.param("ConcreteThing", "advanced_classes.py", "do", id="ConcreteThing contains do"),
    pytest.param("Dummy", "advanced_calls.py", "method", id="Dummy contains method"),
    pytest.param("Mixin1", "advanced_classes2.py", "m1", id="Mixin1 contains m1"),
    pytest.param("Mixin2", "advanced_classes2.py", "m2", id="Mixin2 contains m2"),
    pytest.param("Combined", "advanced_classes2.py", "both", id="Combined contains both"),
    pytest.param("Point", "advanced_classes2.py", "magnitude", id="Point contains magnitude"),
    pytest.param("Color", "advanced_classes2.py", "is_primary", id="Color contains is_primary"),
    pytest.param("A", "class_instantiation.py", "greet", id="A contains greet"),
    pytest.param("B", "class_instantiation.py", "greet", id="B contains greet"),
    pytest.param("Fluent", "class_instantiation.py", "step1", id="Fluent contains step1"),
    pytest.param("Fluent", "class_instantiation.py", "step2", id="Fluent contains step2"),
    pytest.param("Fluent", "class_instantiation.py", "step3", id="Fluent contains step3"),
]

EXPECTED_FUNCTION_CONTAINS = [
    pytest.param("return_function", "advanced_functions.py", "inner", id="return_function contains inner"),
    pytest.param("log_decorator", "callbacks_decorators.py", "wrapper", id="log_decorator contains wrapper"),
]


# ==============================================================================
# == TEST IMPLEMENTATIONS
# ==============================================================================

def check_query(graph, query, description):
    """Helper function to execute a Cypher query and assert that a match is found."""
    try:
        result = graph.query(query)
    except Exception as e:
        pytest.fail(f"Query failed for {description} with error: {e}\nQuery was:\n{query}")

    assert result is not None, f"Query for {description} returned None.\nQuery was:\n{query}"
    assert len(result) > 0, f"Query for {description} returned no records.\nQuery was:\n{query}"
    assert result[0].get('count', 0) > 0, f"No match found for {description}.\nQuery was:\n{query}"

@pytest.mark.parametrize("file_name, item_name, item_label", EXPECTED_STRUCTURE)
def test_file_contains_item(graph, file_name, item_name, item_label):
    """Verifies that a File node correctly CONTAINS a Function or Class node."""
    description = f"CONTAINS from [{file_name}] to [{item_name}]"
    abs_file_path = os.path.join(SAMPLE_PROJECT_PATH, file_name)
    query = f"""
    MATCH (f:File {{path: '{abs_file_path}'}})-[:CONTAINS]->(item:{item_label} {{name: '{item_name}'}})
    RETURN count(*) AS count
    """
    check_query(graph, query, description)

@pytest.mark.parametrize("child_name, child_file, parent_name, parent_file", EXPECTED_INHERITANCE)
def test_inheritance_relationship(graph, child_name, child_file, parent_name, parent_file):
    """Verifies that an INHERITS relationship exists between two classes."""
    description = f"INHERITS from [{child_name}] to [{parent_name}]"
    child_path = os.path.join(SAMPLE_PROJECT_PATH, child_file)
    parent_path = os.path.join(SAMPLE_PROJECT_PATH, parent_file)
    query = f"""
    MATCH (child:Class {{name: '{child_name}', file_path: '{child_path}'}})-[:INHERITS]->(parent:Class {{name: '{parent_name}', file_path: '{parent_path}'}})
    RETURN count(*) as count
    """
    check_query(graph, query, description)

@pytest.mark.parametrize("caller_name, caller_file, caller_class, callee_name, callee_file, callee_class", EXPECTED_CALLS)
def test_function_call_relationship(graph, caller_name, caller_file, caller_class, callee_name, callee_file, callee_class):
    """Verifies that a CALLS relationship exists by checking for nodes first, then the relationship."""
    caller_path = os.path.join(SAMPLE_PROJECT_PATH, caller_file)
    callee_path = os.path.join(SAMPLE_PROJECT_PATH, callee_file)

    # Build match clauses for caller and callee
    if caller_class:
        caller_match = f"(caller_class:Class {{name: '{caller_class}', file_path: '{caller_path}'}})-[:CONTAINS]->(caller:Function {{name: '{caller_name}'}})"
    else:
        caller_match = f"(caller:Function {{name: '{caller_name}', file_path: '{caller_path}'}})"

    if callee_class:
        callee_match = f"(callee_class:Class {{name: '{callee_class}', file_path: '{callee_path}'}})-[:CONTAINS]->(callee:Function {{name: '{callee_name}'}})"
    else:
        callee_match = f"(callee:Function {{name: '{callee_name}', file_path: '{callee_path}'}})"

    # 1. Check that the caller node exists
    caller_description = f"existence of caller {caller_class or 'Function'} {{name: '{caller_name}'}} in [{caller_file}]"
    caller_query = f"""
    MATCH {caller_match}
    RETURN count(caller) as count
    """
    check_query(graph, caller_query, caller_description)

    # 2. Check that the callee node exists
    callee_description = f"existence of callee {callee_class or 'Function'} {{name: '{callee_name}'}} in [{callee_file}]"
    callee_query = f"""
    MATCH {callee_match}
    RETURN count(callee) as count
    """
    check_query(graph, callee_query, callee_description)

    # 3. Check that the CALLS relationship exists between them
    relationship_description = f"CALLS from [{caller_name}] to [{callee_name}]"
    relationship_query = f"""
    MATCH {caller_match}
    MATCH {callee_match}
    MATCH (caller)-[:CALLS]->(callee)
    RETURN count(*) as count
    """
    check_query(graph, relationship_query, relationship_description)

@pytest.mark.parametrize("file_name, module_name", EXPECTED_IMPORTS)
def test_import_relationship(graph, file_name, module_name):
    """Verifies that an IMPORTS relationship exists between a file and a module."""
    description = f"IMPORTS from [{file_name}] to [{module_name}]"
    abs_file_path = os.path.join(SAMPLE_PROJECT_PATH, file_name)
    query = f"""
    MATCH (f:File {{path: '{abs_file_path}'}})-[:IMPORTS]->(m:Module {{name: '{module_name}'}})
    RETURN count(*) as count
    """
    check_query(graph, query, description)

@pytest.mark.parametrize("function_name, file_name, parameter_name", EXPECTED_PARAMETERS)
def test_parameter_relationship(graph, function_name, file_name, parameter_name):
    """Verifies that a HAS_PARAMETER relationship exists between a function and a parameter."""
    description = f"HAS_PARAMETER from [{function_name}] to [{parameter_name}]"
    abs_file_path = os.path.join(SAMPLE_PROJECT_PATH, file_name)
    query = f"""
    MATCH (f:Function {{name: '{function_name}', file_path: '{abs_file_path}'}})-[:HAS_PARAMETER]->(p:Parameter {{name: '{parameter_name}'}})
    RETURN count(*) as count
    """
    check_query(graph, query, description)

@pytest.mark.parametrize("class_name, file_name, method_name", EXPECTED_CLASS_METHODS)
def test_class_method_relationship(graph, class_name, file_name, method_name):
    """Verifies that a CONTAINS relationship exists between a class and a method."""
    description = f"CONTAINS from [{class_name}] to [{method_name}]"
    abs_file_path = os.path.join(SAMPLE_PROJECT_PATH, file_name)
    query = f"""
    MATCH (c:Class {{name: '{class_name}', file_path: '{abs_file_path}'}})-[:CONTAINS]->(m:Function {{name: '{method_name}'}})
    RETURN count(*) as count
    """
    check_query(graph, query, description)

@pytest.mark.parametrize("outer_function_name, file_name, inner_function_name", EXPECTED_FUNCTION_CONTAINS)
def test_function_contains_relationship(graph, outer_function_name, file_name, inner_function_name):
    """Verifies that a CONTAINS relationship exists between an outer function and an inner function."""
    description = f"CONTAINS from [{outer_function_name}] to [{inner_function_name}]"
    abs_file_path = os.path.join(SAMPLE_PROJECT_PATH, file_name)
    query = f"""
    MATCH (outer:Function {{name: '{outer_function_name}', file_path: '{abs_file_path}'}})-[:CONTAINS]->(inner:Function {{name: '{inner_function_name}'}})
    RETURN count(*) as count
    """
    check_query(graph, query, description)
