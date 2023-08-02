"""aiohttp request argument parsing module.

Example: ::

    import asyncio
    from aiohttp import web

    from webargs import fields
    from webargs.aiohttpparser import use_args


    hello_args = {
        'name': fields.Str(required=True)
    }
    @asyncio.coroutine
    @use_args(hello_args)
    def index(request, args):
        return web.Response(
            body='Hello {}'.format(args['name']).encode('utf-8')
        )

    app = web.Application()
    app.router.add_route('GET', '/', index)
"""
from __future__ import annotations

import typing

from aiohttp import web
from aiohttp import web_exceptions
from marshmallow import Schema, ValidationError, RAISE

from webargs import core
from webargs.core import json
from webargs.asyncparser import AsyncParser
from webargs.multidictproxy import MultiDictProxy


def is_json_request(req) -> bool:
    content_type = req.content_type
    return core.is_json(content_type)


class HTTPUnprocessableEntity(web.HTTPClientError):
    status_code = 422


# Mapping of status codes to exception classes
# Adapted from werkzeug
exception_map: dict[int, type[web_exceptions.HTTPException]] = {}
exception_map[422] = HTTPUnprocessableEntity


def _find_exceptions() -> None:
    for name in web_exceptions.__all__:
        obj = getattr(web_exceptions, name)
        try:
            is_http_exception = issubclass(obj, web_exceptions.HTTPException)
        except TypeError:
            is_http_exception = False
        if not is_http_exception or obj.status_code is None:
            continue
        old_obj = exception_map.get(obj.status_code, None)
        if old_obj is not None and issubclass(obj, old_obj):
            continue
        exception_map[obj.status_code] = obj


# Collect all exceptions from aiohttp.web_exceptions
_find_exceptions()
del _find_exceptions


class AIOHTTPParser(AsyncParser[web.Request]):
    """aiohttp request argument parser."""

    DEFAULT_UNKNOWN_BY_LOCATION: dict[str, str | None] = {
        "match_info": RAISE,
        "path": RAISE,
        **core.Parser.DEFAULT_UNKNOWN_BY_LOCATION,
    }
    __location_map__ = dict(
        match_info="load_match_info",
        path="load_match_info",
        **core.Parser.__location_map__,
    )

    def load_querystring(self, req, schema: Schema) -> MultiDictProxy:
        """Return query params from the request as a MultiDictProxy."""
        return self._makeproxy(req.query, schema)

    async def load_form(self, req, schema: Schema) -> MultiDictProxy:
        """Return form values from the request as a MultiDictProxy."""
        post_data = await req.post()
        return self._makeproxy(post_data, schema)

    async def load_json_or_form(self, req, schema: Schema) -> dict | MultiDictProxy:
        data = await self.load_json(req, schema)
        if data is not core.missing:
            return data
        return await self.load_form(req, schema)

    async def load_json(self, req, schema: Schema):
        """Return a parsed json payload from the request."""
        if not (req.body_exists and is_json_request(req)):
            return core.missing
        try:
            return await req.json(loads=json.loads)
        except json.JSONDecodeError as exc:
            if exc.doc == "":
                return core.missing
            return self._handle_invalid_json_error(exc, req)
        except UnicodeDecodeError as exc:
            return self._handle_invalid_json_error(exc, req)

    def load_headers(self, req, schema: Schema) -> MultiDictProxy:
        """Return headers from the request as a MultiDictProxy."""
        return self._makeproxy(req.headers, schema)

    def load_cookies(self, req, schema: Schema) -> MultiDictProxy:
        """Return cookies from the request as a MultiDictProxy."""
        return self._makeproxy(req.cookies, schema)

    def load_files(self, req, schema: Schema) -> typing.NoReturn:
        raise NotImplementedError(
            "load_files is not implemented. You may be able to use load_form for "
            "parsing upload data."
        )

    def load_match_info(self, req, schema: Schema) -> typing.Mapping:
        """Load the request's ``match_info``."""
        return req.match_info

    def get_request_from_view_args(
        self, view: typing.Callable, args: typing.Iterable, kwargs: typing.Mapping
    ):
        """Get request object from a handler function or method. Used internally by
        ``use_args`` and ``use_kwargs``.
        """
        req = None
        for arg in args:
            if isinstance(arg, web.Request):
                req = arg
                break
            if isinstance(arg, web.View):
                req = arg.request
                break
        if not isinstance(req, web.Request):
            raise ValueError("Request argument not found for handler")
        return req

    def handle_error(
        self,
        error: ValidationError,
        req,
        schema: Schema,
        *,
        error_status_code: int | None,
        error_headers: typing.Mapping[str, str] | None,
    ) -> typing.NoReturn:
        """Handle ValidationErrors and return a JSON response of error messages
        to the client.
        """
        error_class = exception_map.get(
            error_status_code or self.DEFAULT_VALIDATION_STATUS
        )
        if not error_class:
            raise LookupError(f"No exception for {error_status_code}")
        headers = error_headers
        raise error_class(
            text=json.dumps(error.messages),
            headers=headers,
            content_type="application/json",
        )

    def _handle_invalid_json_error(
        self, error: json.JSONDecodeError | UnicodeDecodeError, req, *args, **kwargs
    ) -> typing.NoReturn:
        error_class = exception_map[400]
        messages = {"json": ["Invalid JSON body."]}
        raise error_class(text=json.dumps(messages), content_type="application/json")


parser = AIOHTTPParser()
use_args = parser.use_args  # type: typing.Callable
use_kwargs = parser.use_kwargs  # type: typing.Callable
