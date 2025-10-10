"""String utility functions for CodeGraphContext.

This module provides utility functions for common string operations.
"""

from typing import Optional


def reverse_string(s: str) -> str:
    """Reverse a given string.
    
    Args:
        s (str): The input string to reverse.
        
    Returns:
        str: The reversed string.
        
    Raises:
        TypeError: If input is not a string.
        
    Examples:
        >>> reverse_string("hello")
        'olleh'
        >>> reverse_string("CodeGraphContext")
        'txetnoCgparGedoC'
        >>> reverse_string("")
        ''
    """
    if not isinstance(s, str):
        raise TypeError(f"Expected str, got {type(s).__name__}")
    
    return s[::-1]


def is_palindrome(s: str) -> bool:
    """Check if a string is a palindrome (case-insensitive, ignoring spaces).
    
    Args:
        s (str): The input string to check.
        
    Returns:
        bool: True if the string is a palindrome, False otherwise.
        
    Raises:
        TypeError: If input is not a string.
        
    Examples:
        >>> is_palindrome("racecar")
        True
        >>> is_palindrome("A man a plan a canal Panama")
        True
        >>> is_palindrome("hello")
        False
    """
    if not isinstance(s, str):
        raise TypeError(f"Expected str, got {type(s).__name__}")
    
    # Remove spaces and convert to lowercase for comparison
    cleaned = s.replace(" ", "").lower()
    return cleaned == cleaned[::-1]


def truncate_string(s: str, max_length: int, suffix: str = "...") -> str:
    """Truncate a string to a maximum length and add a suffix.
    
    Args:
        s (str): The input string to truncate.
        max_length (int): The maximum length of the output string (including suffix).
        suffix (str, optional): The suffix to append when truncating. Defaults to "...".
        
    Returns:
        str: The truncated string with suffix, or the original string if no truncation needed.
        
    Raises:
        TypeError: If s is not a string or max_length is not an integer.
        ValueError: If max_length is less than the length of the suffix.
        
    Examples:
        >>> truncate_string("This is a long string", 10)
        'This is...'
        >>> truncate_string("Short", 20)
        'Short'
        >>> truncate_string("CodeGraphContext", 12, "..")
        'CodeGraph..'
    """
    if not isinstance(s, str):
        raise TypeError(f"Expected str for s, got {type(s).__name__}")
    if not isinstance(max_length, int):
        raise TypeError(f"Expected int for max_length, got {type(max_length).__name__}")
    if not isinstance(suffix, str):
        raise TypeError(f"Expected str for suffix, got {type(suffix).__name__}")
    if max_length < len(suffix):
        raise ValueError(f"max_length ({max_length}) must be >= suffix length ({len(suffix)})")
    
    if len(s) <= max_length:
        return s
    
    return s[:max_length - len(suffix)] + suffix
