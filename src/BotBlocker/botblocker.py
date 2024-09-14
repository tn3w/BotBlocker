from typing import Tuple, Optional
from datetime import datetime, timezone
from flask import Flask, request

try:
    from templatecache import TemplateCache
    from baseproperties import BaseProperties
    from utils.iputils import is_ip_malicious, is_ip_tor
except ImportError:
    from src.BotBlocker.templatecache import TemplateCache
    from src.BotBlocker.baseproperties import BaseProperties
    from src.BotBlocker.utils.iputils import is_ip_malicious, is_ip_tor


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
        app.before_request(self.check_client)


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


    def check_client(self) -> Optional[str]:
        client_ip = self.client_ip

        if client_ip is None:
            return self.access_denied()

        if is_ip_malicious(client_ip):
            return self.access_denied()

        if is_ip_tor(client_ip):
            return self.access_denied()

        return None
