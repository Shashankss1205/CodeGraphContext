import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Toggle this to True to enable debug file logging
# For controlling console log visibility, use CGC_LOG_LEVEL environment variable
debug_mode = True  # Set to True for dev/test, False for production


def debug_log(message):
    """
    Write debug message to a file if debug_mode is enabled.
    
    This is separate from standard logging and writes to ~/mcp_debug.log.
    Use this for detailed debugging that you want persisted to a file.
    
    For controlling console log visibility, use the CGC_LOG_LEVEL environment
    variable instead (see codegraphcontext.utils.logging_config).
    """
    if not debug_mode:
        return
    debug_file = os.path.expanduser("~/mcp_debug.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(debug_file, "a") as f:
        f.write(f"[{timestamp}] {message}\n")
        f.flush()


def info_logger(msg):
    """Log info message. Visibility controlled by logging configuration."""
    return logger.info(msg)


def error_logger(msg):
    """Log error message. Visibility controlled by logging configuration."""
    return logger.error(msg)


def warning_logger(msg):
    """Log warning message. Visibility controlled by logging configuration."""
    return logger.warning(msg)


def debug_logger(msg):
    """Log debug message. Visibility controlled by logging configuration."""
    return logger.debug(msg)
