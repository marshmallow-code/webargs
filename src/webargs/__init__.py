# -*- coding: utf-8 -*-
from distutils.version import LooseVersion
from marshmallow.utils import missing

# Make marshmallow's validation functions importable from webargs
from marshmallow import validate

from webargs.core import dict2schema, ValidationError
from webargs import fields

__version__ = "5.4.0"
__version_info__ = tuple(LooseVersion(__version__).version)
__author__ = "Steven Loria"
__license__ = "MIT"


__all__ = ("dict2schema", "ValidationError", "fields", "missing", "validate")
