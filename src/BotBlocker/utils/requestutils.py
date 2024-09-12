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



IP_SOURCES: Final[list[dict]] = [
    {"headers": "CF-Connecting-IP"},
    {"environ": "HTTP_X_REAL_IP"},
    {"environ": "HTTP_CF_CONNECTING_IP"},
    {"environ": "HTTP_X_FORWARDED_FOR"},
    {"headers": "X-Forwarded-For"},
    {"headers": "X-Real-IP"},
    {"headers": "X-Cluster-Client-Ip"},
    {"headers": "X-Forwarded"},
    {"headers": "True-Client-Ip"},
    {"headers": "X-Appengine-User-Ip"},
    {"environ": "REMOTE_ADDR"},
    {"request": "remote_addr"},
    {"environ": "HTTP_X_REAL_IP_V6"},
    {"environ": "HTTP_CF_CONNECTING_IP_V6"},
    {"headers": "CF-Connecting-IP-V6"},
    {"environ": "HTTP_X_FORWARDED_FOR_V6"},
    {"headers": "X-Forwarded-For-V6"},
    {"headers": "X-Real-IP-V6"},
    {"headers": "X-Cluster-Client-Ip-V6"},
    {"headers": "X-Forwarded-V6"},
    {"headers": "True-Client-Ip-V6"},
    {"headers": "X-Appengine-User-Ip-V6"},
    {"environ": "REMOTE_ADDR_V6"},
    {"request": "remote_addr_v6"}
]

def test(request: Request) -> bool:
    ip_list = set()

    for source in IP_SOURCES:
        source_type = list(source.keys())[0]
        source_key = list(source.values())[0]

        if source_type == "environ":
            ip = request.environ.get(source_key)
        elif source_type == "headers":
            ip = request.headers.get(source_key)
        else:
            ip = getattr(request, source_key, None)

        if ip:
            ip_list.add(ip)

    print(ip_list)
    return True


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
                    source = "HTTP_" + source.upper().replace("-", "_")
                    ip = request.environ.get(source)

                if ip:
                    ip_list.add(ip)

    for ip in ip_list:
        if is_valid_ip(ip):
            return ip

    return None


if __name__ == "__main__":
    print("requestutil.py: This file is not designed to be executed.")
