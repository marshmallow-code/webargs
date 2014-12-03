# -*- coding: utf-8 -*-
import sys

PY2 = int(sys.version[0]) == 2

if PY2:
    text_type = unicode
    binary_type = str
    string_types = (str, unicode)
    basestring = basestring
else:
    text_type = str
    binary_type = bytes
    string_types = (str,)
    basestring = (str, bytes)
