"""
--- Request Utils ---

This module implements utilities for handling requests. It provides methods
for retrieving data from requests, determining if a request is a POST request,
and getting the IP address from a request.

Author:   tn3w (mail@tn3w.dev)
License:  Apache-2.0 license
"""

import re
from typing import Optional, Final, Tuple, Any
from urllib.parse import urlparse, urlunparse, urlencode, parse_qs, quote
from flask import Request, g

try:
    from useragentutils import is_user_agent_crawler
    from iputils import is_valid_ip, is_ipv4, is_ipv6
    from utils import is_float, Logger
except ImportError:
    try:
        from utils.utils import is_float, Logger
        from utils.useragentutils import is_user_agent_crawler
        from utils.iputils import is_valid_ip, is_ipv4, is_ipv6
    except ImportError:
        from src.BotBlocker.utils.utils import is_float, Logger
        from src.BotBlocker.utils.useragentutils import is_user_agent_crawler
        from src.BotBlocker.utils.iputils import is_valid_ip, is_ipv4, is_ipv6


USER_AGENT_PATTERN: Final[str] = (
    r"^Mozilla/\d+\.\d+"
    r" \([^)]+\)"
    r" .+?/[\d\.]+.*"
)
USER_AGENT_REGEX: Final[re.Pattern] = re.compile(USER_AGENT_PATTERN)


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

    scheme = request.headers.get("X-Forwarded-Proto", "")
    if scheme not in ["https", "http"]:
        if request.is_secure:
            scheme = "https"
        else:
            scheme = "http"

    parsed_url = urlparse(str(request.url))

    query_params = parse_qs(parsed_url.query)
    safe_query = urlencode({k: [quote(v) for v in vs] for k, vs in query_params.items()})

    safe_url = urlunparse(
        (scheme, request.host, parsed_url.path,
         parsed_url.params, safe_query, parsed_url.fragment)
    )

    return safe_url


def get_domain(url: str) -> str:
    """
    Extracts the domain from a given HTTP request.

    Args:
        url (str): The URL from which to extract the domain.

    Returns:
        str: The extracted domain name from the request URL.
    """

    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    parsed_url = urlparse(url)
    netloc = parsed_url.netloc

    if ":" in netloc:
        netloc = netloc.split(":")[0]

    domain_parts = netloc.split(".")
    if all(part.isdigit() for part in netloc.split(".")):
        return netloc

    if len(domain_parts) > 2:
        domain = ".".join(domain_parts[-2:])
    else:
        domain = netloc

    return domain


def get_subdomain(url: str) -> Optional[str]:
    """
    Extracts the subdomain from a given URL.

    Args:
        url (str): The URL from which to extract the subdomain.

    Returns:
        str: The extracted subdomain, or an empty string if no subdomain exists.
    """

    parsed_url = urlparse(url)
    netloc = parsed_url.netloc

    if is_ipv4(parsed_url.hostname) or is_ipv6(parsed_url.hostname):
        return None

    if ":" in netloc:
        netloc = netloc.split(":")[0]

    domain_parts = netloc.split(".")

    if len(domain_parts) > 2:
        subdomain = ".".join(domain_parts[:-2])
        return subdomain

    return None


def update_url(original_url: str, new_host: Optional[str] = None,
               param_to_add: Optional[dict] = None, params_to_remove: Optional[list] = None) -> str:
    """
    Updates the given URL by optionally changing the host,
    adding query parameters, or removing specific query parameters.

    Args:
        original_url (str): The original URL to be updated.
        new_host (Optional[str]): A new host to replace the current one in the URL.
            If None, the original host is retained.
        param_to_add (Optional[dict]): A dictionary of query parameters to add or update in the URL. 
            Keys represent parameter names and values represent the values for those parameters.
        params_to_remove (Optional[list]): A list of query parameters to
            remove from the URL if they exist.

    Returns:
        str: The updated URL with any changes applied.
    """

    parsed_url = urlparse(original_url)
    new_netloc = new_host if new_host else parsed_url.netloc

    query_params = parse_qs(parsed_url.query)

    for key in query_params:
        query_params[key] = [v.strip("[]'\"") for v in query_params[key]]


    if params_to_remove:
        for param in params_to_remove:
            query_params.pop(param, None)

    if param_to_add:
        for key, value in param_to_add.items():
            query_params[key] = value

    new_query = urlencode(query_params, doseq=True)

    new_url = urlunparse((
        parsed_url.scheme,
        new_netloc,
        parsed_url.path,
        parsed_url.params,
        new_query,
        parsed_url.fragment
    ))

    return new_url


