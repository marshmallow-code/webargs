# -*- coding: utf-8 -*-
from marshmallow.utils import missing

# Make marshmallow's validation functions importable from webargs
from marshmallow import validate

from webargs.core import dict2schema, ValidationError
from webargs import fields

__version__ = "5.2.0"
__author__ = "Steven Loria"
__license__ = "MIT"


__all__ = ("dict2schema", "ValidationError", "fields", "missing", "validate")
