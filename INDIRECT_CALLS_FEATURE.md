# Indirect Function Calls Feature

## Summary

I've successfully added support for **indirect (transitive) function calls** to the `cgc analyze calls` command. This allows you to trace not just direct function calls, but also the entire chain of indirect calls up to a configurable depth.

## Changes Made

### 1. CLI Command Updates (`src/codegraphcontext/cli/main.py`)

Added two new flags to the `analyze calls` command:
- `--indirect` / `-i`: Enable indirect call tracing
- `--depth` / `-d`: Set maximum depth for indirect calls (default: 3)

**Usage Examples:**
```bash
# Direct calls only (original behavior)
cgc analyze calls process_data

# Indirect calls with default depth (3)
cgc analyze calls process_data --indirect

# Indirect calls with custom depth
cgc analyze calls process_data --indirect --depth 5

# With file filter
cgc analyze calls process_data --file src/main.py --indirect
```

### 2. New Method in CodeFinder (`src/codegraphcontext/tools/code_finder.py`)

Added `what_does_function_call_indirect()` method that:
- Uses Cypher variable-length path matching: `[:CALLS*1..{max_depth}]`
- Returns all functions reachable within the specified depth
- Includes depth information for each called function
- Limits results to 100 functions (vs 20 for direct calls)

**Key Features:**
- Traverses the call graph transitively
- Shows depth level for each called function
- Maintains ordering by depth, then dependency status, then name
- Works with or without file path filtering

### 3. Updated Display

The output table now includes:
- **Called Function**: Name of the called function
- **Location**: File path and line number
- **Depth**: How many hops away (only shown with `--indirect`)
- **Type**: Whether it's a project function or dependency

The header also indicates when indirect mode is active:
```
Function 'main' calls (indirect, depth ≤ 3):
```

### 4. Documentation Updates

Updated both:
- `CLI_Commands.md`
- `docs/docs/cli.md`

To reflect the new flags and functionality.

## Example Use Case

Given this call chain:
```
main() → level_1_function() → level_2_function() → level_3_function()
```

**Direct calls** (`cgc analyze calls main`):
- Shows only: `level_1_function` (depth 1)

**Indirect calls** (`cgc analyze calls main --indirect --depth 3`):
- Shows:
  - `level_1_function` (depth 1)
  - `level_2_function` (depth 2)
  - `level_3_function` (depth 3)

## Testing

I've created `example_indirect_calls.py` in your workspace to demonstrate the feature. After indexing this file, you can test:

```bash
# Index the example file
cgc index example_indirect_calls.py

# Test direct calls
cgc analyze calls main

# Test indirect calls
cgc analyze calls main --indirect --depth 3
```

## Technical Details

The implementation uses Cypher's variable-length path syntax:
```cypher
MATCH path = (caller)-[:CALLS*1..{max_depth}]->(called:Function)
WITH called, length(path) as depth
```

This efficiently traverses the call graph and returns the shortest path to each reachable function, along with the depth information.

## Benefits

1. **Better Code Understanding**: See the full impact of a function's execution
2. **Dependency Analysis**: Understand transitive dependencies
3. **Refactoring Safety**: Know all functions affected by changes
4. **Performance Analysis**: Identify deep call chains that might impact performance
5. **Testing Coverage**: Ensure tests cover indirect call paths

## Backward Compatibility

The feature is fully backward compatible:
- Default behavior (without `--indirect`) remains unchanged
- Existing scripts and workflows continue to work
- The `--depth` flag is only used when `--indirect` is specified
