from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath("../../src"))

project = "dawgtools"
author = "Noah Hoffman"

try:
    import dawgtools  # noqa: F401

    release = dawgtools.__version__
except Exception:
    release = "0.1"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

autodoc_mock_imports = [
    "pyodbc",
    "openai",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

html_theme = "furo"
html_static_path = ["_static"]
