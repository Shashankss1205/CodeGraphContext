import os
from datetime import datetime
import logging
logger = logging.getLogger(__name__)

# Toggle this to True to enable debug logging
debug_mode = True  # Set to True for dev/test, False for production
log_mode = True  # Set to True to enable user login logging

def debug_log(message):
    """Write debug message to a file if debug_mode is enabled"""
    if not debug_mode:
        return
    debug_file = os.path.expanduser("~/mcp_debug.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(debug_file, "a") as f:
        f.write(f"[{timestamp}] {message}\n")
        f.flush()

def info_logger(msg):
    if log_mode:
        return logger.info(msg)
    else:
        return

def error_logger(msg):
    if log_mode:
        return logger.error(msg)
    else:
        return
    
def warning_logger(msg):
    if log_mode:
        return logger.warning(msg)
    else:
        return
    
def debug_logger(msg):
    return logger.debug(msg)
