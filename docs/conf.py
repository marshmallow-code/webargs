import datetime as dt
import sys
import os

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath(os.path.join("..", "src")))
import webargs  # noqa

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_issues",
]

primary_domain = "py"
default_role = "py:obj"

github_user = "marshmallow-code"
github_repo = "webargs"

issues_github_path = f"{github_user}/{github_repo}"

intersphinx_mapping = {
    "python": ("http://python.readthedocs.io/en/latest/", None),
    "marshmallow": ("http://marshmallow.readthedocs.io/en/latest/", None),
}

# The master toctree document.
master_doc = "index"

language = "en"

html_domain_indices = False
source_suffix = ".rst"
project = "webargs"
copyright = f"2014-{dt.datetime.utcnow():%Y}, Steven Loria and contributors"
version = release = webargs.__version__
templates_path = ["_templates"]
exclude_patterns = ["_build"]

# THEME

html_theme = "furo"

html_theme_options = {
    "light_css_variables": {"color-brand-primary": "#268bd2"},
    "description": "Declarative parsing and validation of HTTP request objects.",
}
html_logo = "_static/logo.png"

html_context = {
    "tidelift_url": (
        "https://tidelift.com/subscription/pkg/pypi-webargs"
        "?utm_source=pypi-webargs&utm_medium=referral&utm_campaign=docs"
    ),
    "donate_url": "https://opencollective.com/marshmallow",
}
html_sidebars = {
    "*": [
        "sidebar/scroll-start.html",
        "sidebar/brand.html",
        "sidebar/search.html",
        "sidebar/navigation.html",
        "donate.html",
        "sponsors.html",
        "sidebar/ethical-ads.html",
        "sidebar/scroll-end.html",
    ]
}
