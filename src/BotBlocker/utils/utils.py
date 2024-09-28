"""
--- BotBlocker Utils ---

This module includes utilities for the BotBlocker project.

Author:   tn3w (mail@tn3w.dev)
License:  Apache-2.0 license
"""

import re
import json
import time
import socket
import secrets
import functools
import http.client
import urllib.error
import urllib.request
from traceback import format_exc
from typing import Tuple, Final, Optional, Any


CHARACTER_CATEGORIES: Final[dict] = {
    "a-z": "abcdefghijklmnopqrstuvwxyz",
    "A-Z": "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "0-9": "0123456789",
    "%": "!\'#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
}


def generate_secure_random_string(length: int, characters: str = "a-zA-Z0-9%"):
    """
    Generate a random string of a specified length using a set of characters.

    Parameters:
        length (int): The length of the string to be generated.
        characters (str): A string specifying the character sets to include in the generated string. 

    Returns:
        str: A randomly generated string of the specified length
            composed of the selected characters.
    """

    full_characters = ""
    for category, mapping in CHARACTER_CATEGORIES.items():
        if category in characters:
            full_characters += mapping

    return "".join(secrets.choice(characters) for _ in range(length))


def is_float(value: str) -> bool:
    """
    Check if a given string represents a valid float.

    Args:
        value (str): The string to be checked.

    Returns:
        bool: True if the string represents a valid float, False otherwise.
    """

    if not isinstance(value, str):
        return False

    float_pattern = re.compile(r'^-?\d+(\.\d+)?$')
    return bool(float_pattern.match(value))


def handle_exception(exception: Tuple[Exception, str], *args) -> None:
    """
    Handles an exception by printing the exception message and traceback.

    Args:
        exception (Tuple[Exception, str]): A tuple containing the exception to
            handle and an optional message.
        *args: Additional arguments to be printed alongside the exception message and traceback.

    Returns:
        None: This function does not return a value; it only prints the exception details.
    """

    if isinstance(exception, str):
        print(exception, *args)
        return

    traceback = format_exc()
    print(exception, traceback, *args)


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


def matches_asterisk_rule(obj: str, asterisk_rule: str) -> bool:
    """
    Checks if a string matches a given asterisk rule.

    Args:
        obj (str): The string to check.
        asterisk_rule (str): The asterisk rule to match against.

    Returns:
        bool: True if the string matches the rule, False otherwise.
    """

    if isinstance(obj, str) and isinstance(asterisk_rule, str) and '*' in asterisk_rule:
        parts = asterisk_rule.split('*')

        if len(parts) == 2:
            start, end = parts
            return obj.startswith(start) and obj.endswith(end)

        first_asterisk_index = asterisk_rule.index('*')
        last_asterisk_index = asterisk_rule.rindex('*')
        start = asterisk_rule[:first_asterisk_index]
        middle = asterisk_rule[first_asterisk_index + 1:last_asterisk_index]
        end = asterisk_rule[last_asterisk_index + 1:]

        return obj.startswith(start) and obj.endswith(end) and middle in obj

    return obj == asterisk_rule


def get_fields(rule: tuple) -> list:
    """
    Extracts fields from a rule tuple.

    Args:
        rule (tuple): The rule tuple to extract fields from.

    Returns:
        list: A list of fields extracted from the rule.
    """

    fields = []

    for i, value in enumerate(rule):
        if value in ('and', 'or'):
            fields.append(get_fields(rule[:i]))
            fields.append(get_fields(rule[i + 1:]))

    field = rule[0]
    fields.append(field)
    return fields


def compare_numbers(field_data: Any, value: Any, morethan: bool = False) -> bool:
    """
    Compares two numbers based on the given operator.

    Args:
        field_data (Any): The first number (or string representation of a number).
        value (Any): The second number to compare against.
        morethan (bool): If True, checks if field_data is greater than value; 
                         if False, checks if field_data is less than value.

    Returns:
        bool: True if the comparison is true, False otherwise.
    """

    if isinstance(field_data, str):
        if field_data.is_digit():
            field_data = int(field_data)

    if not isinstance(field_data, int):
        return False

    if morethan:
        return field_data > value

    return field_data < value


def check_string_start_end(field_data: Any, value: str, startswith: bool = False) -> bool:
    """
    Checks if a string starts or ends with a given value.

    Args:
        field_data (Any): The string to check (or integer to convert).
        value (str): The value to check against.
        startswith (bool): If True, checks if the string starts with the value; 
                           if False, checks if it ends with the value.

    Returns:
        bool: True if the condition is met, False otherwise.
    """

    if isinstance(field_data, int):
        field_data = str(field_data)
    elif not isinstance(field_data, str):
        return False

    if startswith:
        return field_data.startswith(value)

    return field_data.endswith(value)


