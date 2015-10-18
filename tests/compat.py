# -*- coding: utf-8 -*-
import sys

PY2 = int(sys.version[0]) == 2

if PY2:
    text_type = unicode  # flake8: noqa
    binary_type = str
    string_types = (str, unicode)  # flake8: noqa
    basestring = basestring  # flake8: noqa
else:
    text_type = str
    binary_type = bytes
    string_types = (str,)
    basestring = (str, bytes)