def get_theme(request: Request, without_customization: bool = False,
              default: str = "light") -> Tuple[Optional[str], bool]:
    """
    Retrieve the theme setting.

    Args:
        request (Request): The request object to be checked, which is expected
                           to have a "method" attribute representing the HTTP
                           method of the request.
        without_customization (bool): Flag to allow theme customization.
        default (str): The default theme if none is set.

    Return:
        Tuple[Optional[str], bool]: A tuple containing the theme and a
            boolean indicating if the default theme is used.
    """

    theme = None
    if not without_customization:
        theme_from_args = request.args.get("theme")
        theme_from_cookies = request.cookies.get("theme")
        theme_from_form = request.form.get("theme")

        theme = (
            theme_from_args
            if theme_from_args in ["light", "dark"]
            else (
                theme_from_cookies
                if theme_from_cookies in ["light", "dark"]
                else (
                    theme_from_form
                    if theme_from_form in ["light", "dark"]
                    else None
                )
            )
        )

    if theme is None:
        return default, True

    return theme, False


def is_post(request: Request) -> bool:
    """
    Determine if the given request is a POST request.

    This function checks the HTTP method of the provided request object
    and returns True if the method is "POST", and False otherwise.

    Args:
        request (Request): The request object to be checked, which is expected
                           to have a "method" attribute representing the HTTP
                           method of the request.

    Returns:
        bool: True if the request method is "POST", False otherwise.
    """

    return request.method.lower() == "post"


def is_get(request: Request) -> bool:
    """
    Determine if the given request is a GET request.

    This function checks the HTTP method of the provided request object
    and returns True if the method is "GET", and False otherwise.

    Args:
        request (Request): The request object to be checked, which is expected
                           to have a "method" attribute representing the HTTP
                           method of the request.

    Returns:
        bool: True if the request method is "GET", False otherwise.
    """

    return request.method.lower() == "get"


def is_get_or_post(request: Request) -> bool:
    """
    Determine if the given request is either a GET or POST request.

    This function checks the HTTP method of the provided request object
    and returns True if the method is "GET" or "POST", and False otherwise.

    Args:
        request (Request): The request object to be checked, which is expected
                           to have a "method" attribute representing the HTTP
                           method of the request.

    Returns:
        bool: True if the request method is "GET" or "POST", False otherwise.
    """

    return request.method.lower() in ("get", "post")


def get_http_version(request: Request) -> Optional[float]:
    """
    Extracts the HTTP version from the given request object.

    Args:
        request (Request): The request object containing the environment 
                           information.

    Returns:
        Optional[float]: The HTTP version as a float (e.g., 1.1, 2.0), 
                         or None if the version cannot be determined.
    """

    server_protocol = request.environ.get("SERVER_PROTOCOL")

    if not server_protocol:
        return None

    match = re.search(r"HTTP/(\d\.\d|\d)", server_protocol)

    if not match:
        return None

    first_match_group = match.group(1)
    if not is_float(first_match_group):
        return None

    return float(first_match_group)


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
                    ip = ip.split(",")[0] if "," in ip else ip
                    ip_list.add(ip.strip())

    for ip in ip_list:
        if is_valid_ip(ip):
            return ip

    return None


def is_user_agent_malicious(request: Request, check_for_crawlers: bool = False,
                            logger: Optional[Logger] = None) -> bool:
    """
    Determine if the user agent from the given request is malicious.

    Args:
        request (Request): The HTTP request object containing user agent information.
        check_for_crawlers (bool): If set to True, the function will also check if the 
                                    user agent is a known web crawler. Defaults to False.

    Returns:
        bool: True if the user agent is considered malicious, False otherwise.
    """

    user_agent = request.user_agent.string

    if not isinstance(user_agent, str) or user_agent.strip() == "":
        if logger is not None:
            logger.log(user_agent = user_agent, malicious = True, service = "uanone")

        return True

    if bool(USER_AGENT_REGEX.match(user_agent)) is False:
        if logger is not None:
            logger.log(user_agent = user_agent, malicious = True, service = "uainvalid")

        return True

    if check_for_crawlers:
        if is_user_agent_crawler(user_agent):
            if logger is not None:
                logger.log(user_agent = user_agent, malicious = True, service = "uacrawler")

            return True

    return False


if __name__ == "__main__":
    print("requestutil.py: This file is not designed to be executed.")
