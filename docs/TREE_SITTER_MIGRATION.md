# Tree-sitter Migration Guide

## Overview

CodeGraphContext has migrated from `tree-sitter-languages` to `tree-sitter-language-pack` to support Python 3.13+ and future Python versions. This document explains the changes and their implications.

## Why This Migration Was Necessary

### The Problem
- `tree-sitter-languages` is a monolithic package that ships all grammars in a single binary
- It has ABI compatibility issues with Python 3.13 and 3.14
- The package is no longer actively maintained for newer Python versions
- Total failure on ABI breaks (all-or-nothing approach)

### The Solution
- `tree-sitter-language-pack` ships per-language wheels
- Tracks CPython ABI changes properly
- Works on Python 3.12, 3.13, 3.14, and future versions
- Better memory control and performance characteristics

## What Changed

### 1. Dependencies (pyproject.toml)

**Before:**
```toml
requires-python = ">=3.9,<3.13"
dependencies = [
    "tree-sitter==0.20.4",
    "tree-sitter-languages==1.10.2",
    ...
]
```

**After:**
```toml
requires-python = ">=3.9"
dependencies = [
    "tree-sitter>=0.21.0",
    "tree-sitter-language-pack>=0.6.0",
    ...
]
```

### 2. Parser Lifecycle Management

**Before:**
```python
from tree_sitter_languages import get_language

language = get_language("python")
parser = Parser()
parser.set_language(language)
```

**After:**
```python
from codegraphcontext.utils.tree_sitter_manager import get_tree_sitter_manager

ts_manager = get_tree_sitter_manager()
language = ts_manager.get_language_safe("python")  # Cached
parser = Parser()
parser.set_language(language)

# Or use the convenience method:
parser = ts_manager.create_parser("python")  # Creates new parser each time
```

### 3. Language Caching

**Key Principle:** Cache languages, NOT parsers.

- **Languages are cached** globally and thread-safe
- **Parsers are NOT cached** - each component creates its own parser
- **Parsers are NOT thread-safe** - never share a parser across threads

### 4. Language Name Aliasing

The new system supports language aliases for better compatibility:

```python
# All of these work:
ts_manager.get_language_safe("python")
ts_manager.get_language_safe("py")

ts_manager.get_language_safe("c_sharp")
ts_manager.get_language_safe("c#")
ts_manager.get_language_safe("csharp")
ts_manager.get_language_safe("cs")
```

Supported aliases:
- `py` → `python`
- `js` → `javascript`
- `ts` → `typescript`
- `c++` → `cpp`
- `c#`, `csharp`, `cs` → `c_sharp`
- `rb` → `ruby`
- `rs` → `rust`

### 5. Error Handling

**Before:**
```python
parser = get_parser("unknown")  # Often silently fails late
```

**After:**
```python
try:
    language = ts_manager.get_language_safe("unknown")
except ValueError as e:
    # Clear error message about missing language
    print(f"Language not available: {e}")
```

## Architecture Changes

### New Module: `tree_sitter_manager.py`

Located at: `src/codegraphcontext/utils/tree_sitter_manager.py`

**Key Components:**

1. **TreeSitterManager Class**
   - Singleton pattern for global language cache
   - Thread-safe language loading
   - Parser creation (not caching)
   - Language availability checking

2. **Language Aliases Dictionary**
   - Maps common aliases to canonical names
   - Ensures consistent language naming

3. **Convenience Functions**
   - `get_language_safe(lang)` - Get cached language
   - `create_parser(lang)` - Create new parser instance

### Updated: `graph_builder.py`

**Changes:**
- Import from `tree_sitter_manager` instead of `tree_sitter_languages`
- `TreeSitterParser.__init__` uses `get_tree_sitter_manager()`
- Each `TreeSitterParser` instance creates its own parser (not shared)

## Performance Implications

### Improvements ✅
- **Faster startup**: Languages loaded lazily on first use
- **Better memory control**: Only load languages you actually use
- **Improved indexing**: Per-language wheels are more optimized
- **Lower memory footprint**: No monolithic binary

### Considerations ⚠️
- **First parse per language**: Slightly slower (one-time language load)
- **Subsequent parses**: Same or faster than before

## Thread Safety

### Critical Rules

1. **Languages are thread-safe** ✅
   - Cached globally
   - Safe to share across threads
   - Loaded once, used everywhere

2. **Parsers are NOT thread-safe** ❌
   - Each thread must create its own parser
   - Never share a parser instance
   - Use `create_parser()` for each thread

### Example: Thread-Safe Usage

```python
from concurrent.futures import ThreadPoolExecutor
from codegraphcontext.utils.tree_sitter_manager import get_tree_sitter_manager

def parse_file(file_path):
    # Each thread creates its own parser
    ts_manager = get_tree_sitter_manager()
    parser = ts_manager.create_parser("python")
    
    with open(file_path, 'rb') as f:
        tree = parser.parse(f.read())
    return tree

# Safe: Each thread gets its own parser
with ThreadPoolExecutor(max_workers=4) as executor:
    results = executor.map(parse_file, file_paths)
```

## Grammar Version Considerations

### Potential Issues

Because grammars are now updated independently:
- AST shapes may differ slightly from old version
- Node names might change
- Query files (.scm) may need updates

### What We've Done

- Tested all language parsers with new grammars
- Verified node names and query patterns
- Updated any breaking changes

### What You Should Do

If you extend CodeGraphContext with custom parsers:
1. Test your tree-sitter queries with new grammars
2. Verify hardcoded node names still exist
3. Check AST structure hasn't changed significantly

## Migration Checklist

For users upgrading CodeGraphContext:

- [ ] Uninstall old dependencies:
  ```bash
  pip uninstall tree-sitter tree-sitter-languages
  ```

- [ ] Install new version:
  ```bash
  pip install --upgrade codegraphcontext
  ```

- [ ] Verify installation:
  ```bash
  python -c "from codegraphcontext.utils.tree_sitter_manager import get_tree_sitter_manager; print(get_tree_sitter_manager().get_supported_languages())"
  ```

- [ ] Test with your codebase:
  ```bash
  cgc index /path/to/your/repo
  ```

## Troubleshooting

### "Language 'X' is not available"

**Cause:** The language grammar isn't in `tree-sitter-language-pack`

**Solution:** 
1. Check if language name is correct (try aliases)
2. Verify language is supported: `ts_manager.get_supported_languages()`
3. Check if grammar exists in tree-sitter-language-pack

### "Parser is not thread-safe" errors

**Cause:** Sharing a parser instance across threads

**Solution:** Create a new parser for each thread using `create_parser()`

### Import errors on Python 3.13+

**Cause:** Old dependencies still installed

**Solution:**
```bash
pip uninstall tree-sitter tree-sitter-languages
pip install --force-reinstall codegraphcontext
```

## Benefits Summary

✅ **Future-proof**: Works with Python 3.13, 3.14, and beyond  
✅ **Better control**: Explicit parser lifecycle management  
✅ **Faster indexing**: Optimized per-language wheels  
✅ **Cleaner architecture**: Clear separation of concerns  
✅ **Thread-safe**: Proper caching and lifecycle management  
✅ **Better errors**: Clear, actionable error messages  
✅ **Flexible**: Language aliasing for compatibility  

## References

- [tree-sitter-language-pack GitHub](https://github.com/grantjenks/py-tree-sitter-language-pack)
- [tree-sitter Documentation](https://tree-sitter.github.io/tree-sitter/)
- [Python 3.13 Release Notes](https://docs.python.org/3.13/whatsnew/3.13.html)
