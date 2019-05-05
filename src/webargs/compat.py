# -*- coding: utf-8 -*-
# flake8: noqa
import sys

PY2 = int(sys.version_info[0]) == 2

if PY2:
    from collections import Mapping

    basestring = basestring
    text_type = unicode
    iteritems = lambda d: d.iteritems()
else:
    from collections.abc import Mapping

    basestring = (str, bytes)
    text_type = str
    iteritems = lambda d: d.items()
