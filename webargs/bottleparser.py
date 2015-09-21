# -*- coding: utf-8 -*-
"""Bottle request argument parsing module.

Example: ::

    from bottle import route, run
    from marshmallow import fields
    from webargs.bottleparser import use_args

    hello_args = {
        'name': fields.Str(missing='World')
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

logger = logging.getLogger(__name__)

class BottleParser(core.Parser):
    """Bottle.py request argument parser."""

    def parse_querystring(self, req, name, field):
        """Pull a querystring value from the request."""
        return core.get_value(req.query, name, core.is_multiple(field))

    def parse_form(self, req, name, field):
        """Pull a form value from the request."""
        return core.get_value(req.forms, name, core.is_multiple(field))

    def parse_json(self, req, name, field):
        """Pull a json value from the request."""
        try:
            return core.get_value(req.json, name, core.is_multiple(field))
        except (AttributeError, ValueError):
            pass
        return core.missing

    def parse_headers(self, req, name, field):
        """Pull a value from the header data."""
        return core.get_value(req.headers, name, core.is_multiple(field))

    def parse_cookies(self, req, name, field):
        """Pull a value from the cookiejar."""
        return req.get_cookie(name)

    def parse_files(self, req, name, field):
        """Pull a file from the request."""
        return core.get_value(req.files, name, core.is_multiple(field))

    def handle_error(self, error):
        """Handles errors during parsing. Aborts the current request with a
        400 error.
        """
        logger.error(error)
        status_code = getattr(error, 'status_code', self.DEFAULT_VALIDATION_STATUS)
        headers = getattr(error, 'headers', {})
        raise HTTPError(status=status_code, body=error.messages,
                        headers=headers, exception=error)

    def parse(self, argmap, req=None, *args, **kwargs):
        """Parses the request using the given arguments map.
        Uses Bottle's context-local request object if req=None.
        """
        req_obj = req or request  # Default to context-local request
        return super(BottleParser, self).parse(argmap, req_obj, *args, **kwargs)

parser = BottleParser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs
