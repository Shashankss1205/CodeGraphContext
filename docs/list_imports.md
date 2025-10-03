## list_imports Tool Guide

The `list_imports` tool scans a directory (or a single file) and returns a de-duplicated list of imported packages/modules for a supported language.

### Supported Languages & File Extensions
| Language    | Extensions                          | Notes |
|------------|--------------------------------------|-------|
| python      | .py                                  | Relative imports (e.g. `from . import x`) are ignored. Returns both stdlib & third-party when invoked via the MCP server. |
| javascript  | .js, .jsx, .mjs                      | Ignores relative (`./` or `../`) paths; keeps package / first segment (e.g. `react`, `@scope/pkg`). |
| typescript  | .ts, .tsx                            | Same extraction logic as JavaScript. |
| java        | .java                                | Captures the first two segments (e.g. `java.util`). |

> NOTE: The internal utility class `ImportExtractor` (used in tests or direct Python usage) filters out Python stdlib modules in its own `list_imports_tool` method, but the exposed MCP server `list_imports` tool does **not** currently filter them (the filtering code was commented out). This means you may see items like `os`, `sys`, `json` in results when calling the tool through an AI client.

### When to Use
Use this tool to quickly:
1. Understand external dependencies in an unfamiliar repo.
2. Spot unexpected libraries or duplicated dependency surfaces.
3. Generate a starting list for dependency auditing or SBOM enrichment.

### Arguments
| Name       | Type    | Required | Default  | Description |
|------------|---------|----------|----------|-------------|
| `path`     | string  | Yes      | —        | Directory or file path to scan. |
| `language` | string  | No       | `python` | One of: `python`, `javascript`, `typescript`, `java`. Determines which extensions and parser to use. |
| `recursive`| boolean | No       | `true`   | If `true`, walks subdirectories; otherwise only the top level (or the file itself). |

### Output Shape
```json
{
  "imports": ["requests", "rich", "watchdog"],
  "language": "python",
  "path": "/abs/path/to/project",
  "count": 3
}
```

### Example (Python Project)
Natural Language prompt to your AI client:
> List all Python package imports from the tests/sample_project directory.

Underlying tool invocation:
```json
{
  "path": "<repo_root>/tests/sample_project",
  "language": "python"
}
```

Possible (abridged) output:
```json
{
  "imports": [
    "asyncio", "collections", "contextlib", "dataclasses", "functools", "importlib", "itertools",
    "json", "math", "os", "pathlib", "sys", "typing"
  ],
  "language": "python",
  "path": ".../tests/sample_project",
  "count": 13
}
```

### Example (JavaScript / TypeScript)
```json
{
  "path": "<repo_root>/sample_project_javascript",
  "language": "javascript"
}
```
Returns only package / scope roots (e.g. `react`, `lodash`, `@scope/pkg`). Relative imports such as `./utils/helpers.js` are ignored.

### Edge Cases & Notes
1. Empty directory → returns `imports: []`, `count: 0`.
2. Mixed-language repos: run the tool multiple times with different `language` values; it does not auto-detect.
3. Vendored or copied third-party code inside your tree will be scanned like first-party; if you want to exclude, run on a narrower path.
4. For Python, if you only want third-party packages, post-filter by removing modules that appear in `stdlibs.module_names` (the filtering is intentionally disabled at the server layer currently).
5. Symlinks are followed implicitly by `Path.glob`; ensure you are not unintentionally scanning huge dependency directories.

### Using Directly in Python (Advanced)
If you are scripting inside this repository and want the filtered (third-party only) behavior:
```python
from codegraphcontext.tools.import_extractor import ImportExtractor
imports = ImportExtractor().list_imports_tool(path="tests/sample_project")
print(imports)
```
That internal helper currently subtracts standard library names for Python.

### Troubleshooting
| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `{"error": "Path ... does not exist"}` | Wrong relative path | Use an absolute path or confirm working directory. |
| Missing expected imports | They are relative (`./`, `../`) or inside unsupported language extension | Confirm file extensions and that imports are not local relative modules. |
| Large `count` with many stdlib names | Expected: server version keeps stdlib | Post-filter if you only need third-party dependencies. |

### Roadmap Suggestions (If You Want to Contribute Further)
* Add optional flag `exclude_stdlib` (default `false`).
* Add language autodetection when `language` omitted.
* Provide a `--format requirements` mode to emit a requirements-style guess for Python.

---
If you improve this tool or add the optional flags above, update this document accordingly.
