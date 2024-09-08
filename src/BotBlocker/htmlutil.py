"""
--- HTML Utilities ---
This module includes utilities for HTML manipulation. It provides methods
for removing unnecessary whitespace, comments, and newlines, while also
minimizing embedded <style> and <script> tags. Additionally, it provides
a method to minimize an HTML template by removing unnecessary whitespace,
comments, and newlines, while also minimizing embedded <style> and <script>
tags.

Author:   tn3w (mail@tn3w.dev)
License:  Apache-2.0 license
"""

import re


def minimize_html(html: str) -> str:
    """
    Minimize an HTML template by removing unnecessary whitespace, comments,
    and newlines, while also minimizing embedded <style> and <script> tags.

    Parameters:
        html (str): The input HTML string to be minimized.

    Returns:
        str: A minimized version of the input HTML string.
    """

    html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)

    def minify_js_css(content: str) -> str:
        content = re.sub(r"\s*([{}:;,])\s*", r"\1", content)
        content = re.sub(r"\s+", " ", content)
        return content.strip()

    def minify_js(content: str) -> str:
        content = re.sub(r"\s*([{}();,:])\s*", r"\1", content)
        content = re.sub(r"\s+", " ", content)
        return content.strip()

    html = re.sub(
        r"(<style.*?>)(.*?)(</style>)",
        lambda m: m.group(1) + minify_js_css(m.group(2)) + m.group(3),
        html, flags=re.DOTALL
    )

    html = re.sub(
        r"(<script.*?>)(.*?)(</script>)",
        lambda m: m.group(1) + minify_js(m.group(2)) + m.group(3),
        html, flags=re.DOTALL
    )

    html = re.sub(r">\s+<", "><", html)
    html = html.strip()

    return html


def minimize_js(js: str) -> str:
    """
    Minimize a JavaScript string by removing unnecessary whitespace, comments,
    and newlines.
    
    Parameters:
        js (str): The input JavaScript string to be minimized.

    Returns:
        str: A minimized version of the input JavaScript string.
    """

    js = re.sub(r"//.*?\n", "", js)
    js = re.sub(r"/\*.*?\*/", "", js, flags=re.DOTALL)

    js = re.sub(r"\s*([{}();,:])\s*", r"\1", js)
    js = re.sub(r"\s+", " ", js)

    return js.strip()


def minimize_css(css: str) -> str:
    """
    Minimize a CSS string by removing unnecessary whitespace, comments,
    and newlines.
    
    Parameters:
        css (str): The input CSS string to be minimized.

    Returns:
        str: A minimized version of the input CSS string.
    """

    css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)

    css = re.sub(r"\s*([{}:;,])\s*", r"\1", css)
    css = re.sub(r"\s+", " ", css)

    return css.strip()


MINIMIZE_FUNCTIONS = {
    "html": minimize_html,
    "js": minimize_js,
    "css": minimize_css
}

def minimize(content: str, file_extension: str) -> str:
    """
    Minimize the provided content based on the file extension.

    Args:
        content (str): The content to be minimized.
        file_extension (str): The file extension of the content.

    Returns:
        str: The minimized content.
    """

    normalized_file_extension = re.sub(r'[^a-zA-Z0-9]', '', file_extension)

    return MINIMIZE_FUNCTIONS.get(normalized_file_extension, minimize_html)(content)


if __name__ == "__main__":
    print("htmlutil.py: This file is not designed to be executed.")
