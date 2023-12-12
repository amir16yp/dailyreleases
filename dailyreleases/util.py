import difflib
import logging
import time
from functools import wraps
from typing import Sequence, List


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


def retry(attempts=3, delay=0):
    """
    Retry wrapped function `attempts` times.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for i in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.exception(
                        f"{func.__name__} attempt {i}/{attempts}", exc_info=e
                    )
                    if i >= attempts:
                        raise
                    time.sleep(delay)

        return wrapper

    return decorator
