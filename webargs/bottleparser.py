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

import bottle

from webargs import core

logger = logging.getLogger(__name__)

class BottleParser(core.Parser):
    """Bottle.py request argument parser."""

    def parse_querystring(self, req, name, field):
        """Pull a querystring value from the request."""
        return core.get_value(req.query, name, field)

    def parse_form(self, req, name, field):
        """Pull a form value from the request."""
        return core.get_value(req.forms, name, field)

    def parse_json(self, req, name, field):
        """Pull a json value from the request."""
        json_body = self._cache.get('json')
        if json_body is None:
            try:
                self._cache['json'] = json_body = req.json
            except (AttributeError, ValueError):
                return core.missing
        if json_body is not None:
            return core.get_value(req.json, name, field)
        else:
            return core.missing

    def parse_headers(self, req, name, field):
        """Pull a value from the header data."""
        return core.get_value(req.headers, name, field)

    def parse_cookies(self, req, name, field):
        """Pull a value from the cookiejar."""
        return req.get_cookie(name)

    def parse_files(self, req, name, field):
        """Pull a file from the request."""
        return core.get_value(req.files, name, field)

    def handle_error(self, error):
        """Handles errors during parsing. Aborts the current request with a
        400 error.
        """
        logger.error(error)
        status_code = getattr(error, 'status_code', self.DEFAULT_VALIDATION_STATUS)
        headers = getattr(error, 'headers', {})
        raise bottle.HTTPError(status=status_code, body=error.messages,
                        headers=headers, exception=error)

    def get_default_request(self):
        """Override to use bottle's thread-local request object by default."""
        return bottle.request

parser = BottleParser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs
