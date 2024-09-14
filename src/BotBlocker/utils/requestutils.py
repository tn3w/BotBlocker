"""
--- Request Utilities ---
This module implements utilities for handling requests. It provides methods
for retrieving data from requests, determining if a request is a POST request,
and getting the IP address from a request.

Author:   tn3w (mail@tn3w.dev)
License:  Apache-2.0 license
"""

from typing import Any, Optional, Final
from urllib.parse import urlparse, urlunparse, urlencode, parse_qs, quote
from flask import Request

try:
    from iputils import is_valid_ip
except ImportError:
    try:
        from utils.iputils import is_valid_ip
    except ImportError:
        from src.BotBlocker.utils.iputils import is_valid_ip


def get_json_data(request: Request, default: Any = None) -> Any:
    """
    Gets the json data of an request.

    Args:
        request Request: An request object from flask.
        default Any: The default value to be
                     returned if there is not json data.

    Return:
        Any: The json data or the default value.
    """

    if not request.is_json:
        return default

    json_data = request.get_json()
    if not isinstance(json_data, (dict, list)):
        return default

    return json_data


def get_url(request: Request) -> str:
    """
    Retrieve the full URL of the request.

    :return: The full URL as a string.
    """

    scheme = request.headers.get('X-Forwarded-Proto', '')
    if scheme not in ['https', 'http']:
        if request.is_secure:
            scheme = 'https'
        else:
            scheme = 'http'

    parsed_url = urlparse(str(request.url))

    query_params = parse_qs(parsed_url.query)
    safe_query = urlencode({k: [quote(v) for v in vs] for k, vs in query_params.items()})

    safe_url = urlunparse(
        (scheme, request.host, parsed_url.path,
         parsed_url.params, safe_query, parsed_url.fragment)
    )

    return safe_url


def is_post(request: Request) -> bool:
    """
    Determine if the given request is a POST request.

    This function checks the HTTP method of the provided request object
    and returns True if the method is 'POST', and False otherwise.

    Args:
        request (Request): The request object to be checked, which is expected
                           to have a 'method' attribute representing the HTTP
                           method of the request.

    Returns:
        bool: True if the request method is 'POST', False otherwise.
    """

    return request.method.lower() == "post"


def is_get(request: Request) -> bool:
    """
    Determine if the given request is a GET request.

    This function checks the HTTP method of the provided request object
    and returns True if the method is 'GET', and False otherwise.

    Args:
        request (Request): The request object to be checked, which is expected
                           to have a 'method' attribute representing the HTTP
                           method of the request.

    Returns:
        bool: True if the request method is 'GET', False otherwise.
    """

    return request.method.lower() == "get"


def is_get_or_post(request: Request) -> bool:
    """
    Determine if the given request is either a GET or POST request.

    This function checks the HTTP method of the provided request object
    and returns True if the method is 'GET' or 'POST', and False otherwise.

    Args:
        request (Request): The request object to be checked, which is expected
                           to have a 'method' attribute representing the HTTP
                           method of the request.

    Returns:
        bool: True if the request method is 'GET' or 'POST', False otherwise.
    """

    return request.method.lower() in ("get", "post")


IP_SOURCS: Final[list[tuple]] = [
    "X-Real-Ip", "CF-Connecting-IP",
    "X-Forwarded-For", "X-Real-IP",
    "X-Cluster-Client-Ip", "X-Forwarded",
    "True-Client-Ip", "X-Appengine-User-Ip",
    "REMOTE_ADDR",
]


def get_ip_address(request: Request) -> Optional[str]:
    """
    Get the IP address from the request.

    :param request: The request object
    :return: The IP address
    """

    ip_list = set()

    for source in IP_SOURCS:
        if source == "REMOTE_ADDR":
            ip = request.remote_addr
            if ip:
                ip_list.add(ip)

            continue

        for i in range(2):
            if i == 1:
                source = source + "-V6"

            for method in ["environ", "headers"]:
                if method == "headers":
                    ip = request.headers.get(source)
                else:
                    source = source.upper().replace("-", "_")
                    for i in range(2):
                        if i == 1:
                            source = "HTTP_" + source

                        ip = request.environ.get(source)

                if ip:
                    ip = ip.split(",")[0] if ',' in ip else ip
                    ip_list.add(ip.strip())

    for ip in ip_list:
        if is_valid_ip(ip):
            return ip

    return None


if __name__ == "__main__":
    print("requestutil.py: This file is not designed to be executed.")
