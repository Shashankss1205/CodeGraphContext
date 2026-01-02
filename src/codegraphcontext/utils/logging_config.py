"""
Centralized logging configuration for CodeGraphContext.

This module provides context-aware logging configuration that adjusts
log levels based on whether the code is running as:
- CLI command (quiet by default)
- MCP server (needs visibility)
- Background worker (minimal output)

Users can override logging levels using the CGC_LOG_LEVEL environment variable.
"""

import logging
import os
import sys


def setup_logging(context: str = "cli", level: str = None) -> None:
    """
    Configure logging for different execution contexts.
    
    Args:
        context: Execution context - "cli", "mcp", or "worker"
        level: Override log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
               If None, uses context-appropriate defaults or CGC_LOG_LEVEL env var
    
    Context Defaults:
        - cli: WARNING (quiet output, only show warnings/errors)
        - mcp: INFO (server needs operational visibility)
        - worker: WARNING (background process, minimal output)
    
    Environment Variable:
        CGC_LOG_LEVEL: Override default level for any context
        Example: CGC_LOG_LEVEL=DEBUG cgc index .
    
    Examples:
        >>> setup_logging("cli")  # CLI with quiet output
        >>> setup_logging("mcp")  # MCP server with INFO logs
        >>> # With env: CGC_LOG_LEVEL=DEBUG
        >>> setup_logging("cli")  # Will use DEBUG despite CLI context
    """
    # Determine the appropriate log level
    if level is None:
        # Check environment variable first
        env_level = os.getenv("CGC_LOG_LEVEL", "").upper()
        if env_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            level = env_level
        else:
            # Use context-based defaults
            context_defaults = {
                "cli": "WARNING",
                "mcp": "INFO",
                "worker": "WARNING",
            }
            level = context_defaults.get(context, "WARNING")
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.WARNING)
    
    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        stream=sys.stderr,
        force=True  # Override any previous configuration
    )
    
    # Set specific logger levels for noisy third-party libraries
    # These should always be WARNING or higher regardless of our level
    logging.getLogger("neo4j").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    # Get the root logger to verify configuration
    logger = logging.getLogger(__name__)
    
    # Only log this in DEBUG mode to avoid noise
    if numeric_level <= logging.DEBUG:
        logger.debug(f"Logging configured for context='{context}' with level={level}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    This is a convenience wrapper around logging.getLogger that ensures
    the logger respects the configuration set by setup_logging().
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.debug("Debug message")
    """
    return logging.getLogger(name)
