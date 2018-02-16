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

    def parse_view_args(self, req):
        """Pull a value from the request's ``view_args``."""
        return req.view_args

    def parse_json(self, req):
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
            return {}
        return json_data

    def parse_querystring(self, req):
        """Pull a querystring value from the request."""
        return self._flatten_multidict(req.args)

    def parse_form(self, req):
        """Pull a form value from the request."""
        try:
            return self._flatten_multidict(req.form)
        except AttributeError:
            return {}

    def parse_headers(self, req):
        """Pull a value from the header data."""
        return req.headers

    def parse_cookies(self, req):
        """Pull a value from the cookiejar."""
        return req.cookies

    def parse_files(self, req):
        """Pull a file from the request."""
        return self._flatten_multidict(req.files)

    def handle_error(self, error):
        """Handles errors during parsing. Aborts the current HTTP request and
        responds with a 422 error.
        """
        status_code = getattr(error, 'status_code', self.DEFAULT_VALIDATION_STATUS)
        abort(status_code, messages=error.messages, exc=error)

    def get_default_request(self):
        """Override to use Flask's thread-local request objec by default"""
        return flask.request

    def _flatten_multidict(self, multidict):
        flat = multidict.to_dict(flat=False)
        print(flat)
        for key, value in flat.items():
            if len(value) == 1:
                flat[key] = value[0]
        return flat

parser = FlaskParser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs
