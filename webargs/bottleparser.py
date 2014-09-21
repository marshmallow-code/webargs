# -*- coding: utf-8 -*-
"""Bottle request argument parsing module.

Example: ::

    from bottle import route
    from webargs import Arg
    from webargs.bottleparser import use_args

    hello_args = {
        'name': Arg(str, default='World')
    }

    @route('/', method=['GET', 'POST'])
    @use_args(hello_args)
    def index(args)
        return 'Hello ' + args['name']
"""
from bottle import abort, request

from webargs import core


class BottleParser(core.Parser):
    """Bottle.py request argument parser."""

    def parse_querystring(self, req, name, arg):
        """Pull a querystring value from the request."""
        return core.get_value(req.query, name, arg.multiple)

    def parse_form(self, req, name, arg):
        """Pull a form value from the request."""
        return core.get_value(req.forms, name, arg.multiple)

    def parse_json(self, req, name, arg):
        """Pull a json value from the request."""
        try:
            return core.get_value(req.json, name, arg.multiple)
        except (AttributeError, ValueError):
            pass
        return core.Missing

    def parse_headers(self, req, name, arg):
        """Pull a value from the header data."""
        return core.get_value(req.headers, name, arg.multiple)

    def parse_cookies(self, req, name, arg):
        """Pull a value from the cookiejar."""
        return req.get_cookie(name)

    def parse_files(self, req, name, arg):
        """Pull a file from the request."""
        return core.get_value(req.files, name, arg.multiple)

    def handle_error(self, error):
        """Handles errors during parsing. Aborts the current request with a
        400 error.
        """
        return abort(400, str(error))

    def parse(self, argmap, req=None, *args, **kwargs):
        """Parses the request using the given arguments map.
        Uses Bottle's context-local request object if req=None.
        """
        req_obj = req or request  # Default to context-local request
        return super(BottleParser, self).parse(argmap, req_obj, *args, **kwargs)

parser = BottleParser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs
