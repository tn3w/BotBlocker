"""
--- File Tools ---
This module includes functionalities to read from and
write to files, methods to check file access permissions.

Author:   tn3w (mail@tn3w.dev)
License:  Apache-2.0 license
"""

import os
import json
import pickle
import shutil
from typing import Any
from threading import Lock
from concurrent.futures import ThreadPoolExecutor

try:
    from src.BotBlocker.utils.utils import handle_exception
except ImportError:
    try:
        from utils.utils import handle_exception
    except ImportError:
        from utils import handle_exception


def can_read(file_path: str) -> bool:
    """
    Checks if a file can be read.

    Args:
        file_path (str): The name to the file to check.

    Returns:
        bool: True if the file can be read, False otherwise.    
    """

    if not os.path.isfile(file_path):
        return False

    return os.access(file_path, os.R_OK)


def can_write(file_path: str, content_size: int) -> bool:
    """
    Checks if a file can be written to.

    Args:
        file_path (str): The path to the file to check.
        content_size (int): The size of the content to write to the file.

    Returns:
        bool: True if the file can be written to, False otherwise.    
    """

    directory_path = os.path.dirname(file_path)
    if not os.path.isdir(directory_path):
        return False

    if not os.access(directory_path, os.W_OK):
        return False

    if not os.path.getsize(directory_path) + content_size\
        <= os.stat(directory_path).st_blksize:
        return False

    return True


def has_subdirectory(directory_path: str) -> bool:
    """
    Checks if a directory has any subdirectories.

    Args:
        directory_path (str): The path to the directory to check.

    Returns:
        bool: True if the directory has any subdirectories, False otherwise.
    """

    if not os.path.isdir(directory_path):
        return False

    for entry in os.listdir(directory_path):
        full_path = os.path.join(directory_path, entry)
        if os.path.isdir(full_path):
            return True

    return False


def read(file_path: str, as_bytes: bool = False, default: Any = None) -> Any:
    """
    Reads a file.
    
    Args:
        file_path (str): The path to the file to read.
        default (Any, optional): The default value to return if the file
                                 does not exist. Defaults to None.
        as_bytes (bool, optional): Whether to return the file as bytes. Defaults to False.

    Returns:
        Any: The contents of the file, or the default value if the file does not exist.
    """

    if not can_read(file_path):
        return default

    try:
        with open(file_path, "r" + ("b" if as_bytes else ""),
                  encoding = None if as_bytes else "utf-8") as file:
            return file.read()

    except (FileNotFoundError, IsADirectoryError, IOError,
            PermissionError, ValueError, UnicodeDecodeError,
            TypeError, OSError) as exc:
        handle_exception(exc)

    return default


def write(file_path: str, content: Any) -> bool:
    """
    Writes a file.

    Args:
        file_path (str): The path to the file to write to.
        content (Any): The content to write to the file.

    Returns:
        bool: True if the file was written successfully, False otherwise.
    """

    if not can_write(file_path, len(content)):
        return False

    try:
        with open(file_path, "w" + ("b" if isinstance(content, bytes) else "")) as file:
            file.write(content)

        return True

    except (FileNotFoundError, IsADirectoryError, IOError,
            PermissionError, ValueError, TypeError, OSError) as exc:
        handle_exception(exc)

    return False


def delete(object_path: str) -> bool:
    """
    Deletes a object (like a file or directory).

    Args:
        object_path (str): The path to the object to delete.

    Returns:
        bool: True if the object was deleted successfully, False otherwise.
    """

    if not os.path.exists(object_path):
        return False

    try:
        if os.path.isdir(object_path):
            if has_subdirectory(object_path):
                shutil.rmtree(object_path)
                return True

            os.rmdir(object_path)
            return True

        os.remove(object_path)
        return True

    except (FileNotFoundError, IsADirectoryError, IOError,
            PermissionError, TypeError, OSError) as exc:
        handle_exception(exc)

    return False


file_locks: dict = {}
WRITE_EXECUTOR = ThreadPoolExecutor()


