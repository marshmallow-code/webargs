# -*- coding: utf-8 -*-

import sys
import os

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath('..'))
import webargs

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.viewcode',
    'sphinx_issues',
]

primary_domain = 'py'
default_role = 'py:obj'

issues_github_path = 'sloria/webargs'

intersphinx_mapping = {
    'python': ('http://python.readthedocs.org/en/latest/', None),
    'marshmallow': ('http://marshmallow.readthedocs.org/en/latest/', None),
}

# The master toctree document.
master_doc = 'index'

language = 'en'

html_domain_indices = False
templates_path = ['_templates']
source_suffix = '.rst'
project = u'webargs'
copyright = u'2014-2015'
version = release = webargs.__version__
exclude_patterns = ['_build']

# THEME

# Add any paths that contain custom themes here, relative to this directory.
html_theme_path = ['./_themes']
html_theme = 'lucuma'
html_static_path = ['_static']
templates_path = ['_templates']

html_context = {
    'project': project,
    'author': 'Steven Loria',
    'author_url': 'http://stevenloria.com',
    'github': 'https://github.com/sloria/webargs',
    'seo_description': 'A friendly library for parsing HTTP request arguments.',
    'license': 'MIT Licensed',
}
