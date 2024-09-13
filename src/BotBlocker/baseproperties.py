from typing import Optional
from flask import request

try:
    from utils.requestutils import get_ip_address
except ImportError:
    from src.BotBlocker.utils.requestutils import get_ip_address


class BaseProperties:
    """
    A class for common properties used in the bot blocker.
    """

    @property
    def client_ip(self) -> Optional[str]:
        """
        Get the IP address of the client.

        Returns:
            Optional[str]: The IP address of the client.
        """

        cached_ip_address = getattr(request, "client_ip_address", None)
        if cached_ip_address is not None:
            return cached_ip_address

        ip_address = get_ip_address(request)
        setattr(request, "client_ip_address", ip_address)

        return ip_address
