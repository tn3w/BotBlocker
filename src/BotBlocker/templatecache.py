"""
--- Template Cache ---
A class for caching and minimizing HTML templates. This class provides
a method to retrieve the cached templates for use in rendering. The
cache is automatically loaded when the class is initialized.

Author:   tn3w (mail@tn3w.dev)
License:  Apache-2.0 license
"""

import os

try:
    from src.BotBlocker.cons import TEMPLATES_DIRECTORY_PATH
    from src.BotBlocker.util.fileutil import read
    from src.BotBlocker.util.htmlutil import minimize_html, minimize
except ImportError as exc:
    from cons import TEMPLATES_DIRECTORY_PATH
    from util.fileutil import read
    from util.htmlutil import minimize_html, minimize


class TemplateCache:
    """
    A class for caching and minimizing HTML templates.
    """


    def __init__(self, template_dir: str = TEMPLATES_DIRECTORY_PATH) -> None:
        """
        Initialize the TemplateCache instance.
        """

        self.template_dir = template_dir
        self.assets_dir = None

        self._templates = {}
        self._assets = {}

        self._load()


    def _load(self) -> None:
        """
        Load templates from the specified directory into the cache.

        This private method reads all template files from the template directory,
        minimizes their HTML content, and stores them in the internal cache.
        """

        if not os.path.isdir(TEMPLATES_DIRECTORY_PATH):
            return

        for template_file_name in os.listdir(TEMPLATES_DIRECTORY_PATH):
            template_file_path = os.path.join(TEMPLATES_DIRECTORY_PATH, template_file_name)

            template_file_content = read(template_file_path)
            if template_file_content is None:
                continue

            minimized_template = minimize_html(template_file_content)
            self._templates[template_file_name] = minimized_template

        if self.assets_dir is None:
            self.assets_dir = os.path.join(self.template_dir, "assets")

        if os.path.isdir(self.assets_dir):
            for asset_file_name in os.listdir(self.assets_dir):
                asset_file_path = os.path.join(self.assets_dir, asset_file_name)

                asset_file_content = read(asset_file_path)
                if asset_file_content is None:
                    continue

                file_name, extension = os.path.splitext(asset_file_name)[:2]
                self._assets[file_name] = minimize(asset_file_content, extension)

        print(self._assets)


    def render(self, template_name: str, **kwargs) -> str:
        """
        Render the specified template with the provided keyword arguments.

        Args:
            template_name (str): The name of the template to render.
            **kwargs: The keyword arguments to pass to the template.

        Returns:
            str: The rendered template.
        """

        template = self._templates.get(template_name)
        if template is None:
            return ""

        kwargs.update(self._assets)

        sorted_kwargs = dict(
            sorted(
                kwargs.items(),
                key=lambda item: len(item[0]),
                reverse=True
            )
        )

        for key, value in sorted_kwargs.items():
            key = key.upper()

            template = template.replace("{" + key + "}", value)

        return template


if __name__ == "__main__":
    print("templatecache.py: This file is not designed to be executed.")
