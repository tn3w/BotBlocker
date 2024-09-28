from typing import Optional
from flask import request, g

try:
    from utils.requestutils import get_ip_address
    from utils.beamutils import get_beam_id, RequestLogger
except ImportError:
    from src.BotBlocker.utils.requestutils import get_ip_address
    from src.BotBlocker.utils.beamutils import get_beam_id, RequestLogger


class BaseProperties:
    """
    A class for common properties used in the bot blocker.
    """


    @property
    def beam_id(self) -> str:
        """
        Retrieves the beam ID associated with the current request.

        Returns:
            str: The generated beam ID based on the client's IP address and user agent.
        """

        cached_beam_id = getattr(g, "botblocker_beam_id", None)
        if cached_beam_id is not None:
            return cached_beam_id

        beam_id = get_beam_id([self.client_ip, request.user_agent.string])
        setattr(g, "botblocker_beam_id", beam_id)

        return beam_id


    @property
    def request_logger(self) -> RequestLogger:
        """
        Gets an instance of RequestLogger initialized with the current beam ID.

        Returns:
            RequestLogger: An instance of RequestLogger that can be used to log requests
            associated with the current beam ID.
        """

        cached_request_logger = getattr(g, "botblocker_request_logger", None)
        if cached_request_logger is not None:
            return cached_request_logger

        request_logger = RequestLogger(self.beam_id)
        setattr(g, "botblocker_request_logger", request_logger)

        return request_logger


    @property
    def client_ip(self) -> Optional[str]:
        """
        Get the IP address of the client.

        Returns:
            Optional[str]: The IP address of the client.
        """

        cached_ip_address = getattr(g, "botblocker_client_ip_address", None)
        if cached_ip_address is not None:
            return cached_ip_address

        ip_address = get_ip_address(request)
        setattr(g, "botblocker_client_ip_address", ip_address)

        return ip_address