class CachedFile:
    """
    A interface for an file type with caching.
    """


    def __init__(self) -> None:
        self._data = {}


    def _get_cache(self, file_path: str) -> Any:
        """
        Gets the cached value for the given file path.

        Args:
            file_path (str): The path to the file to get the cached value for.

        Returns:
            Any: The cached value for the given file path.
        """

        return self._data.get(file_path)


    def _set_cache(self, file_path: str, value: Any) -> None:
        """
        Sets the cached value for the given file path.

        Args:
            file_path (str): The path to the file to set the cached value for.
            value (Any): The value to set the cached value to.
        
        Returns:
            None
        """

        self._data[file_path] = value


    def _load(self, file_path: str) -> Any:
        """
        Loads the file.

        Args:
            file_path (str): The path to the file to load.

        Returns:
            Any: The loaded file.
        """

        return read(file_path)


    def _dump(self, data: Any, file_path: str) -> bool:
        """
        Writes the data to the file.

        Args:
            data (Any): The data to write to the file.
            file_path (str): The path to the file to write to.

        Returns:
            bool: True if the file was written successfully, False otherwise.
        """

        return write(file_path, data)


    def load(self, file_path: str,
             default: Any = None) -> Any:
        """
        Loads the file.

        Args:
            file_path (str): The path to the file to load.
            default (Any, optional): The default value to return if the file
                                     does not exist. Defaults to None.

        Returns:
            Any: The loaded file.
        """

        file_data = self._get_cache(file_path)

        if file_data is None:
            if not can_read(file_path):
                return default

            if file_path not in file_locks:
                file_locks[file_path] = Lock()

            with file_locks[file_path]:
                try:
                    data = self._load(file_path)
                except (FileNotFoundError, IsADirectoryError, IOError,
                        PermissionError, ValueError, json.JSONDecodeError,
                        pickle.UnpicklingError, UnicodeDecodeError) as exc:
                    handle_exception(exc)
                else:

                    self._set_cache(file_path, data)
                    return data

            return default

        return file_data


    def dump(self, file_path: str, data: Any, as_thread: bool = False) -> bool:
        """
        Dumps the data to the file.

        Args:
            file_path (str): The path to the file to dump the data to.
            data (Any): The data to dump to the file.
            as_thread (bool, optional): Whether to dump the data as a thread. Defaults to False.
        
        Returns:
            bool: True if the data was dumped successfully, False otherwise.
        """

        file_directory = os.path.dirname(file_path)

        if can_write(file_directory, len(data)):
            return False

        if file_path not in file_locks:
            file_locks[file_path] = Lock()

        self._set_cache(file_path, data)

        try:
            if as_thread:
                WRITE_EXECUTOR.submit(self._dump, data, file_path)
            else:
                self._dump(data, file_path)
        except (FileNotFoundError, IsADirectoryError, IOError,
                PermissionError, ValueError, TypeError,
                pickle.PicklingError, OSError, RuntimeError) as exc:
            handle_exception(exc)

        return True


class PICKLEFile(CachedFile):
    """
    A pickle file type with caching.
    """


    def _load(self, file_path: str) -> Any:
        """
        Loads the file.

        Args:
            file_path (str): The path to the file to load.

        Returns:
            Any: The loaded file.
        """

        with open(file_path, 'rb') as file:
            return pickle.load(file)


    def _dump(self, data: Any, file_path: str) -> None:
        """
        Writes the data to the file.

        Args:
            data (Any): The data to write to the file.
        
        Returns:
            bool: True if the file was written successfully, False otherwise.
        """

        with file_locks[file_path]:
            with open(file_path, 'wb') as file:
                pickle.dump(data, file)


class JSONFile(CachedFile):
    """
    A JSON file type with caching.
    """


    def _load(self, file_path: str) -> Any:
        """
        Loads the file.

        Args:
            file_path (str): The path to the file to load.

        Returns:
            Any: The loaded file.
        """

        with open(file_path, 'r', encoding = 'utf-8') as file:
            return json.load(file)


    def _dump(self, data: Any, file_path: str) -> None:
        """
        Writes the data to the file.

        Args:
            data (Any): The data to write to the file.

        Returns:
            bool: True if the file was written successfully, False otherwise.
        """

        with file_locks[file_path]:
            with open(file_path, 'w', encoding = 'utf-8') as file:
                json.dump(data, file)


PICKLE = PICKLEFile()
JSON = JSONFile()


if __name__ == "__main__":
    print("fileutil.py: This file is not designed to be executed.")
