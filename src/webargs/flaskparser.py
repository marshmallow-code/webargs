"""Flask request argument parsing module.

Example: ::

    from flask import Flask

    from webargs import fields
    from webargs.flaskparser import use_args

    app = Flask(__name__)

    user_detail_args = {
        'per_page': fields.Int()
    }

    @app.route("/user/<int:uid>")
    @use_args(user_detail_args)
    def user_detail(args, uid):
        return ("The user page for user {uid}, showing {per_page} posts.").format(
            uid=uid, per_page=args["per_page"]
        )
"""
import flask
from werkzeug.exceptions import HTTPException

import marshmallow as ma

from webargs import core
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

    DEFAULT_UNKNOWN_BY_LOCATION = {
        "view_args": ma.RAISE,
        "path": ma.RAISE,
        **core.Parser.DEFAULT_UNKNOWN_BY_LOCATION,
    }
    __location_map__ = dict(
        view_args="load_view_args",
        path="load_view_args",
        **core.Parser.__location_map__,
    )

    def _raw_load_json(self, req):
        """Return a json payload from the request for the core parser's load_json

        Checks the input mimetype and may return 'missing' if the mimetype is
        non-json, even if the request body is parseable as json."""
        if not is_json_request(req):
            return core.missing

        return core.parse_json(req.get_data(cache=True))

    def _handle_invalid_json_error(self, error, req, *args, **kwargs):
        abort(400, exc=error, messages={"json": ["Invalid JSON body."]})

    def load_view_args(self, req, schema):
        """Return the request's ``view_args`` or ``missing`` if there are none."""
        return req.view_args or core.missing

    def load_querystring(self, req, schema):
        """Return query params from the request as a MultiDictProxy."""
        return MultiDictProxy(req.args, schema)

    def load_form(self, req, schema):
        """Return form values from the request as a MultiDictProxy."""
        return MultiDictProxy(req.form, schema)

    def load_headers(self, req, schema):
        """Return headers from the request as a MultiDictProxy."""
        return MultiDictProxy(req.headers, schema)

    def load_cookies(self, req, schema):
        """Return cookies from the request."""
        return req.cookies

    def load_files(self, req, schema):
        """Return files from the request as a MultiDictProxy."""
        return MultiDictProxy(req.files, schema)

    def handle_error(self, error, req, schema, *, error_status_code, error_headers):
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

    def get_default_request(self):
        """Override to use Flask's thread-local request object by default"""
        return flask.request


parser = FlaskParser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs
