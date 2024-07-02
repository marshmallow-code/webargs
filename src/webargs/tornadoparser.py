"""Tornado request argument parsing module.

Example: ::

    import tornado.web
    from marshmallow import fields
    from webargs.tornadoparser import use_args


    class HelloHandler(tornado.web.RequestHandler):
        @use_args({"name": fields.Str(load_default="World")})
        def get(self, args):
            response = {"message": "Hello {}".format(args["name"])}
            self.write(response)
"""

from __future__ import annotations

import json
import typing

import marshmallow as ma
import tornado.concurrent
import tornado.web
from tornado.escape import _unicode
from tornado.httputil import HTTPServerRequest

from webargs import core
from webargs.multidictproxy import MultiDictProxy


class HTTPError(tornado.web.HTTPError):
    """`tornado.web.HTTPError` that stores validation errors."""

    def __init__(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        self.messages = kwargs.pop("messages", {})
        self.headers = kwargs.pop("headers", None)
        super().__init__(*args, **kwargs)


def is_json_request(req: HTTPServerRequest) -> bool:
    content_type = req.headers.get("Content-Type")
    return content_type is not None and core.is_json(content_type)


class WebArgsTornadoMultiDictProxy(MultiDictProxy):
    """
    Override class for Tornado multidicts, handles argument decoding
    requirements.
    """

    def __getitem__(self, key: str) -> typing.Any:
        try:
            value = self.data.get(key, core.missing)
            if value is core.missing:
                return core.missing
            if key in self.multiple_keys:
                return [
                    _unicode(v) if isinstance(v, (str, bytes)) else v for v in value
                ]
            if value and isinstance(value, (list, tuple)):
                value = value[0]

            if isinstance(value, (str, bytes)):
                return _unicode(value)
            return value
        # based on tornado.web.RequestHandler.decode_argument
        except UnicodeDecodeError as exc:
            raise HTTPError(400, f"Invalid unicode in {key}: {value[:40]!r}") from exc


class WebArgsTornadoCookiesMultiDictProxy(MultiDictProxy):
    """
    And a special override for cookies because they come back as objects with a
    `value` attribute we need to extract.
    Also, does not use the `_unicode` decoding step
    """

    def __getitem__(self, key: str) -> typing.Any:
        cookie = self.data.get(key, core.missing)
        if cookie is core.missing:
            return core.missing
        if key in self.multiple_keys:
            return [cookie.value]
        return cookie.value


class TornadoParser(core.Parser[HTTPServerRequest]):
    """Tornado request argument parser."""

    def _raw_load_json(self, req: HTTPServerRequest) -> typing.Any:
        """Return a json payload from the request for the core parser's load_json

        Checks the input mimetype and may return 'missing' if the mimetype is
        non-json, even if the request body is parseable as json."""
        if not is_json_request(req):
            return core.missing

        # request.body may be a concurrent.Future on streaming requests
        # this would cause a TypeError if we try to parse it
        if isinstance(req.body, tornado.concurrent.Future):
            return core.missing

        return core.parse_json(req.body)

    def load_querystring(self, req: HTTPServerRequest, schema: ma.Schema) -> typing.Any:
        """Return query params from the request as a MultiDictProxy."""
        return self._makeproxy(
            req.query_arguments, schema, cls=WebArgsTornadoMultiDictProxy
        )

    def load_form(self, req: HTTPServerRequest, schema: ma.Schema) -> typing.Any:
        """Return form values from the request as a MultiDictProxy."""
        return self._makeproxy(
            req.body_arguments, schema, cls=WebArgsTornadoMultiDictProxy
        )

    def load_headers(self, req: HTTPServerRequest, schema: ma.Schema) -> typing.Any:
        """Return headers from the request as a MultiDictProxy."""
        return self._makeproxy(req.headers, schema, cls=WebArgsTornadoMultiDictProxy)

    def load_cookies(self, req: HTTPServerRequest, schema: ma.Schema) -> typing.Any:
        """Return cookies from the request as a MultiDictProxy."""
        # use the specialized subclass specifically for handling Tornado
        # cookies
        return self._makeproxy(
            req.cookies, schema, cls=WebArgsTornadoCookiesMultiDictProxy
        )

    def load_files(self, req: HTTPServerRequest, schema: ma.Schema) -> typing.Any:
        """Return files from the request as a MultiDictProxy."""
        return self._makeproxy(req.files, schema, cls=WebArgsTornadoMultiDictProxy)

    def handle_error(
        self,
        error: ma.ValidationError,
        req: HTTPServerRequest,
        schema: ma.Schema,
        *,
        error_status_code: int | None,
        error_headers: typing.Mapping[str, str] | None,
    ) -> typing.NoReturn:
        """Handles errors during parsing. Raises a `tornado.web.HTTPError`
        with a 400 error.
        """
        status_code = error_status_code or self.DEFAULT_VALIDATION_STATUS
        if status_code == 422:
            reason = "Unprocessable Entity"
        else:
            reason = None
        raise HTTPError(
            status_code,
            log_message=str(error.messages),
            reason=reason,
            messages=error.messages,
            headers=error_headers,
        )

    def _handle_invalid_json_error(
        self,
        error: json.JSONDecodeError | UnicodeDecodeError,
        req: HTTPServerRequest,
        *args: typing.Any,
        **kwargs: typing.Any,
    ) -> typing.NoReturn:
        raise HTTPError(
            400,
            log_message="Invalid JSON body.",
            reason="Bad Request",
            messages={"json": ["Invalid JSON body."]},
        )

    def get_request_from_view_args(
        self,
        view: typing.Any,
        args: tuple[typing.Any, ...],
        kwargs: typing.Mapping[str, typing.Any],
    ) -> HTTPServerRequest:
        return args[0].request


parser = TornadoParser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs
