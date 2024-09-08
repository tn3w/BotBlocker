from typing import Tuple
from datetime import datetime
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


    def access_denied(self) -> Tuple[str, int]:
        """
        Render the access denied page.

        Returns:
            Tuple[str, int]: A tuple containing the rendered HTML template and
            the HTTP status code.
        """

        replaces = {
            "domain": request.host,
            "path": request.path,
            "ray_id": "1111111",
            "client_country": "US",
            "client_ip": "127.0.0.1",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " UTC",
        }

        return self.template_cache.render("access_denied.html", **replaces), 403
