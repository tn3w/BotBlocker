"""
--- Template Cache ---

A class for caching and minimizing HTML templates. This class provides
a method to retrieve the cached templates for use in rendering. The
cache is automatically loaded when the class is initialized.

Author:   tn3w (mail@tn3w.dev)
License:  Apache-2.0 license
"""

import re
import os

try:
    from src.BotBlocker.utils.fileutils import read
    from src.BotBlocker.utils.htmlutils import minimize_html, minimize
    from src.BotBlocker.utils.consutils import TEMPLATES_DIRECTORY_PATH
except ImportError as exc:
    from utils.fileutils import read
    from utils.htmlutils import minimize_html, minimize
    from utils.consutils import TEMPLATES_DIRECTORY_PATH


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
                template = minimize(asset_file_content, extension)

                rendered_template = re.sub(r'\s+', ' ', template).strip()
                rendered_template = re.sub(r'\s*\{\s*', '{', rendered_template)
                rendered_template = re.sub(r'\s*\}\s*', '}', rendered_template)

                self._assets[file_name] = rendered_template


    def replace_vars(self, template: str, replaces: dict) -> str:
        """
        Replace variables in a template string based on provided replacements.
        
        Args:
            template (str): The template string containing variables and 
                            conditional sections.
            replaces (dict): A dictionary mapping variable names to their 
                            replacement values.
        
        Returns:
            str: The rendered template with variables replaced and 
                unnecessary whitespace removed.
        """

        def evaluate_condition(variable_name: str, content: str) -> str:
            """
            Evaluates a conditional block by checking if the variable exists 
            and is truthy in the 'replaces' dictionary.
            """

            if replaces.get(variable_name):
                return content.strip()

            return ''

        def process_conditions(template: str) -> str:
            """
            Processes all conditionals in the template.
            """

            stack = []
            result = []
            idx = 0
            while idx < len(template):
                if template.startswith("{if ", idx):
                    end_if_idx = template.find('}', idx)
                    var_name = template[idx + 4:end_if_idx].strip()
                    stack.append((var_name, len(result)))
                    idx = end_if_idx + 1
                elif template.startswith("{endif}", idx):
                    if not stack:
                        raise ValueError("Unmatched endif found.")
                    var_name, start_idx = stack.pop()
                    conditional_content = ''.join(result[start_idx:])
                    result = result[:start_idx]
                    result.append(evaluate_condition(var_name, conditional_content))
                    idx += len("{endif}")
                else:
                    result.append(template[idx])
                    idx += 1

            if stack:
                raise ValueError("Unmatched if found.")

            return ''.join(result)

        rendered_template = process_conditions(template)

        sorted_replaces = dict(
            sorted(replaces.items(), key=lambda item: len(item[0]), reverse=True)
        )

        for key, value in sorted_replaces.items():
            if isinstance(value, str):
                key = key.upper()
                rendered_template = rendered_template.replace("{" + key + "}", value)

        rendered_template = re.sub(r'\s+', ' ', rendered_template).strip()
        rendered_template = re.sub(r'\s*\{\s*', '{', rendered_template)
        rendered_template = re.sub(r'\s*\}\s*', '}', rendered_template)

        return rendered_template


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

        assets = {}
        for asset_name, asset in self._assets.items():
            assets[asset_name] = self.replace_vars(asset, kwargs)

        kwargs.update(assets)

        rendered_template = self.replace_vars(template, kwargs)
        return rendered_template


if __name__ == "__main__":
    print("templatecache.py: This file is not designed to be executed.")
