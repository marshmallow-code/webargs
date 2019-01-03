# -*- coding: utf-8 -*-
from marshmallow.utils import missing

# Make marshmallow's validation functions importable from webargs
from marshmallow import validate

from webargs.core import argmap2schema, dict2schema, WebargsError, ValidationError
from webargs import fields

__version__ = "4.4.1"
__author__ = "Steven Loria"
__license__ = "MIT"


__all__ = (
    "dict2schema",
    "argmap2schema",
    "WebargsError",
    "ValidationError",
    "fields",
    "missing",
    "validate",
)
