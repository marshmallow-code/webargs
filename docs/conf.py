# -*- coding: utf-8 -*-
import datetime as dt
import sys
import os
import sphinx_typlog_theme

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath(".."))
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

issues_github_path = "{}/{}".format(github_user, github_repo)

intersphinx_mapping = {
    "python": ("http://python.readthedocs.io/en/latest/", None),
    "marshmallow": ("http://marshmallow.readthedocs.io/en/latest/", None),
}

# The master toctree document.
master_doc = "index"

language = "en"

html_domain_indices = False
source_suffix = ".rst"
project = u"webargs"
copyright = u"2014-{0:%Y}, Steven Loria and contributors".format(dt.datetime.utcnow())
version = release = webargs.__version__
exclude_patterns = ["_build"]

# THEME

# Add any paths that contain custom themes here, relative to this directory.
html_theme = "sphinx_typlog_theme"
html_theme_path = [sphinx_typlog_theme.get_path()]

html_theme_options = {
    "logo_name": "webargs",
    "description": "A friendly library for parsing HTTP request arguments.",
    "github_user": github_user,
    "github_repo": github_repo,
}

html_sidebars = {"**": ["logo.html", "github.html", "globaltoc.html", "searchbox.html"]}
