"""
--- Bot Blocker Module ---

This module provides functionalities to block bots from accessing
the website, including methods for client verification, access 
denial handling, and template rendering.

Author:   tn3w (mail@tn3w.dev)
License:  Apache-2.0 license
"""

from urllib.parse import urlparse
from datetime import datetime, timezone
from typing import Final, Union, Tuple, Optional, Dict
from flask import Flask, request, g

try:
    from templatecache import TemplateCache
    from baseproperties import BaseProperties
    from utils.geoiputils import GeoIP, get_geoip
    from utils.utils import get_fields, matches_rule
    from utils.consutils import DATASETS_DIRECTORY_PATH
    from utils.iputils import is_ip_malicious, is_ip_tor
    from utils.requestutils import (
        get_url, get_domain, get_subdomain, get_json_data, is_user_agent_malicious,
        get_http_version, update_url
    )
except ImportError:
    from src.BotBlocker.utils.geoiputils import GeoIP, get_geoip
    from src.BotBlocker.utils.utils import get_fields, matches_rule
    from src.BotBlocker.utils.consutils import DATASETS_DIRECTORY_PATH
    from src.BotBlocker.utils.iputils import is_ip_malicious, is_ip_tor
    from src.BotBlocker.utils.requestutils import (
        get_url, get_domain, get_subdomain, get_json_data, is_user_agent_malicious,
        get_http_version, update_url
    )
    from src.BotBlocker.templatecache import TemplateCache
    from src.BotBlocker.baseproperties import BaseProperties


