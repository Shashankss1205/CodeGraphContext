
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
    ("function_chains.py", "f1", "Function"),
    ("function_chains.py", "f2", "Function"),
    ("function_chains.py", "f3", "Function"),
    ("function_chains.py", "make_adder", "Function"),
    ("generators.py", "gen_numbers", "Function"),
    ("generators.py", "agen_numbers", "Function"),
    ("generators.py", "async_with_example", "Function"),
    ("generators.py", "AsyncCM", "Class"),
    ("datatypes.py", "Point", "Class"),
    ("datatypes.py", "Color", "Class"),
    ("complex_classes.py", "Base", "Class"),
    ("complex_classes.py", "Child", "Class"),
    ("complex_classes.py", "decorator", "Function"),
    ("complex_classes.py", "decorated_function", "Function"),
    ("control_flow.py", "choose_path", "Function"),
    ("control_flow.py", "ternary", "Function"),
    ("control_flow.py", "try_except_finally", "Function"),
    ("control_flow.py", "conditional_inner_import", "Function"),
    ("control_flow.py", "env_based_import", "Function"),
    ("circular1.py", "func1", "Function"),
    ("circular2.py", "func2", "Function"),
    ("cli_and_dunder.py", "run", "Function"),
    ("comprehensions_generators.py", "double", "Function"),
    ("context_managers.py", "FileOpener", "Class"),
    ("context_managers.py", "use_file", "Function"),
    ("dynamic_dispatch.py", "add", "Function"),
    ("dynamic_dispatch.py", "sub", "Function"),
    ("dynamic_dispatch.py", "mul", "Function"),
    ("dynamic_dispatch.py", "dispatch_by_key", "Function"),
    ("dynamic_dispatch.py", "dispatch_by_string", "Function"),
    ("dynamic_dispatch.py", "partial_example", "Function"),
    ("dynamic_dispatch.py", "C", "Class"),
    ("dynamic_dispatch.py", "methodcaller_example", "Function"),
    ("dynamic_dispatch.py", "dynamic_import_call", "Function"),
    ("dynamic_imports.py", "import_optional", "Function"),
    ("dynamic_imports.py", "import_by___import__", "Function"),
    ("dynamic_imports.py", "importlib_runtime", "Function"),
    ("import_reexports.py", "core_function", "Function"),
    ("import_reexports.py", "reexport", "Function"),
    ("mapping_calls.py", "Dispatcher", "Class"),
    ("mapping_calls.py", "use_dispatcher", "Function"),
    ("module_c/submodule1.py", "call_helper_twice", "Function"),
    ("module_c/submodule2.py", "wrapper", "Function"),
    ("namespace_pkg/ns_module.py", "ns_func", "Function"),
    ("pattern_matching.py", "matcher", "Function"),
    ("typing_examples.py", "typed_func", "Function"),
    ("typing_examples.py", "union_func", "Function"),
    ("typing_examples.py", "dict_func", "Function"),
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
    pytest.param("Child", "complex_classes.py", "Base", "complex_classes.py", id="Child inherits from Base"),
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
    pytest.param("greet", "complex_classes.py", "Child", "greet", "complex_classes.py", "Base", marks=pytest.mark.skip(reason="super() calls are not supported yet"), id="Child.greet->Base.greet"),
    pytest.param("class_method", "complex_classes.py", "Child", "greet", "complex_classes.py", "Child", id="Child.class_method->Child.greet"),
    pytest.param("use_file", "context_managers.py", None, "__enter__", "context_managers.py", "FileOpener", marks=pytest.mark.skip(reason="Implicit context manager calls not supported"), id="use_file->FileOpener.__enter__"),
    pytest.param("partial_example", "dynamic_dispatch.py", None, "add", "dynamic_dispatch.py", None, marks=pytest.mark.skip(reason="Calls via functools.partial not supported yet"), id="partial_example->add"),
    pytest.param("async_with_example", "generators.py", None, "__aenter__", "generators.py", "AsyncCM", marks=pytest.mark.skip(reason="Implicit async context manager calls not supported"), id="async_with_example->AsyncCM.__aenter__"),
    pytest.param("call", "mapping_calls.py", "Dispatcher", "start", "mapping_calls.py", "Dispatcher", marks=pytest.mark.skip(reason="Dynamic call via dict lookup not supported"), id="Dispatcher.call->start"),
    pytest.param("greet", "class_instantiation.py", None, "greet", "class_instantiation.py", "A", marks=pytest.mark.skip(reason="Indexer does not capture calls to methods of instantiated objects within the same file"), id="A.greet called"),
    pytest.param("greet", "class_instantiation.py", None, "greet", "class_instantiation.py", "B", marks=pytest.mark.skip(reason="Indexer does not capture calls to methods of instantiated objects within the same file"), id="B.greet called"),
    pytest.param("step1", "class_instantiation.py", "Fluent", "step1", "class_instantiation.py", "Fluent", marks=pytest.mark.skip(reason="Indexer does not capture method chaining calls"), id="Fluent.step1 called"),
    pytest.param("step2", "class_instantiation.py", "Fluent", "step2", "class_instantiation.py", "Fluent", marks=pytest.mark.skip(reason="Indexer does not capture method chaining calls"), id="Fluent.step2 called"),
    pytest.param("step3", "class_instantiation.py", "Fluent", "step3", "class_instantiation.py", "Fluent", marks=pytest.mark.skip(reason="Indexer does not capture method chaining calls"), id="Fluent.step3 called"),
    pytest.param("dynamic", "class_instantiation.py", "B", "lambda", "class_instantiation.py", None, marks=pytest.mark.skip(reason="Dynamic attribute assignment and lambda calls not supported"), id="B.dynamic called"),
    pytest.param("add_argument", "cli_and_dunder.py", None, "add_argument", None, None, marks=pytest.mark.skip(reason="Calls to external library methods not fully supported"), id="ArgumentParser.add_argument called"),
    pytest.param("parse_args", "cli_and_dunder.py", None, "parse_args", None, None, marks=pytest.mark.skip(reason="Calls to external library methods not fully supported"), id="ArgumentParser.parse_args called"),
    pytest.param("print", "cli_and_dunder.py", None, "print", None, None, marks=pytest.mark.skip(reason="Built-in function calls not explicitly indexed"), id="print called"),
    pytest.param("double", "comprehensions_generators.py", None, "double", "comprehensions_generators.py", None, marks=pytest.mark.skip(reason="Indexer does not capture calls within comprehensions/generators"), id="double called in list comprehension"),
    pytest.param("range", "comprehensions_generators.py", None, "range", None, None, marks=pytest.mark.skip(reason="Built-in function calls not explicitly indexed"), id="range called in list comprehension"),
    pytest.param("double", "comprehensions_generators.py", None, "double", "comprehensions_generators.py", None, marks=pytest.mark.skip(reason="Indexer does not capture calls within comprehensions/generators"), id="double called in generator expression"),
    pytest.param("range", "comprehensions_generators.py", None, "range", None, None, marks=pytest.mark.skip(reason="Built-in function calls not explicitly indexed"), id="range called in generator expression"),
    pytest.param("list", "comprehensions_generators.py", None, "list", None, None, marks=pytest.mark.skip(reason="Built-in function calls not explicitly indexed"), id="list called"),
    pytest.param("sorted", "comprehensions_generators.py", None, "sorted", None, None, marks=pytest.mark.skip(reason="Built-in function calls not explicitly indexed"), id="sorted called"),
    pytest.param("len", "comprehensions_generators.py", None, "len", None, None, marks=pytest.mark.skip(reason="Built-in function calls not explicitly indexed"), id="len called"),
    pytest.param("open", "comprehensions_generators.py", None, "open", None, None, marks=pytest.mark.skip(reason="Built-in function calls not explicitly indexed"), id="open called for write"),
    pytest.param("write", "comprehensions_generators.py", None, "write", None, None, marks=pytest.mark.skip(reason="Method calls on built-in types not explicitly indexed"), id="write called"),
    pytest.param("open", "comprehensions_generators.py", None, "open", None, None, marks=pytest.mark.skip(reason="Built-in function calls not explicitly indexed"), id="open called for read"),
    pytest.param("read", "comprehensions_generators.py", None, "read", None, None, marks=pytest.mark.skip(reason="Method calls on built-in types not explicitly indexed"), id="read called"),
    pytest.param("ValueError", "control_flow.py", None, "ValueError", None, None, marks=pytest.mark.skip(reason="Built-in exception constructors not explicitly indexed"), id="ValueError called"),
    pytest.param("str", "control_flow.py", None, "str", None, None, marks=pytest.mark.skip(reason="Built-in type constructors not explicitly indexed"), id="str called"),
    pytest.param("getenv", "control_flow.py", None, "getenv", None, None, marks=pytest.mark.skip(reason="Calls to external library methods not fully supported"), id="os.getenv called"),
    pytest.param("dumps", "control_flow.py", None, "dumps", None, None, marks=pytest.mark.skip(reason="Calls to external library methods not fully supported"), id="json.dumps called"),
    pytest.param("namedtuple", "datatypes.py", None, "namedtuple", None, None, marks=pytest.mark.skip(reason="Calls to external library functions not fully supported"), id="namedtuple called"),
    pytest.param("DISPATCH", "dynamic_dispatch.py", None, "add", "dynamic_dispatch.py", None, marks=pytest.mark.skip(reason="Dynamic dispatch via dictionary lookup not supported"), id="dispatch_by_key calls add dynamically"),
    pytest.param("DISPATCH", "dynamic_dispatch.py", None, "sub", "dynamic_dispatch.py", None, marks=pytest.mark.skip(reason="Dynamic dispatch via dictionary lookup not supported"), id="dispatch_by_key calls sub dynamically"),
    pytest.param("DISPATCH", "dynamic_dispatch.py", None, "mul", "dynamic_dispatch.py", None, marks=pytest.mark.skip(reason="Dynamic dispatch via dictionary lookup not supported"), id="dispatch_by_key calls mul dynamically"),
    pytest.param("get", "dynamic_dispatch.py", None, "get", None, None, marks=pytest.mark.skip(reason="Calls to built-in dictionary methods not explicitly indexed"), id="globals().get called"),
    pytest.param("callable", "dynamic_dispatch.py", None, "callable", None, None, marks=pytest.mark.skip(reason="Built-in function calls not explicitly indexed"), id="callable called"),
    pytest.param("partial", "dynamic_dispatch.py", None, "partial", None, None, marks=pytest.mark.skip(reason="Calls to external library functions not fully supported"), id="partial called"),
    pytest.param("methodcaller", "dynamic_dispatch.py", None, "methodcaller", None, None, marks=pytest.mark.skip(reason="Calls to external library functions not fully supported"), id="methodcaller called"),
    pytest.param("method", "dynamic_dispatch.py", "C", "method", "dynamic_dispatch.py", "C", marks=pytest.mark.skip(reason="Dynamic call via operator.methodcaller not supported"), id="C.method called via methodcaller"),
    pytest.param("import_module", "dynamic_dispatch.py", None, "import_module", None, None, marks=pytest.mark.skip(reason="Calls to external library functions not fully supported"), id="importlib.import_module called"),
    pytest.param("getattr", "dynamic_dispatch.py", None, "getattr", None, None, marks=pytest.mark.skip(reason="Built-in function calls not explicitly indexed"), id="getattr called"),
    pytest.param("dumps", "dynamic_imports.py", None, "dumps", None, None, marks=pytest.mark.skip(reason="Calls to external library methods not fully supported"), id="json.dumps called in import_optional"),
    pytest.param("__import__", "dynamic_imports.py", None, "__import__", None, None, marks=pytest.mark.skip(reason="Built-in function calls not explicitly indexed"), id="__import__ called"),
    pytest.param("getattr", "dynamic_imports.py", None, "getattr", None, None, marks=pytest.mark.skip(reason="Built-in function calls not explicitly indexed"), id="getattr called in import_by___import__"),
    pytest.param("import_module", "dynamic_imports.py", None, "import_module", None, None, marks=pytest.mark.skip(reason="Calls to external library functions not fully supported"), id="importlib.import_module called in importlib_runtime"),
    pytest.param("getattr", "dynamic_imports.py", None, "getattr", None, None, marks=pytest.mark.skip(reason="Built-in function calls not explicitly indexed"), id="getattr called in importlib_runtime"),
    pytest.param("f3", "function_chains.py", None, "f3", "function_chains.py", None, marks=pytest.mark.skip(reason="Indexer does not capture chained function calls"), id="f3 called"),
    pytest.param("f2", "function_chains.py", None, "f2", "function_chains.py", None, marks=pytest.mark.skip(reason="Indexer does not capture chained function calls"), id="f2 called"),
    pytest.param("f1", "function_chains.py", None, "f1", "function_chains.py", None, marks=pytest.mark.skip(reason="Indexer does not capture chained function calls"), id="f1 called"),
    pytest.param("strip", "function_chains.py", None, "strip", None, None, marks=pytest.mark.skip(reason="Method calls on built-in types not explicitly indexed"), id="strip called"),
    pytest.param("lower", "function_chains.py", None, "lower", None, None, marks=pytest.mark.skip(reason="Method calls on built-in types not explicitly indexed"), id="lower called"),
    pytest.param("replace", "function_chains.py", None, "replace", None, None, marks=pytest.mark.skip(reason="Method calls on built-in types not explicitly indexed"), id="replace called"),
    pytest.param("make_adder", "function_chains.py", None, "make_adder", "function_chains.py", None, marks=pytest.mark.skip(reason="Indexer does not capture calls to functions that return functions"), id="make_adder called"),
    pytest.param("adder", "function_chains.py", None, "adder", "function_chains.py", None, marks=pytest.mark.skip(reason="Indexer does not capture calls to inner functions returned by other functions"), id="adder called"),
    pytest.param("make_adder", "function_chains.py", None, "make_adder", "function_chains.py", None, marks=pytest.mark.skip(reason="Indexer does not capture calls to functions that return functions in a chain"), id="make_adder called in chain"),
    pytest.param("adder", "function_chains.py", None, "adder", "function_chains.py", None, marks=pytest.mark.skip(reason="Indexer does not capture calls to inner functions returned by other functions in a chain"), id="adder called in chain"),
    pytest.param("sqrt", "import_reexports.py", None, "sqrt", None, None, marks=pytest.mark.skip(reason="Calls to aliased imported functions not fully supported"), id="m.sqrt called"),
    pytest.param("Dispatcher", "mapping_calls.py", None, "Dispatcher", "mapping_calls.py", None, marks=pytest.mark.skip(reason="Indexer does not capture class constructor calls"), id="Dispatcher constructor called"),
    pytest.param("str", "pattern_matching.py", None, "str", None, None, marks=pytest.mark.skip(reason="Built-in type constructors not explicitly indexed"), id="str called in pattern matching"),
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
    pytest.param("cli_and_dunder.py", "argparse", id="cli_and_dunder imports argparse"),
    pytest.param("cli_and_dunder.py", "advanced_functions", id="cli_and_dunder imports advanced_functions"),
    pytest.param("control_flow.py", "os", id="control_flow imports os"),
    pytest.param("datatypes.py", "dataclasses", id="datatypes imports dataclasses"),
    pytest.param("datatypes.py", "enum", id="datatypes imports enum"),
    pytest.param("datatypes.py", "collections", id="datatypes imports collections"),
    pytest.param("dynamic_dispatch.py", "functools", id="dynamic_dispatch imports functools"),
    pytest.param("dynamic_dispatch.py", "operator", id="dynamic_dispatch imports operator"),
    pytest.param("dynamic_dispatch.py", "importlib", id="dynamic_dispatch imports importlib"),
    pytest.param("dynamic_imports.py", "importlib", id="dynamic_imports imports importlib"),
    pytest.param("import_reexports.py", "math", marks=pytest.mark.skip(reason="Indexer does not support aliased imports (e.g., 'import math as m')"), id="import_reexports imports math"),
    pytest.param("module_c/submodule1.py", "module_b", id="submodule1 imports module_b"),
    pytest.param("module_c/submodule2.py", "module_c.submodule1", id="submodule2 imports submodule1"),
    pytest.param("typing_examples.py", "typing", id="typing_examples imports typing"),
    pytest.param("control_flow.py", "numpy", marks=pytest.mark.skip(reason="Indexer does not capture conditional imports"), id="control_flow imports numpy (conditional)"),
    pytest.param("control_flow.py", "ujson", marks=pytest.mark.skip(reason="Indexer does not capture conditional imports"), id="control_flow imports ujson (conditional)"),
    pytest.param("control_flow.py", "json", id="control_flow imports json (conditional)"),
    pytest.param("dynamic_imports.py", "ujson", marks=pytest.mark.skip(reason="Indexer does not capture conditional imports"), id="dynamic_imports imports ujson (conditional)"),
    pytest.param("dynamic_imports.py", "json", id="dynamic_imports imports json (conditional)"),
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
    pytest.param("run", "cli_and_dunder.py", "argv", id="run has parameter argv"),
    pytest.param("greet", "complex_classes.py", "self", id="Base.greet has self"),
    pytest.param("greet", "complex_classes.py", "self", id="Child.greet has self"),
    pytest.param("static_method", "complex_classes.py", "x", id="Child.static_method has x"),
    pytest.param("class_method", "complex_classes.py", "cls", id="Child.class_method has cls"),
    pytest.param("class_method", "complex_classes.py", "y", id="Child.class_method has y"),
    pytest.param("decorator", "complex_classes.py", "func", id="decorator has func"),
    pytest.param("decorated_function", "complex_classes.py", "x", id="decorated_function has x"),
    pytest.param("double", "comprehensions_generators.py", "x", id="double has parameter x"),
    pytest.param("__enter__", "context_managers.py", "self", id="FileOpener.__enter__ has self"),
    pytest.param("__exit__", "context_managers.py", "self", id="FileOpener.__exit__ has self"),
    pytest.param("__exit__", "context_managers.py", "exc_type", id="FileOpener.__exit__ has exc_type"),
    pytest.param("__exit__", "context_managers.py", "exc_val", id="FileOpener.__exit__ has exc_val"),
    pytest.param("__exit__", "context_managers.py", "exc_tb", id="FileOpener.__exit__ has exc_tb"),
    pytest.param("choose_path", "control_flow.py", "x", id="choose_path has parameter x"),
    pytest.param("ternary", "control_flow.py", "x", id="ternary has parameter x"),
    pytest.param("try_except_finally", "control_flow.py", "x", id="try_except_finally has parameter x"),
    pytest.param("conditional_inner_import", "control_flow.py", "use_numpy", id="conditional_inner_import has use_numpy"),
    pytest.param("add", "dynamic_dispatch.py", "a", id="add has a"),
    pytest.param("add", "dynamic_dispatch.py", "b", id="add has b"),
    pytest.param("sub", "dynamic_dispatch.py", "a", id="sub has a"),
    pytest.param("sub", "dynamic_dispatch.py", "b", id="sub has b"),
    pytest.param("mul", "dynamic_dispatch.py", "a", id="mul has a"),
    pytest.param("mul", "dynamic_dispatch.py", "b", id="mul has b"),
    pytest.param("dispatch_by_key", "dynamic_dispatch.py", "name", id="dispatch_by_key has name"),
    pytest.param("dispatch_by_key", "dynamic_dispatch.py", "a", id="dispatch_by_key has a"),
    pytest.param("dispatch_by_key", "dynamic_dispatch.py", "b", id="dispatch_by_key has b"),
    pytest.param("method", "dynamic_dispatch.py", "x", id="C.method has x"),
    pytest.param("methodcaller_example", "dynamic_dispatch.py", "x", id="methodcaller_example has x"),
    pytest.param("import_by___import__", "dynamic_imports.py", "name", id="import_by___import__ has name"),
    pytest.param("importlib_runtime", "dynamic_imports.py", "name", id="importlib_runtime has name"),
    pytest.param("importlib_runtime", "dynamic_imports.py", "attr", id="importlib_runtime has attr"),
    pytest.param("f1", "function_chains.py", "x", id="f1 has x"),
    pytest.param("f2", "function_chains.py", "x", id="f2 has x"),
    pytest.param("f3", "function_chains.py", "x", id="f3 has x"),
    pytest.param("make_adder", "function_chains.py", "n", id="make_adder has n"),
    pytest.param("gen_numbers", "generators.py", "n", id="gen_numbers has n"),
    pytest.param("agen_numbers", "generators.py", "n", id="agen_numbers has n"),
    pytest.param("call", "mapping_calls.py", "cmd", id="Dispatcher.call has cmd"),
    pytest.param("use_dispatcher", "mapping_calls.py", "cmd", id="use_dispatcher has cmd"),
    pytest.param("call_helper_twice", "module_c/submodule1.py", "x", id="call_helper_twice has x"),
    pytest.param("wrapper", "module_c/submodule2.py", "x", id="wrapper has x"),
    pytest.param("matcher", "pattern_matching.py", "x", id="matcher has x"),
    pytest.param("typed_func", "typing_examples.py", "a", marks=pytest.mark.skip(reason="Indexer does not support parameters with type hints"), id="typed_func has a"),
    pytest.param("typed_func", "typing_examples.py", "b", marks=pytest.mark.skip(reason="Indexer does not support parameters with type hints"), id="typed_func has b"),
    pytest.param("union_func", "typing_examples.py", "x", marks=pytest.mark.skip(reason="Indexer does not support parameters with type hints"), id="union_func has x"),
    pytest.param("dict_func", "typing_examples.py", "d", marks=pytest.mark.skip(reason="Indexer does not support parameters with type hints"), id="dict_func has d"),
    pytest.param("wrapper", "complex_classes.py", "*args", marks=pytest.mark.skip(reason="Indexer does not capture variadic parameters (*args)"), id="wrapper has *args"),
    pytest.param("wrapper", "complex_classes.py", "**kwargs", marks=pytest.mark.skip(reason="Indexer does not capture variadic parameters (**kwargs)"), id="wrapper has **kwargs"),
    pytest.param("dispatch_by_string", "dynamic_dispatch.py", "*args", marks=pytest.mark.skip(reason="Indexer does not capture variadic parameters (*args)"), id="dispatch_by_string has *args"),
    pytest.param("dispatch_by_string", "dynamic_dispatch.py", "**kwargs", marks=pytest.mark.skip(reason="Indexer does not capture variadic parameters (**kwargs)"), id="dispatch_by_string has **kwargs"),
    pytest.param("dynamic_import_call", "dynamic_dispatch.py", "*args", marks=pytest.mark.skip(reason="Indexer does not capture variadic parameters (*args)"), id="dynamic_import_call has *args"),
    pytest.param("dynamic_import_call", "dynamic_dispatch.py", "**kwargs", marks=pytest.mark.skip(reason="Indexer does not capture variadic parameters (**kwargs)"), id="dynamic_import_call has **kwargs"),
    pytest.param("adder", "function_chains.py", "x", id="adder has x"),
    pytest.param("__aenter__", "generators.py", "self", id="AsyncCM.__aenter__ has self"),
    pytest.param("__aexit__", "generators.py", "self", id="AsyncCM.__aexit__ has self"),
    pytest.param("__aexit__", "generators.py", "exc_type", id="AsyncCM.__aexit__ has exc_type"),
    pytest.param("__aexit__", "generators.py", "exc_val", id="AsyncCM.__aexit__ has exc_val"),
    pytest.param("__aexit__", "generators.py", "exc_tb", id="AsyncCM.__aexit__ has exc_tb"),
    pytest.param("__init__", "mapping_calls.py", "self", id="Dispatcher.__init__ has self"),
    pytest.param("start", "mapping_calls.py", "self", id="Dispatcher.start has self"),
    pytest.param("stop", "mapping_calls.py", "self", id="Dispatcher.stop has self"),
    pytest.param("ns_func", "namespace_pkg/ns_module.py", None, marks=pytest.mark.skip(reason="Functions with no parameters are not explicitly tested for parameter existence"), id="ns_func has no parameters"),
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
    pytest.param("AsyncCM", "generators.py", "__aenter__", id="AsyncCM contains __aenter__"),
    pytest.param("AsyncCM", "generators.py", "__aexit__", id="AsyncCM contains __aexit__"),
    pytest.param("Base", "complex_classes.py", "greet", id="Base contains greet"),
    pytest.param("Child", "complex_classes.py", "greet", id="Child contains greet"),
    pytest.param("Child", "complex_classes.py", "static_method", id="Child contains static_method"),
    pytest.param("Child", "complex_classes.py", "class_method", id="Child contains class_method"),
    pytest.param("FileOpener", "context_managers.py", "__enter__", id="FileOpener contains __enter__"),
    pytest.param("FileOpener", "context_managers.py", "__exit__", id="FileOpener contains __exit__"),
    pytest.param("C", "dynamic_dispatch.py", "method", id="C contains method"),
    pytest.param("Dispatcher", "mapping_calls.py", "__init__", id="Dispatcher contains __init__"),
    pytest.param("Dispatcher", "mapping_calls.py", "start", id="Dispatcher contains start"),
    pytest.param("Dispatcher", "mapping_calls.py", "stop", id="Dispatcher contains stop"),
    pytest.param("Dispatcher", "mapping_calls.py", "call", id="Dispatcher contains call"),
]

