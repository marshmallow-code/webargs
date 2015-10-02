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

__all__ = [
    'Nested',
    'DelimitedList',
]
# Expose all fields from marshmallow.fields.
# We do this instead of 'from marshmallow.fields import *' because webargs
# has its own subclass of Nested
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

class DelimitedList(ma.fields.List):
    """Same as `marshmallow.fields.List`, except can load from either a list or
    a delimited string (e.g. "foo,bar,baz").

    :param Field cls_or_instance: A field class or instance.
    :param str delimiter: Delimiter between values.
    :param bool as_string: Dump values to string.
    """

    delimiter = ','

    def __init__(self, cls_or_instance, delimiter=None, as_string=False, **kwargs):
        self.delimiter = delimiter or self.delimiter
        self.as_string = as_string
        super(DelimitedList, self).__init__(cls_or_instance, **kwargs)

    def _serialize(self, value, attr, obj):
        ret = super(DelimitedList, self)._serialize(value, attr, obj)
        if self.as_string:
            return self.delimiter.join(format(each) for each in value)
        return ret

    def _deserialize(self, value, attr, data):
        ret = (
            value
            if ma.utils.is_iterable_but_not_string(value)
            else value.split(self.delimiter)
        )
        return super(DelimitedList, self)._deserialize(ret, attr, data)
