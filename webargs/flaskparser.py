# -*- coding: utf-8 -*-
"""Flask request argument parsing module.

Example: ::

    from flask import Flask

    from webargs import fields
    from webargs.flaskparser import use_args

    app = Flask(__name__)

    hello_args = {
        'name': fields.Str(required=True)
    }

    @app.route('/')
    @use_args(hello_args)
    def index(args):
        return 'Hello ' + args['name']
"""
import flask
from werkzeug.exceptions import HTTPException

from webargs import core


def abort(http_status_code, exc=None, **kwargs):
    """Raise a HTTPException for the given http_status_code. Attach any keyword
    arguments to the exception for later processing.

    From Flask-Restful. See NOTICE file for license information.
    """
    try:
        flask.abort(http_status_code)
    except HTTPException as err:
        if len(kwargs):
            err.data = kwargs
        err.exc = exc
        raise err


def is_json_request(req):
    return core.is_json(req.mimetype)


class FlaskParser(core.Parser):
    """Flask request argument parser."""

    __location_map__ = dict(
        view_args='parse_view_args',
        **core.Parser.__location_map__
    )

    def parse_view_args(self, req, name, field):
        """Pull a value from the request's ``view_args``."""
        return core.get_value(req.view_args, name, field)

    def parse_json(self, req, name, field):
        """Pull a json value from the request."""
        # Pass force in order to handle vendor media types,
        # e.g. applications/vnd.json+api
        # this should be unnecessary in Flask 1.0
        force = is_json_request(req)
        # Fail silently so that the webargs parser can handle the error
        if hasattr(req, 'get_json'):
            # Flask >= 0.10.x
            json_data = req.get_json(force=force, silent=True)
        else:
            # Flask <= 0.9.x
            json_data = req.json
        if json_data is None:
            return core.missing
        return core.get_value(json_data, name, field, allow_many_nested=True)

    def parse_querystring(self, req, name, field):
        """Pull a querystring value from the request."""
        return core.get_value(req.args, name, field)

    def parse_form(self, req, name, field):
        """Pull a form value from the request."""
        try:
            return core.get_value(req.form, name, field)
        except AttributeError:
            pass
        return core.missing

    def parse_headers(self, req, name, field):
        """Pull a value from the header data."""
        return core.get_value(req.headers, name, field)

    def parse_cookies(self, req, name, field):
        """Pull a value from the cookiejar."""
        return core.get_value(req.cookies, name, field)

    def parse_files(self, req, name, field):
        """Pull a file from the request."""
        return core.get_value(req.files, name, field)

    def handle_error(self, error):
        """Handles errors during parsing. Aborts the current HTTP request and
        responds with a 422 error.
        """
        status_code = getattr(error, 'status_code', self.DEFAULT_VALIDATION_STATUS)
        abort(status_code, messages=error.messages, exc=error)

    def get_default_request(self):
        """Override to use Flask's thread-local request objec by default"""
        return flask.request

parser = FlaskParser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs
