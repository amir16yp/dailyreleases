import difflib
import logging
import os
import time
from functools import wraps
from typing import Sequence, List
from time import sleep

from .Config import CONFIG

logger = logging.getLogger(__name__)


def case_insensitive_close_matches(word: str, possibilities: Sequence[str],
                                   n=3, cutoff=0.6) -> List[str]:
    """
    Python's difflib.get_close_matches does case sensitive sequence matching,
    this function decorates the library function to make it case insensitive.
    """
    possibilities = {sequence.lower(): sequence for sequence in possibilities}
    close_matches = difflib.get_close_matches(
        word.lower(), possibilities, n=n, cutoff=cutoff)
    return [possibilities[m] for m in close_matches]


def markdown_escape(text: str) -> str:
    """
    Escape reddit markdown.
    """
    table = {
        "\\": "\\\\",
        "`": "\\`",
        "*": "\\*",
        "_": "\\_",
        "{": "\\{",
        "}": "\\}",
        "[": "\\[",
        "]": "\\]",
        "(": "\\(",
        ")": "\\)",
        "#": "\\#",
        "+": "\\+",
        "-": "\\-",
        ".": "\\.",
        "!": "\\!",
        "~": "\\~",
        "|": "&#124;",
    }
    return text.translate(str.maketrans(table))


def setup_logging():
    """Configure logging for the application"""
    log_level = getattr(logging, CONFIG.CONFIG['logging']['level'].upper())
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Create logs directory if it doesn't exist
    log_dir = CONFIG.DATA_DIR.joinpath('logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure file handler
    file_handler = logging.FileHandler(log_dir.joinpath('main.log'))
    file_handler.setFormatter(logging.Formatter(log_format))
    
    # Configure console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


def retry(attempts=3, delay=60):
    """Retry decorator for functions that may fail"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == attempts - 1:
                        raise e
                    logging.warning(f"Attempt {attempt + 1} failed: {e}")
                    sleep(delay)
            return None
        return wrapper
    return decorator
