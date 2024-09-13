from typing import Tuple
from datetime import datetime, timezone
from flask import Flask, request

try:
    from templatecache import TemplateCache
    from utils.requestutils import get_ip_address
    from baseproperties import BaseProperties
except ImportError:
    from src.BotBlocker.templatecache import TemplateCache
    from src.BotBlocker.utils.requestutils import get_ip_address
    from src.BotBlocker.baseproperties import BaseProperties


class BotBlocker(BaseProperties):
    """ 
    A class for blocking bots from accessing the website.
    """


    def __init__(self, app: Flask):
        self.app = app
        self.template_cache = TemplateCache()

        self.add_to_app()


    def add_to_app(self):
        """
        Add the bot blocker to the Flask app.
        """

        app = self.app
        app.before_request(self.access_denied)


    def get_default_replaces(self) -> dict:
        """
        Get the default replacements for the template.

        Returns:
            dict: A dictionary containing the default replacements.
        """

        return {
            "domain": request.host,
            "path": request.path,
            "ray_id": "1111111",
            "client_country": "US",
            "client_ip": " — IP: " + self.client_ip if self.client_ip is not None else "",
            "client_user_agent": request.user_agent.string,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") + " UTC",
        }


    def access_denied(self) -> Tuple[str, int]:
        """
        Render the access denied page.

        Returns:
            Tuple[str, int]: A tuple containing the rendered HTML template and
            the HTTP status code.
        """

        return self.template_cache.render(
            "access_denied.html", **self.get_default_replaces()
        ), 403
