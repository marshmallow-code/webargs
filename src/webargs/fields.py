"""Field classes.

Includes all fields from `marshmallow.fields` in addition to a custom
`Nested` field and `DelimitedList`.

All fields can optionally take a special `location` keyword argument, which
tells webargs where to parse the request argument from.

.. code-block:: python

    args = {
        "active": fields.Bool(location="query"),
        "content_type": fields.Str(data_key="Content-Type", location="headers"),
    }
"""
from __future__ import annotations

import marshmallow as ma

# Expose all fields from marshmallow.fields.
from marshmallow.fields import *  # noqa: F40

__all__ = ["DelimitedList", "DelimitedTuple"] + ma.fields.__all__


# TODO: remove custom `Nested` in the next major release
#
# the `Nested` class is only needed on versions of marshmallow prior to v3.15.0
# in that version, `ma.fields.Nested` gained the ability to consume dict inputs
# prior to that, this subclass adds this capability
#
# if we drop support for ma.__version_info__ < (3, 15) we can do this
class Nested(ma.fields.Nested):  # type: ignore[no-redef]
    """Same as `marshmallow.fields.Nested`, except can be passed a dictionary as
    the first argument, which will be converted to a `marshmallow.Schema`.

    .. note::

        The schema class here will always be `marshmallow.Schema`, regardless
        of whether a custom schema class is set on the parser. Pass an explicit schema
        class if necessary.
    """

    def __init__(self, nested, *args, **kwargs):
        if isinstance(nested, dict):
            nested = ma.Schema.from_dict(nested)
        super().__init__(nested, *args, **kwargs)


class DelimitedFieldMixin:
    """
    This is a mixin class for subclasses of ma.fields.List and ma.fields.Tuple
    which split on a pre-specified delimiter. By default, the delimiter will be ","

    Because we want the MRO to reach this class before the List or Tuple class,
    it must be listed first in the superclasses

    For example, a DelimitedList-like type can be defined like so:

    >>> class MyDelimitedList(DelimitedFieldMixin, ma.fields.List):
    >>>     pass
    """

    delimiter: str = ","
    # delimited fields set is_multiple=False for webargs.core.is_multiple
    is_multiple: bool = False

    def _serialize(self, value, attr, obj, **kwargs):
        # serializing will start with parent-class serialization, so that we correctly
        # output lists of non-primitive types, e.g. DelimitedList(DateTime)
        return self.delimiter.join(
            format(each) for each in super()._serialize(value, attr, obj, **kwargs)
        )

    def _deserialize(self, value, attr, data, **kwargs):
        # attempting to deserialize from a non-string source is an error
        if not isinstance(value, (str, bytes)):
            raise self.make_error("invalid")
        values = value.split(self.delimiter) if value else []
        return super()._deserialize(values, attr, data, **kwargs)


class DelimitedList(DelimitedFieldMixin, ma.fields.List):
    """A field which is similar to a List, but takes its input as a delimited
    string (e.g. "foo,bar,baz").

    Like List, it can be given a nested field type which it will use to
    de/serialize each element of the list.

    :param Field cls_or_instance: A field class or instance.
    :param str delimiter: Delimiter between values.
    """

    default_error_messages = {"invalid": "Not a valid delimited list."}

    def __init__(
        self,
        cls_or_instance: ma.fields.Field | type,
        *,
        delimiter: str | None = None,
        **kwargs,
    ):
        self.delimiter = delimiter or self.delimiter
        super().__init__(cls_or_instance, **kwargs)


class DelimitedTuple(DelimitedFieldMixin, ma.fields.Tuple):
    """A field which is similar to a Tuple, but takes its input as a delimited
    string (e.g. "foo,bar,baz").

    Like Tuple, it can be given a tuple of nested field types which it will use to
    de/serialize each element of the tuple.

    :param Iterable[Field] tuple_fields: An iterable of field classes or instances.
    :param str delimiter: Delimiter between values.
    """

    default_error_messages = {"invalid": "Not a valid delimited tuple."}

    def __init__(self, tuple_fields, *, delimiter: str | None = None, **kwargs):
        self.delimiter = delimiter or self.delimiter
        super().__init__(tuple_fields, **kwargs)
