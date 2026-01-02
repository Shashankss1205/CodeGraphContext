import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def debug_log(message):
    """
    Log debug message using standard logging.
    
    This replaces the old manual file logging implementation.
    Visibility is controlled by the standard logging configuration
    (CGC_LOG_LEVEL environment variable).
    """
    logger.debug(message)


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
