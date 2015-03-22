# -*- coding: utf-8 -*-
import sys
import os

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath('..'))
import webargs
sys.path.append(os.path.abspath("_themes"))
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.viewcode', 'sphinx_issues']
primary_domain = 'py'
default_role = 'py:obj'
issues_github_path = 'sloria/webargs'
templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'
project = u'webargs'
copyright = u'2014-2015'
version = release = webargs.__version__
exclude_patterns = ['_build']
pygments_style = 'flask_theme_support.FlaskyStyle'
html_theme = 'kr_small'
html_theme_path = ['_themes']
