# -*- coding: utf-8 -*-
"""Field classes.

Includes all fields from `marshmallow.fields` in addition to a custom
`Nested` field `DelimitedList`, and `DelimitedPaths`.

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
    'DelimitedPaths',
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
        try:
            ret = (
                value
                if ma.utils.is_iterable_but_not_string(value)
                else value.split(self.delimiter)
            )
        except AttributeError:
            self.fail('invalid')
        return super(DelimitedList, self)._deserialize(ret, attr, data)


class DelimitedPaths(DelimitedList):
    """
    Convert a potentially overlapping jsonapi include list like:
    ``'funder.users,investments.allocations.report,investments.grantee,investments.invitation,services'``

    Into a nested dict structure like::

        {'funder': {'users': {}},
         'investments': {'allocations': {'report': {}},
                         'grantee': {},
                         'invitation': {}},
         'services': {}}

    :param str glue: Delimiter between values.
    """
    glue = '.'

    def __init__(self, glue=None, **kwargs):
        self.glue = glue or self.glue
        # Force inner list to be made of Strings
        cls_or_instance = ma.fields.String()
        super(DelimitedPaths, self).__init__(cls_or_instance, **kwargs)

    def _serialize(self, value, attr, obj):
        # Nest this function because I'm not going to test all the optional parameters.
        def recursive_flatten_dict(in_dict, out_list=None, prefix=None):
            """
            Reduce a nested dict to a list with compound keys using the glue.
            :param dict in_dict: the nested dict to flatten.
            :param list out_list: Optional list to append paths from in_dict.
            :param list prefix: a list of parent keys to glue together to prefix to
                                the new key.
            :return: list with all the keys glued together.
            :rtype: list
            """
            if not isinstance(out_list, list):
                out_list = []
            if not isinstance(prefix, list):
                prefix = []
            for key, value in in_dict.items():
                if key == '':
                    raise TypeError('Cannot flatten empty string keys')
                if value:
                    recursive_flatten_dict(value, out_list, prefix + [key])
                else:
                    out_list.append(self.glue.join(prefix + [key]))
            return out_list

        value = recursive_flatten_dict(value)
        # Because these come from unordered dicts tox py2 tests fail without sorting
        value.sort()

        return super(DelimitedPaths, self)._serialize(value, attr, obj)

    def _deserialize(self, value, attr, data):
        if value == {} or value == []:
            return {}

        delimited_list = super(DelimitedPaths, self)._deserialize(value, attr, data)

        paths = {}
        if delimited_list is not None:
            for path in delimited_list:
                keys = path.split(self.glue)
                pointer = paths
                for k in keys:
                    if k not in pointer:
                        pointer[k] = {}
                    pointer = pointer[k]
        return paths
