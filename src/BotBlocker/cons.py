"""
--- Constants ---
This file contains the constants used in the application.

Author:   tn3w (mail@tn3w.dev)
License:  Apache-2.0 license
"""

import os
from typing import Final, Tuple


CURRENT_DIRECTORY_PATH: Final[str] = os.path.dirname(os.path.abspath(__file__))\
    .replace("\\\\", "\\")\
    .replace("\\", "/")\
    .replace("/src/BotBlocker", "")\
    .replace("/src", "")

is_test_environment: bool = os.path.exists(os.path.join(CURRENT_DIRECTORY_PATH, '.test'))
if not is_test_environment:
    try:
        import pkg_resources
    except ImportError:
        is_test_environment: bool = True


def get_work_dir(test_environment: bool = False) -> Tuple[str, bool]:
    """
    Determine the working directory for the application.

    Args:
        test_environment (bool, optional): Whether to use the test environment.
                                           Defaults to False.

    Return:
        Tuple[str, bool]: The working directory path and a boolean indicating the test environment.
    """

    if test_environment:
        return CURRENT_DIRECTORY_PATH, True

    try:
        file_path = pkg_resources.resource_filename('BotBlocker', '')
    except ModuleNotFoundError:
        return CURRENT_DIRECTORY_PATH, True

    if not isinstance(file_path, str) or not os.path.isdir(file_path):
        return CURRENT_DIRECTORY_PATH, True

    return file_path, False


WORK_DIRECTORY_PATH: Final[str]
TEST_ENVIRONMENT: Final[bool]
WORK_DIRECTORY_PATH, TEST_ENVIRONMENT = get_work_dir(is_test_environment)

SRC_DIRECTORY_PATH: Final[str] = os.path.join(WORK_DIRECTORY_PATH, 'src', 'BotBlocker')\
    if TEST_ENVIRONMENT else WORK_DIRECTORY_PATH\

TEMPLATES_DIRECTORY_PATH: Final[str] = os.path.join(SRC_DIRECTORY_PATH, 'templates')


if __name__ == "__main__":
    print("cons.py: This file is not designed to be executed.")
