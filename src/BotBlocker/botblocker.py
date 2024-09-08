from typing import Tuple
from datetime import datetime, timezone
from flask import Flask, request

try:
    from templatecache import TemplateCache
except ImportError:
    from src.BotBlocker.templatecache import TemplateCache


class BotBlocker:
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
            "client_ip": "127.0.0.1",
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
