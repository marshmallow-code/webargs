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
from webargs.core import json
from webargs.multidictproxy import MultiDictProxy


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
        view_args="load_view_args",
        path="load_view_args",
        **core.Parser.__location_map__
    )

    def load_view_args(self, req, schema):
        """Read the request's ``view_args`` or ``missing`` if there are none."""
        return req.view_args or core.missing

    def load_json(self, req, schema):
        """Read a json payload from the request.

        Checks the input mimetype and may return 'missing' if the mimetype is
        non-json, even if the request body is parseable as json."""
        if not is_json_request(req):
            return core.missing

        json_data = self._cache.get("json")
        if json_data is None:
            # We decode the json manually here instead of
            # using req.get_json() so that we can handle
            # JSONDecodeErrors consistently
            data = req.get_data(cache=True)
            try:
                self._cache["json"] = json_data = core.parse_json(data)
            except json.JSONDecodeError as e:
                if e.doc == "":
                    return core.missing
                else:
                    return self.handle_invalid_json_error(e, req)

        return json_data

    def load_querystring(self, req, schema):
        """Read query params from the request.

        Is a multidict."""
        return MultiDictProxy(req.args, schema)

    def load_form(self, req, schema):
        """Read form values from the request.

        Is a multidict."""
        return MultiDictProxy(req.form, schema)

    def load_headers(self, req, schema):
        """Read headers from the request.

        Is a multidict."""
        return MultiDictProxy(req.headers, schema)

    def load_cookies(self, req, schema):
        """Read cookies from the request."""
        return req.cookies

    def load_files(self, req, schema):
        """Read files from the request.

        Is a multidict."""
        return MultiDictProxy(req.files, schema)

    def handle_error(self, error, req, schema, error_status_code, error_headers):
        """Handles errors during parsing. Aborts the current HTTP request and
        responds with a 422 error.
        """
        status_code = error_status_code or self.DEFAULT_VALIDATION_STATUS
        abort(
            status_code,
            exc=error,
            messages=error.messages,
            schema=schema,
            headers=error_headers,
        )

    def handle_invalid_json_error(self, error, req, *args, **kwargs):
        abort(400, exc=error, messages={"json": ["Invalid JSON body."]})

    def get_default_request(self):
        """Override to use Flask's thread-local request objec by default"""
        return flask.request


parser = FlaskParser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs
