# -*- coding: utf-8 -*-
import marshmallow as ma

from webargs.compat import MARSHMALLOW_VERSION_INFO


def dict2schema(dct, schema_class=ma.Schema):
    """Generate a `marshmallow.Schema` class given a dictionary of
    `Fields <marshmallow.fields.Field>`.
    """
    attrs = dct.copy()

    class Meta(object):
        if MARSHMALLOW_VERSION_INFO[0] < 3:
            strict = True
        else:
            register = False

    attrs["Meta"] = Meta
    return type(str(""), (schema_class,), attrs)
