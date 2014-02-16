# -*- coding: utf-8 -*-
"""Flask request argument parsing module.

Example: ::

    from flask import Flask
    from webargs import Arg
    from webargs.flaskparser import use_args

    app = Flask(__name__)

    hello_args = {
        'name': Arg(str, required=True)
    }

    @app.route('/')
    @use_args(hello_args)
    def index(args):
        return 'Hello ' + args['name']
"""
from flask import request
from flask import abort as flask_abort
from werkzeug.exceptions import HTTPException

from webargs import core

def abort(http_status_code, **kwargs):
    """Raise a HTTPException for the given http_status_code. Attach any keyword
    arguments to the exception for later processing.

    From Flask-Restful. See NOTICE file for license information.
    """
    try:
        flask_abort(http_status_code)
    except HTTPException as err:
        if len(kwargs):
            err.data = kwargs
        raise err


class FlaskParser(core.Parser):
    """Flask request argument parser."""

    def parse_json(self, req, name):
        """Pull the json value from the request."""
        try:
            return req.json.get(name, None)
        except AttributeError:
            return None

    def parse_querystring(self, req, name):
        """Pull the querystring value from the request."""
        return req.args.get(name, None)

    def parse_form(self, req, name):
        """Pull the form value from the request."""
        try:
            return req.form.get(name, None)
        except AttributeError:
            return None

    def parse_headers(self, req, name):
        """Pull the value from the header data."""
        return req.headers.get(name, None)

    def parse_cookies(self, req, name):
        """Pull the value from the cookiejar."""
        return req.cookies.get(name, None)

    def handle_error(self, error):
        """Handles errors during parsing. Aborts the current HTTP request and
        responds with a 400 response.
        """
        abort(400, message=error)

    def parse(self, argmap, req=None, *args, **kwargs):
        """Parses the request using the given arguments map.
        Uses Flask's context-local request object if req=None.
        """
        req_obj = req or request  # Default to context-local request
        return super(FlaskParser, self).parse(argmap, req_obj, *args, **kwargs)

use_args = FlaskParser().use_args
