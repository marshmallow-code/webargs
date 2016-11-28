# -*- coding: utf-8 -*-
from marshmallow.utils import missing
# Make marshmallow's validation functions importable from webargs
from marshmallow import validate

from webargs.core import argmap2schema, WebargsError, ValidationError
from webargs import fields

__version__ = '1.5.1'
__author__ = 'Steven Loria'
__license__ = 'MIT'


__all__ = (
    'argmap2schema',
    'WebargsError',
    'ValidationError',
    'fields',
    'missing',
    'validate',
)