DEFAULT_THIRD_PARTIES = ["ipapi", "ipintel", "tor_hostname", "tor_exonerator", "geoip"]
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
    "theme": "light", "language": "en", "without_customization": False,
    "without_cookies": False, "without_arg_transfer": False, "without_watermark": False,

    # Miscellaneous
    "debug": False, "third_parties": DEFAULT_THIRD_PARTIES, "host": None
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
        super().__init__()
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
        """
        Retrieves the settings for the bot blocker.

        Returns:
            dict: A dictionary containing the merged settings, including default settings, 
                cached settings, and any modifications based on the defined rules.
        """

        base_settings = self.default_settings.copy()

        cached_settings = getattr(g, "botblocker_settings", None)
        if isinstance(cached_settings, dict):
            base_settings.update(cached_settings)
            return base_settings

        fields = []
        for rule in self.rules:
            fields.extend(get_fields(rule))

        field_data = self.get_field_data(fields)
        for rule, changes in self.rules.items():
            if not matches_rule(rule, field_data):
                continue

            for setting_name, setting_value in changes.items():
                base_settings[setting_name] = setting_value

        g.botblocker_settings = base_settings
        return base_settings


    def get_field_data(self, fields: list) -> dict:
        """
        Collects and returns field data based on the provided fields.

        Args:
            fields (list): A list of fields for which data is to be collected.

        Returns:
            dict: A dictionary containing the collected field data, including basic request 
                information and any additional data based on the specified fields.
        """

        url = get_url(request)
        ip = self.ip_address

        splitted_url = urlparse(url)
        basic_information = {
            "host": request.host, "netloc": splitted_url.netloc,
            "hostname": splitted_url.hostname, "domain": get_domain(url),
            "subdomain": get_subdomain(url), "path": splitted_url.path,
            "endpoint": request.endpoint, "scheme": splitted_url.scheme,
            "args": dict(request.args), "is_json": request.is_json,
            "json": get_json_data(request, {}), "url": url,
            "ip": ip, "user_agent": request.user_agent.string
        }

        third_parties = self.default_settings["third_parties"]

        geoip = None
        for field in fields:
            if field in basic_information:
                continue

            if field == "is_ip_malicious":
                basic_information["is_ip_malicious"] = is_ip_malicious(
                    self.ip_address, third_parties
                )
                continue

            if field == "is_ip_tor":
                basic_information["is_ip_tor"] = is_ip_tor(
                    self.ip_address, third_parties
                )
                continue

            if "geoip" in third_parties:
                if geoip is None:
                    geoip = get_geoip()

                for db_class in geoip.values():
                    db_class: GeoIP
                    if field not in db_class.fields:
                        continue

                    informations = db_class.get(ip)
                    if not isinstance(informations, dict):
                        continue

                    basic_information.update(informations)

        return basic_information


    def get_default_replaces(self) -> dict:
        """
        Get the default replacements for the template.

        Returns:
            dict: A dictionary containing the default replacements.
        """

        client_ip = self.ip_address

        url = get_url(request)

        default_host = self.default_settings["host"]
        host = request.host if default_host is None else default_host

        theme, is_default_theme = self.theme

        return {
            "domain": host,
            "path": request.path,
            "beam_id": self.beam_id,
            "client_country": "US",
            "client_ip": "" if client_ip is None else " — IP: " + client_ip,
            "client_user_agent": request.user_agent.string,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S") + " UTC",
            "without_customization": self.default_settings["without_customization"],
            "without_watermark": self.default_settings["without_watermark"],

            # Urls
            "change_language_url": update_url(url, host, {"change_language": 1}),
            "dark_theme_url": update_url(url, host, {"theme": "dark"}),
            "light_theme_url": update_url(url, host, {"theme": "light"}),

            # Theme
            "is_light": theme == "light" and not is_default_theme,
            "is_dark": theme == "dark" and not is_default_theme,
            "is_default_theme": is_default_theme
        }


    def access_denied(self, without_rerouting: bool = False) -> Tuple[str, int]:
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
        """
        Renders and returns the HTML for a CAPTCHA challenge.

        Returns:
            str: The rendered CAPTCHA HTML as a string.
        """

        return self.template_cache.render("oneclick_captcha.html", **self.get_default_replaces())


    def end_log(self, action_taken: str) -> None:
        """
        Logs the end of a request with relevant information.

        Args:
        action_taken (str): A description of the action that was taken by the user, 
            which will be logged for tracking and auditing purposes.
        """

        self.request_logger.log(
            end_of_information = True, ip_address = self.ip_address,
            user_agent = request.user_agent.string, http_version = get_http_version(request),
            action_taken = action_taken
        )


    def get_suspicious_response(self, settings: Optional[dict] = None) -> str:
        """
        Determines the appropriate response for a suspicious request based on the provided settings.

        Args:
            settings (Optional[dict]): A dictionary containing configuration settings for handling
            suspicious responses. If None, the instance's default settings are used.

        Returns:
            str: A response indicating either access denial or a CAPTCHA challenge.
        """

        if settings is None:
            settings = self.settings

        if settings["action"] == "block_if_suspicious":
            self.end_log("block")
            return self.access_denied()

        self.end_log("captcha")
        return self.captcha()


    def check_client(self) -> Optional[str]:
        """
        Checks the client's request against various security
        measures and determines the appropriate response.

        Returns:
            Optional[str]: A response indicating either access denial,
                a CAPTCHA challenge, or None if the client is safe.
        """

        settings = self.settings
        third_parties = settings["third_parties"]

        logger = self.request_logger
        if settings["action"] == "allow":
            self.end_log("allow")
            return

        if settings["action"] == "block":
            self.end_log("block")
            return self.access_denied()

        if settings["action"] == "fight":
            self.end_log("captcha")
            return self.captcha()

        if is_user_agent_malicious(request, settings["enable_crawler_block"], logger):
            return self.get_suspicious_response()

        client_ip = self.ip_address

        if client_ip is None:
            logger.log(ip_address = client_ip, malicious = True, service = "ipnone")
            return self.get_suspicious_response()

        if is_ip_malicious(client_ip, third_parties, logger):
            return self.get_suspicious_response()

        if is_ip_tor(client_ip, third_parties, logger):
            return self.get_suspicious_response()

        self.end_log("allow")
        return