def evaluate_operator(field_data: Any, operator: str, value: Any) -> bool:
    """
    Evaluates an operator against field data and a value.

    Args:
        field_data (Any): The data to evaluate.
        operator (str): The operator to use for evaluation.
        value (Any): The value to compare against.

    Returns:
        bool: True if the evaluation is true, False otherwise.
    """

    operator_actions = [
        (
            ['==', 'equals', 'equal', 'is', 'isthesameas'],
            lambda: matches_asterisk_rule(field_data, value)
        ),
        (
            ['!=', 'doesnotequal', 'doesnotequals', 'notequals', 'notequal', 'notis'],
            lambda: not matches_asterisk_rule(field_data, value)
        ),
        (['contains', 'contain'], lambda: value in field_data),
        (
            ['doesnotcontain', 'doesnotcontains', 'notcontain', 'notcontains'],
            lambda: value not in field_data
        ),
        (['isin', 'in'], lambda: field_data in value),
        (['isnotin', 'notisin', 'notin'], lambda: field_data not in value),
        (['greaterthan', 'largerthan'], lambda: compare_numbers(field_data, value, True)),
        (['lessthan'], lambda: compare_numbers(field_data, value)),
        (
            ['startswith', 'beginswith'],
            lambda: check_string_start_end(field_data, value, True)
        ),
        (
            ['endswith', 'concludeswith', 'finisheswith'],
            lambda: check_string_start_end(field_data, value)
        ),
    ]

    for operators, action in operator_actions:
        if operator in operators:
            return action()

    return False


def matches_rule(rule: tuple, fields: dict) -> bool:
    """
    Checks if a rule matches the given fields.

    Args:
        rule (tuple): The rule to check.
        fields (dict): The fields to match against.

    Returns:
        bool: True if the rule matches the fields, False otherwise.
    """

    i = 0
    for i, value in enumerate(rule):
        if value == 'and':
            return matches_rule(rule[:i], fields) and \
                matches_rule(rule[i + 1:], fields)

        if value == 'or':
            return matches_rule(rule[:i], fields) or \
                matches_rule(rule[i + 1:], fields)

        i += 1

    field, operator, value = rule
    field_data = fields.get(field, None)

    if field_data is None:
        return False

    if isinstance(operator, str):
        operator = operator.strip(' ').lower()

    return evaluate_operator(field_data, operator, value)


def http_request(url: str, method: str = "GET", timeout: int = 2,
                 is_json: bool = False, default: Optional[Any] = None) -> Optional[Any]:
    """
    Sends an HTTP request to the specified URL and returns the response content.

    Args:
        url (str): The URL to which the request is sent.
        method (str, optional): The HTTP method to use for the request. 
                                Defaults to "GET".
        timeout (int, optional): The maximum time (in seconds) to wait 
                                 for a response. Defaults to 2 seconds.
        is_json (bool, optional): If True, the response content is parsed 
                                  as JSON and returned as a Python object. 
                                  If False, the raw response content is 
                                  returned as bytes. Defaults to False.
        default (Optional[Any], optional): The value to return if an 
                                            exception occurs during the 
                                            request. Defaults to None.

    Returns:
        Optional[Any]: The response content, either as a parsed JSON 
                        object or as bytes. Returns None if an exception 
                        occurs during the request.
    """

    try:
        req = urllib.request.Request(
            url, headers = {"User-Agent":
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                " (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.3"
            }, method = method
        )

        with urllib.request.urlopen(req, timeout = timeout) as response:
            if response.getcode() != 200:
                return default

            content = response.read().decode("utf-8")

        if is_json:
            return json.loads(content)

        return content
    except (urllib.error.HTTPError, urllib.error.URLError, socket.timeout, TimeoutError,
            json.JSONDecodeError, http.client.RemoteDisconnected, UnicodeEncodeError,
            http.client.IncompleteRead, http.client.HTTPException, ConnectionResetError,
            ConnectionAbortedError, ConnectionRefusedError, ConnectionError) as exc:
        handle_exception(exc)

    return default


class Logger:
    """
    A simple logging class that provides functionality to log messages 
    with various parameters.
    """


    def log(self, **kwargs) -> None:
        """
        Logs a message with the provided keyword arguments.

        Args:
            **kwargs: Arbitrary keyword arguments that represent the 
                      details of the log entry. This can include 
                      information such as log level, message, 
                      timestamp, and any other relevant data.

        Returns:
            None: This method does not return any value.
        """


if __name__ == "__main__":
    print("utils.py: This file is not designed to be executed.")
