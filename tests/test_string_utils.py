"""Tests for string_utils module."""

import pytest
from src.codegraphcontext.utils.string_utils import (
    reverse_string,
    is_palindrome,
    truncate_string,
)


class TestReverseString:
    """Tests for reverse_string function."""

    def test_reverse_simple_string(self):
        """Test reversing a simple string."""
        assert reverse_string("hello") == "olleh"

    def test_reverse_with_spaces(self):
        """Test reversing a string with spaces."""
        assert reverse_string("hello world") == "dlrow olleh"

    def test_reverse_empty_string(self):
        """Test reversing an empty string."""
        assert reverse_string("") == ""

    def test_reverse_single_character(self):
        """Test reversing a single character."""
        assert reverse_string("a") == "a"

    def test_reverse_with_special_chars(self):
        """Test reversing a string with special characters."""
        assert reverse_string("hello@123") == "321@olleh"

    def test_reverse_palindrome(self):
        """Test reversing a palindrome."""
        assert reverse_string("racecar") == "racecar"

    def test_reverse_type_error(self):
        """Test that TypeError is raised for non-string input."""
        with pytest.raises(TypeError, match="Expected str, got int"):
            reverse_string(123)

        with pytest.raises(TypeError, match="Expected str, got NoneType"):
            reverse_string(None)


class TestIsPalindrome:
    """Tests for is_palindrome function."""

    def test_simple_palindrome(self):
        """Test a simple palindrome."""
        assert is_palindrome("racecar") is True

    def test_not_palindrome(self):
        """Test a non-palindrome string."""
        assert is_palindrome("hello") is False

    def test_palindrome_with_spaces(self):
        """Test palindrome with spaces."""
        assert is_palindrome("A man a plan a canal Panama") is True

    def test_palindrome_case_insensitive(self):
        """Test that palindrome check is case-insensitive."""
        assert is_palindrome("RaceCar") is True

    def test_empty_string_palindrome(self):
        """Test that empty string is a palindrome."""
        assert is_palindrome("") is True

    def test_single_character_palindrome(self):
        """Test that single character is a palindrome."""
        assert is_palindrome("a") is True

    def test_palindrome_with_special_chars(self):
        """Test palindrome with special characters."""
        assert is_palindrome("a@a") is True

    def test_palindrome_type_error(self):
        """Test that TypeError is raised for non-string input."""
        with pytest.raises(TypeError, match="Expected str, got int"):
            is_palindrome(123)


class TestTruncateString:
    """Tests for truncate_string function."""

    def test_truncate_long_string(self):
        """Test truncating a long string."""
        assert truncate_string("This is a long string", 10) == "This is..."

    def test_no_truncation_needed(self):
        """Test that short strings are not truncated."""
        assert truncate_string("Short", 20) == "Short"

    def test_truncate_exact_length(self):
        """Test truncating when string is exactly max_length."""
        assert truncate_string("12345", 5) == "12345"

    def test_truncate_with_custom_suffix(self):
        """Test truncating with a custom suffix."""
        assert truncate_string("CodeGraphContext", 12, "..") == "CodeGraph.."

    def test_truncate_empty_string(self):
        """Test truncating an empty string."""
        assert truncate_string("", 10) == ""

    def test_truncate_with_empty_suffix(self):
        """Test truncating with an empty suffix."""
        assert truncate_string("Hello World", 5, "") == "Hello"

    def test_truncate_type_error_string(self):
        """Test that TypeError is raised for non-string input."""
        with pytest.raises(TypeError, match="Expected str for s, got int"):
            truncate_string(123, 10)

    def test_truncate_type_error_max_length(self):
        """Test that TypeError is raised for non-int max_length."""
        with pytest.raises(TypeError, match="Expected int for max_length, got str"):
            truncate_string("hello", "10")

    def test_truncate_type_error_suffix(self):
        """Test that TypeError is raised for non-string suffix."""
        with pytest.raises(TypeError, match="Expected str for suffix, got int"):
            truncate_string("hello", 10, 123)

    def test_truncate_value_error(self):
        """Test that ValueError is raised when max_length < suffix length."""
        with pytest.raises(ValueError, match="max_length \\(2\\) must be >= suffix length \\(3\\)"):
            truncate_string("hello", 2, "...")

    def test_truncate_minimum_length(self):
        """Test truncating to minimum possible length."""
        assert truncate_string("Hello World", 3, "...") == "..."

    def test_truncate_unicode_string(self):
        """Test truncating a string with unicode characters."""
        assert truncate_string("Hello 世界", 8, "...") == "Hello..."
