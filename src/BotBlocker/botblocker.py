"""
--- Bot Blocker Module ---
This module provides functionalities to block bots from accessing
the website, including methods for client verification, access 
denial handling, and template rendering.

Author:   tn3w (mail@tn3w.dev)
License:  Apache-2.0 license
"""

from datetime import datetime, timezone
from typing import Final, Union, Tuple, Optional, Dict
from flask import Flask, request, g

try:
    from templatecache import TemplateCache
    from baseproperties import BaseProperties
    from utils.consutils import DATASETS_DIRECTORY_PATH
    from utils.iputils import is_ip_malicious, is_ip_tor
except ImportError:
    from src.BotBlocker.templatecache import TemplateCache
    from src.BotBlocker.utils.consutils import DATASETS_DIRECTORY_PATH
    from src.BotBlocker.baseproperties import BaseProperties
    from src.BotBlocker.utils.iputils import is_ip_malicious, is_ip_tor


DEFAULT_THIRD_PARTIES = ["ipapi", "ipintel", "hostnameresolve", "exonerator"]
DEFAULT_SETTINGS: Final[Dict[str, Union[str, int, bool]]] = {
    # Action and Configuration
    "action": "auto", "captcha_type": "oneclick", "hardness": 1, "verification_age": 3600,
    "store_anonymously": True, "as_route": False, "route_extension": "_captchaify",

    # Dataset Parameters
    "dataset": "keys", "dataset_size": (20, 100), "dataset_dir": DATASETS_DIRECTORY_PATH,

    # Rate Limiting
    "enable_rate_limit": False, "rate_limit": (15, 300),

    # Queue
    "enable_queue": False, "client_limit": 20,

    # Crawlers
    "enable_crawler_block": False, "crawler_hints": True,

    # TrueClick
    "enable_trueclick": False, "trueclick_hardness": 2,

    # Error Handling
    "enable_error_handling": False, "errors": None,

    # Customization and Options
    "theme": "light", "language": "en", "without_customisation": False,
    "without_cookies": False, "without_arg_transfer": False, "without_watermark": False,

    # Miscellaneous
    "debug": False, "third_parties": DEFAULT_THIRD_PARTIES
}


class BotBlocker(BaseProperties):
    """ 
    A class for blocking bots from accessing the website.
    """


    @staticmethod
    def _normalize_default_settings(default_settings: Optional[Dict[str, str]] = None):
        if not isinstance(default_settings, dict):
            return DEFAULT_SETTINGS

        new_default_settings = DEFAULT_SETTINGS.copy()
        new_default_settings.update(default_settings)

        return new_default_settings


    def __init__(self, app: Flask, default_settings: Optional[Dict[str, str]] = None,
                 rules: Optional[Dict[tuple, dict]] = None) -> None:
        self.initialized = True

        self.app = app
        self.default_settings = self._normalize_default_settings(default_settings)

        if not isinstance(rules, dict):
            rules = {}
        self.rules = rules

        self.template_cache = TemplateCache()

        self.add_to_app()


    def add_to_app(self):
        """
        Add the bot blocker to the Flask app.
        """

        if getattr(self, "initialized", None) is not True:
            self.default_settings = DEFAULT_SETTINGS
            self.rules = {}

            self.initialized = True

        app = self.app
        app.before_request(self.check_client)


    @property
    def settings(self) -> dict:
        base_settings = self.default_settings.copy()

        cached_settings = getattr(g, "captchaify_settings", None)
        if isinstance(cached_settings, dict):
            base_settings.update(cached_settings)
            return base_settings




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


    def captcha(self) -> str:
        return "Here should be an Captcha!"


    def check_client(self) -> Optional[str]:
        client_ip = self.client_ip

        if client_ip is None:
            return self.access_denied()

        if is_ip_malicious(client_ip):
            return self.captcha()

        if is_ip_tor(client_ip):
            return self.captcha()

        return None
