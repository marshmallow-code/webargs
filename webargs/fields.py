# -*- coding: utf-8 -*-
"""Field classes.

Includes all fields from `marshmallow.fields` in addition to a custom
`Nested` field.

All fields can optionally take a special `location` keyword argument, which tells webargs
where to parse the request argument from. ::

    args = {
        'active': fields.Bool(location='query')
        'content_type': fields.Str(load_from='Content-Type',
                                   location='headers')
    }

"""
import marshmallow as ma

from webargs.core import argmap2schema

# Expose all fields from marshmallow.fields.
# We do this instead of 'from marshmallow.fields import *' because webargs
# has its own subclass of Nested
__all__ = []
for each in (field_name for field_name in ma.fields.__all__ if field_name != 'Nested'):
    __all__.append(each)
    globals()[each] = getattr(ma.fields, each)


class Nested(ma.fields.Nested):
    """Same as `marshmallow.fields.Nested`, except can be passed a dictionary as
    the first argument, which will be converted to a `marshmallow.Schema`.
    """

    def __init__(self, nested, *args, **kwargs):
        if isinstance(nested, dict):
            nested = argmap2schema(nested)
        super(Nested, self).__init__(nested, *args, **kwargs)
