# -*- coding: utf-8 -*-
"""Bottle request argument parsing module.

Example: ::

    from bottle import route, run
    from webargs import Arg
    from webargs.bottleparser import use_args

    hello_args = {
        'name': Arg(str, default='World')
    }
    @route('/', method='GET')
    @use_args(hello_args)
    def index(args):
        return 'Hello ' + args['name']

    if __name__ == '__main__':
        run(debug=True)
"""
import logging

from bottle import request, HTTPError

from webargs import core
from webargs.core import text_type

logger = logging.getLogger(__name__)

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
        logger.error(error)
        status = getattr(error, 'status_code', 400)
        data = getattr(error, 'data', {})
        raise HTTPError(status=status, body=text_type(error),
                        headers=data.get('headers'), exception=error)

    def parse(self, argmap, req=None, *args, **kwargs):
        """Parses the request using the given arguments map.
        Uses Bottle's context-local request object if req=None.
        """
        req_obj = req or request  # Default to context-local request
        return super(BottleParser, self).parse(argmap, req_obj, *args, **kwargs)

parser = BottleParser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs
