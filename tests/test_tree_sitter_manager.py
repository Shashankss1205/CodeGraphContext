"""
Tests for the tree-sitter manager module.

This test suite verifies:
1. Language caching works correctly
2. Parser creation is thread-safe
3. Language aliasing works
4. Error handling is appropriate
"""

import pytest
import threading
from pathlib import Path

from codegraphcontext.utils.tree_sitter_manager import (
    TreeSitterManager,
    get_tree_sitter_manager,
    get_language_safe,
    create_parser,
    LANGUAGE_ALIASES,
)


class TestTreeSitterManager:
    """Test suite for TreeSitterManager class."""
    
    def test_singleton_pattern(self):
        """Test that get_tree_sitter_manager returns the same instance."""
        manager1 = get_tree_sitter_manager()
        manager2 = get_tree_sitter_manager()
        assert manager1 is manager2
    
    def test_get_language_safe_caching(self):
        """Test that languages are cached properly."""
        manager = get_tree_sitter_manager()
        
        # First call loads the language
        lang1 = manager.get_language_safe("python")
        
        # Second call should return cached language
        lang2 = manager.get_language_safe("python")
        
        assert lang1 is lang2
    
    def test_language_aliases(self):
        """Test that language aliases work correctly."""
        manager = get_tree_sitter_manager()
        
        # Test Python aliases
        lang_python = manager.get_language_safe("python")
        lang_py = manager.get_language_safe("py")
        assert lang_python is lang_py
        
        # Test C# aliases
        lang_csharp1 = manager.get_language_safe("c_sharp")
        lang_csharp2 = manager.get_language_safe("c#")
        lang_csharp3 = manager.get_language_safe("csharp")
        lang_csharp4 = manager.get_language_safe("cs")
        assert lang_csharp1 is lang_csharp2
        assert lang_csharp2 is lang_csharp3
        assert lang_csharp3 is lang_csharp4
        
        # Test JavaScript aliases
        lang_js1 = manager.get_language_safe("javascript")
        lang_js2 = manager.get_language_safe("js")
        assert lang_js1 is lang_js2
    
    def test_invalid_language_raises_error(self):
        """Test that invalid language names raise ValueError."""
        manager = get_tree_sitter_manager()
        
        with pytest.raises(ValueError, match="Unknown language"):
            manager.get_language_safe("invalid_language_xyz")
    
    def test_create_parser_returns_new_instance(self):
        """Test that create_parser returns a new parser each time."""
        manager = get_tree_sitter_manager()
        
        parser1 = manager.create_parser("python")
        parser2 = manager.create_parser("python")
        
        # Parsers should be different instances
        assert parser1 is not parser2
        
        # But they should use the same language
        assert parser1.language is parser2.language
    
    def test_thread_safety(self):
        """Test that language loading is thread-safe."""
        manager = get_tree_sitter_manager()
        results = {}
        
        def load_language(lang_name, thread_id):
            """Load a language and store the result."""
            results[thread_id] = manager.get_language_safe(lang_name)
        
        # Create multiple threads that load the same language
        threads = []
        for i in range(10):
            thread = threading.Thread(target=load_language, args=("python", i))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All threads should have gotten the same language instance
        first_lang = results[0]
        for lang in results.values():
            assert lang is first_lang
    
    def test_is_language_available(self):
        """Test the is_language_available method."""
        manager = get_tree_sitter_manager()
        
        # Valid languages should return True
        assert manager.is_language_available("python") is True
        assert manager.is_language_available("javascript") is True
        assert manager.is_language_available("py") is True  # alias
        
        # Invalid languages should return False
        assert manager.is_language_available("invalid_xyz") is False
    
    def test_get_supported_languages(self):
        """Test that get_supported_languages returns expected languages."""
        manager = get_tree_sitter_manager()
        
        supported = manager.get_supported_languages()
        
        # Should be a sorted list
        assert isinstance(supported, list)
        assert supported == sorted(supported)
        
        # Should contain expected languages
        expected_languages = ["python", "javascript", "typescript", "c", "cpp", "java", "ruby", "rust", "go", "c_sharp"]
        for lang in expected_languages:
            assert lang in supported
    
    def test_convenience_functions(self):
        """Test the module-level convenience functions."""
        # Test get_language_safe
        lang1 = get_language_safe("python")
        lang2 = get_language_safe("python")
        assert lang1 is lang2
        
        # Test create_parser
        parser1 = create_parser("python")
        parser2 = create_parser("python")
        assert parser1 is not parser2
        assert parser1.language is parser2.language


class TestLanguageAliases:
    """Test suite for language alias mappings."""
    
    def test_all_aliases_map_to_valid_languages(self):
        """Test that all aliases in LANGUAGE_ALIASES map to valid languages."""
        manager = get_tree_sitter_manager()
        
        # Get unique target languages
        unique_targets = set(LANGUAGE_ALIASES.values())
        
        # Each target should be loadable
        for target in unique_targets:
            try:
                manager.get_language_safe(target)
            except Exception as e:
                pytest.fail(f"Language '{target}' from LANGUAGE_ALIASES is not loadable: {e}")
    
    def test_canonical_names_map_to_themselves(self):
        """Test that canonical names map to themselves in LANGUAGE_ALIASES."""
        canonical_names = ["python", "javascript", "typescript", "c", "cpp", "java", "ruby", "rust", "go", "c_sharp"]
        
        for name in canonical_names:
            assert LANGUAGE_ALIASES.get(name) == name, f"Canonical name '{name}' should map to itself"


class TestParserCreation:
    """Test suite for parser creation and usage."""
    
    def test_parser_can_parse_code(self):
        """Test that created parsers can actually parse code."""
        manager = get_tree_sitter_manager()
        parser = manager.create_parser("python")
        
        # Simple Python code
        code = b"def hello():\n    print('world')\n"
        tree = parser.parse(code)
        
        assert tree is not None
        assert tree.root_node is not None
        assert tree.root_node.type == "module"
    
    def test_multiple_parsers_independent(self):
        """Test that multiple parsers can be used independently."""
        manager = get_tree_sitter_manager()
        
        parser1 = manager.create_parser("python")
        parser2 = manager.create_parser("python")
        
        code1 = b"x = 1"
        code2 = b"y = 2"
        
        tree1 = parser1.parse(code1)
        tree2 = parser2.parse(code2)
        
        # Trees should be different
        assert tree1 is not tree2
        assert tree1.root_node.text != tree2.root_node.text


class TestErrorHandling:
    """Test suite for error handling."""
    
    def test_clear_error_for_unknown_language(self):
        """Test that unknown languages produce clear error messages."""
        manager = get_tree_sitter_manager()
        
        with pytest.raises(ValueError) as exc_info:
            manager.get_language_safe("nonexistent_language")
        
        error_message = str(exc_info.value)
        assert "Unknown language" in error_message
        assert "nonexistent_language" in error_message
    
    def test_case_insensitive_language_names(self):
        """Test that language names are case-insensitive."""
        manager = get_tree_sitter_manager()
        
        # These should all work
        lang1 = manager.get_language_safe("python")
        lang2 = manager.get_language_safe("Python")
        lang3 = manager.get_language_safe("PYTHON")
        
        assert lang1 is lang2
        assert lang2 is lang3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
