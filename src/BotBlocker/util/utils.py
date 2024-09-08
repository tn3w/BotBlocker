"""
--- BotBlocker Utilities ---
This module includes utilities for the BotBlocker project.

Author:   tn3w (mail@tn3w.dev)
License:  Apache-2.0 license
"""

from traceback import format_exc


def handle_exception(exception: Exception) -> None:
    """
    Handles an exception.

    Args:
        exception (Exception): The exception to handle.
    """

    traceback = format_exc()
    print(exception, traceback)


if __name__ == "__main__":
    print("utils.py: This file is not designed to be executed.")
