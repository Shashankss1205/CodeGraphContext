# CRITICAL: Tree-sitter 0.25+ API Breaking Changes

## Status: Migration Partially Complete ⚠️

The migration from `tree-sitter-languages` to `tree-sitter-language-pack` is **functionally complete** for the infrastructure layer, but there are **breaking API changes** in tree-sitter 0.25+ that affect query execution throughout the codebase.

## What's Working ✅

1. **Tree-sitter Manager** (`tree_sitter_manager.py`)
   - Language caching
   - Parser creation with new API
   - Thread safety
   - Language aliasing
   - All tests passing (15/15)

2. **Dependencies**
   - `pyproject.toml` updated
   - Python 3.9+ support (including 3.13, 3.14)
   - New packages installed successfully

3. **Graph Builder** (`graph_builder.py`)
   - Updated to use new manager
   - Parser creation working

## What's Broken ❌

### Query API Changes

**Old API (tree-sitter 0.20.x):**
```python
query = language.query(query_string)
captures = query.captures(node)
```

**New API (tree-sitter 0.25.x):**
```python
from tree_sitter import Query, QueryCursor

query = Query(language, query_string)
cursor = QueryCursor(query)
matches = cursor.matches(node)
# OR
captures = cursor.captures(node)
```

### Affected Files

All language-specific parsers need updates:
- `/src/codegraphcontext/tools/languages/python.py`
- `/src/codegraphcontext/tools/languages/javascript.py`
- `/src/codegraphcontext/tools/languages/typescript.py`
- `/src/codegraphcontext/tools/languages/go.py`
- `/src/codegraphcontext/tools/languages/rust.py`
- `/src/codegraphcontext/tools/languages/c.py`
- `/src/codegraphcontext/tools/languages/cpp.py`
- `/src/codegraphcontext/tools/languages/java.py`
- `/src/codegraphcontext/tools/languages/ruby.py`
- `/src/codegraphcontext/tools/languages/csharp.py`

### Example Fix Needed

**Before:**
```python
query = self.language.query(PYTHON_QUERIES)
captures = query.captures(node)
for capture in captures:
    node, capture_name = capture
    # process...
```

**After:**
```python
from tree_sitter import Query, QueryCursor

query = Query(self.language, PYTHON_QUERIES)
cursor = QueryCursor(query)
matches = cursor.matches(node)
for pattern_index, captures_dict in matches:
    for capture_name, nodes in captures_dict.items():
        for node in nodes:
            # process...
```

## Decision Point 🤔

You have two options:

### Option 1: Complete the Migration (Recommended for Long-term)
**Pros:**
- Full Python 3.13+ support
- Future-proof
- Better performance
- Cleaner architecture

**Cons:**
- Requires updating all 10 language parsers
- Significant testing needed
- Potential for subtle bugs during transition

**Estimated Effort:** 4-6 hours to update all parsers + testing

### Option 2: Rollback to tree-sitter 0.20.x
**Pros:**
- Immediate functionality restored
- No code changes needed
- Lower risk

**Cons:**
- ❌ No Python 3.13+ support
- ❌ Stuck on deprecated packages
- ❌ Will need to migrate eventually anyway

**How to Rollback:**
```bash
pip uninstall tree-sitter tree-sitter-language-pack tree-sitter-c-sharp
pip install tree-sitter==0.20.4 tree-sitter-languages==1.10.2
git checkout pyproject.toml README.md
git checkout src/codegraphcontext/tools/graph_builder.py
rm src/codegraphcontext/utils/tree_sitter_manager.py
```

## Recommended Path Forward

I recommend **Option 1** with a phased approach:

### Phase 1: Create Query Helper (30 minutes)
Create a compatibility layer in `tree_sitter_manager.py`:

```python
def execute_query(language: Language, query_string: str, node):
    """Execute a tree-sitter query and return captures in old format."""
    from tree_sitter import Query, QueryCursor
    
    query = Query(language, query_string)
    cursor = QueryCursor(query)
    
    # Convert new format to old format for backward compatibility
    captures = []
    for pattern_index, captures_dict in cursor.matches(node):
        for capture_name, nodes in captures_dict.items():
            for captured_node in nodes:
                captures.append((captured_node, capture_name))
    
    return captures
```

### Phase 2: Update Language Parsers (3-4 hours)
Update each language parser to use the helper function:

```python
# Old:
# captures = self.language.query(PYTHON_QUERIES).captures(node)

# New:
from ..utils.tree_sitter_manager import execute_query
captures = execute_query(self.language, PYTHON_QUERIES, node)
```

### Phase 3: Test Everything (1-2 hours)
- Run existing test suite
- Test each language parser individually
- Verify graph building works end-to-end

## Current State Summary

✅ **Infrastructure:** Complete and tested  
✅ **Dependencies:** Updated and working  
✅ **Python 3.13+ Support:** Enabled  
❌ **Query Execution:** Needs updates in all language parsers  
❌ **End-to-End Functionality:** Broken until parsers are updated  

## Files Created in This Migration

1. `/src/codegraphcontext/utils/tree_sitter_manager.py` - Core manager (WORKING)
2. `/docs/TREE_SITTER_MIGRATION.md` - User guide
3. `/docs/MIGRATION_IMPLEMENTATION_SUMMARY.md` - Implementation details
4. `/tests/test_tree_sitter_manager.py` - Test suite (ALL PASSING)
5. This file - Critical status update

## Next Steps

**If proceeding with Option 1:**
1. Create the query helper function
2. Update one language parser as a test (e.g., Python)
3. Verify it works end-to-end
4. Update remaining language parsers
5. Run full test suite
6. Update version number and release

**If choosing Option 2:**
1. Execute rollback commands above
2. Document that Python 3.13+ is not supported
3. Plan for future migration when time allows

## Questions?

- Do you want me to proceed with Option 1 and create the query helper?
- Should I update all language parsers now?
- Or would you prefer to rollback and tackle this later?
