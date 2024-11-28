
import logging
import traceback
import sys

def log_tb_error(module_path: str, message: str, error: Exception) -> None:
    """
    Log an error message with full traceback information.
    
    Args:
        module_path: Path to the module where error occurred
        message: Error message to log
        error: Exception that was raised
    """
    tb = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
    logging.error(
        "%s: %s\nTraceback:\n%s",
        module_path,
        message, 
        tb
    )