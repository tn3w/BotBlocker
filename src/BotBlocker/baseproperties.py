from typing import Optional, Tuple
from flask import request, g

try:
    from utils.requestutils import get_ip_address, get_theme
    from utils.beamutils import get_beam_id, RequestLogger
except ImportError:
    from src.BotBlocker.utils.requestutils import get_ip_address, get_theme
    from src.BotBlocker.utils.beamutils import get_beam_id, RequestLogger


class BaseProperties:
    """
    A class for common properties used in the bot blocker.
    """


    def __init__(self) -> None:
        self.default_settings = {}


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

        beam_id = get_beam_id([self.ip_address, request.user_agent.string])
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
    def theme(self) -> Tuple[Optional[str], bool]:
        """
        Retrieves the current theme and its default status for the bot blocker.

        Returns:
            Tuple[Optional[str], bool]: A tuple containing:
                - The current theme as a string, or None if no theme is set.
                - A boolean indicating whether the current theme is the default theme.
        """

        cached_theme, cached_is_default_theme = getattr(g, "botblocker_theme", (None, None))
        if not None in [cached_theme, cached_is_default_theme]:
            return cached_theme, cached_is_default_theme

        theme, is_default_theme = get_theme(
            request, self.default_settings["without_customization"],
            self.default_settings["theme"]
        )

        setattr(g, "botblocker_theme", (theme, is_default_theme))
        return theme, is_default_theme


    @property
    def ip_address(self) -> Optional[str]:
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