EXPECTED_FUNCTION_CONTAINS = [
    pytest.param("return_function", "advanced_functions.py", "inner", id="return_function contains inner"),
    pytest.param("log_decorator", "callbacks_decorators.py", "wrapper", id="log_decorator contains wrapper"),
    pytest.param("make_adder", "function_chains.py", "adder", id="make_adder contains adder"),
    pytest.param("decorator", "complex_classes.py", "wrapper", id="decorator contains wrapper"),
]

EXPECTED_DECORATORS = [
    pytest.param("decorated_function", "complex_classes.py", "decorator", "complex_classes.py", id="decorated_function decorated by decorator"),
    pytest.param("hello", "callbacks_decorators.py", "log_decorator", "callbacks_decorators.py", id="hello decorated by log_decorator"),
]

EXPECTED_EMPTY_FILES = [
    pytest.param("edge_cases/comments_only.py", id="comments_only.py is empty"),
    pytest.param("edge_cases/docstring_only.py", id="docstring_only.py is empty"),
    pytest.param("edge_cases/empty.py", id="empty.py is empty"),
    pytest.param("edge_cases/syntax_error.py", marks=pytest.mark.skip(reason="File with syntax error should be skipped or handled gracefully"), id="syntax_error.py is skipped"),
    pytest.param("module_c/__init__.py", id="module_c/__init__.py is empty"),
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
