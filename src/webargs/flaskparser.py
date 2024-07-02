"""Flask request argument parsing module.

Example: ::

    from flask import Flask

    from webargs import fields
    from webargs.flaskparser import use_args

    app = Flask(__name__)

    user_detail_args = {"per_page": fields.Int()}


    @app.route("/user/<int:uid>")
    @use_args(user_detail_args)
    def user_detail(args, uid):
        return ("The user page for user {uid}, showing {per_page} posts.").format(
            uid=uid, per_page=args["per_page"]
        )
"""

from __future__ import annotations

import json
import typing

import flask
import marshmallow as ma
from werkzeug.exceptions import HTTPException

from webargs import core


def abort(
    http_status_code: int, exc: Exception | None = None, **kwargs: typing.Any
) -> typing.NoReturn:
    """Raise a HTTPException for the given http_status_code. Attach any keyword
    arguments to the exception for later processing.

    From Flask-Restful. See NOTICE file for license information.
    """
    try:
        flask.abort(http_status_code)
    except HTTPException as err:
        err.data = kwargs  # type: ignore
        err.exc = exc  # type: ignore
        raise err


def is_json_request(req: flask.Request) -> bool:
    return core.is_json(req.mimetype)


class FlaskParser(core.Parser[flask.Request]):
    """Flask request argument parser."""

    DEFAULT_UNKNOWN_BY_LOCATION: dict[str, str | None] = {
        "view_args": ma.RAISE,
        "path": ma.RAISE,
        **core.Parser.DEFAULT_UNKNOWN_BY_LOCATION,
    }
    __location_map__ = dict(
        view_args="load_view_args",
        path="load_view_args",
        **core.Parser.__location_map__,
    )

    def _raw_load_json(self, req: flask.Request) -> typing.Any:
        """Return a json payload from the request for the core parser's load_json

        Checks the input mimetype and may return 'missing' if the mimetype is
        non-json, even if the request body is parseable as json."""
        if not is_json_request(req):
            return core.missing

        return core.parse_json(req.get_data(cache=True))

    def _handle_invalid_json_error(
        self,
        error: json.JSONDecodeError | UnicodeDecodeError,
        req: flask.Request,
        *args: typing.Any,
        **kwargs: typing.Any,
    ) -> typing.NoReturn:
        abort(400, exc=error, messages={"json": ["Invalid JSON body."]})

    def load_view_args(self, req: flask.Request, schema: ma.Schema) -> typing.Any:
        """Return the request's ``view_args`` or ``missing`` if there are none."""
        return req.view_args or core.missing

    def load_querystring(self, req: flask.Request, schema: ma.Schema) -> typing.Any:
        """Return query params from the request as a MultiDictProxy."""
        return self._makeproxy(req.args, schema)

    def load_form(self, req: flask.Request, schema: ma.Schema) -> typing.Any:
        """Return form values from the request as a MultiDictProxy."""
        return self._makeproxy(req.form, schema)

    def load_headers(self, req: flask.Request, schema: ma.Schema) -> typing.Any:
        """Return headers from the request as a MultiDictProxy."""
        return self._makeproxy(req.headers, schema)

    def load_cookies(self, req: flask.Request, schema: ma.Schema) -> typing.Any:
        """Return cookies from the request."""
        return req.cookies

    def load_files(self, req: flask.Request, schema: ma.Schema) -> typing.Any:
        """Return files from the request as a MultiDictProxy."""
        return self._makeproxy(req.files, schema)

    def handle_error(
        self,
        error: ma.ValidationError,
        req: flask.Request,
        schema: ma.Schema,
        *,
        error_status_code: int | None,
        error_headers: typing.Mapping[str, str] | None,
    ) -> typing.NoReturn:
        """Handles errors during parsing. Aborts the current HTTP request and
        responds with a 422 error.
        """
        status_code: int = error_status_code or self.DEFAULT_VALIDATION_STATUS
        abort(
            status_code,
            exc=error,
            messages=error.messages,
            schema=schema,
            headers=error_headers,
        )

    def get_default_request(self) -> flask.Request:
        """Override to use Flask's thread-local request object by default"""
        return flask.request


parser = FlaskParser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs
