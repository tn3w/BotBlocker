"""
--- BotBlocker Utilities ---
This module includes utilities for the BotBlocker project.

Author:   tn3w (mail@tn3w.dev)
License:  Apache-2.0 license
"""

import time
import functools
from traceback import format_exc


def handle_exception(exception: Exception) -> None:
    """
    Handles an exception.

    Args:
        exception (Exception): The exception to handle.
    """

    traceback = format_exc()
    print(exception, traceback)


def cache_with_ttl(ttl: int) -> callable:
    """
    Caches the result of a function with a given TTL.

    Args:
        ttl (int): The TTL in seconds.

    Returns:
        callable: The decorated function.
    """

    def decorator(func: callable) -> callable:
        """
        Internal decorator function.

        Args:
            func (callable): The function to decorate.

        Returns:
            callable: The decorated function.
        """

        cache = {}

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """
            Internal wrapper function.

            Args:
                *args: The positional arguments to pass to the function.
                **kwargs: The keyword arguments to pass to the function.
            """

            key = (args, tuple(kwargs.items()))
            current_time = time.time()

            if key in cache:
                result, timestamp = cache[key]
                if current_time - timestamp < ttl:
                    return result

                del cache[key]

            result = func(*args, **kwargs)
            cache[key] = (result, current_time)
            return result

        return wrapper

    return decorator


if __name__ == "__main__":
    print("utils.py: This file is not designed to be executed.")
