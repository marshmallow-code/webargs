"""Pyramid request argument parsing.

Example usage: ::

    from wsgiref.simple_server import make_server
    from pyramid.config import Configurator
    from pyramid.response import Response
    from marshmallow import fields
    from webargs.pyramidparser import use_args

    hello_args = {"name": fields.Str(load_default="World")}


    @use_args(hello_args)
    def hello_world(request, args):
        return Response("Hello " + args["name"])


    if __name__ == "__main__":
        config = Configurator()
        config.add_route("hello", "/")
        config.add_view(hello_world, route_name="hello")
        app = config.make_wsgi_app()
        server = make_server("0.0.0.0", 6543, app)
        server.serve_forever()
"""

from __future__ import annotations

import functools
import typing
from collections.abc import Mapping

import marshmallow as ma
from pyramid.httpexceptions import exception_response
from pyramid.request import Request
from webob.multidict import MultiDict

from webargs import core
from webargs.core import json

F = typing.TypeVar("F", bound=typing.Callable)


def is_json_request(req: Request) -> bool:
    return core.is_json(req.headers.get("content-type"))


class PyramidParser(core.Parser[Request]):
    """Pyramid request argument parser."""

    DEFAULT_UNKNOWN_BY_LOCATION: dict[str, str | None] = {
        "matchdict": ma.RAISE,
        "path": ma.RAISE,
        **core.Parser.DEFAULT_UNKNOWN_BY_LOCATION,
    }
    __location_map__ = dict(
        matchdict="load_matchdict",
        path="load_matchdict",
        **core.Parser.__location_map__,
    )

    def _raw_load_json(self, req: Request) -> typing.Any:
        """Return a json payload from the request for the core parser's load_json

        Checks the input mimetype and may return 'missing' if the mimetype is
        non-json, even if the request body is parseable as json."""
        if not is_json_request(req):
            return core.missing

        return core.parse_json(req.body, encoding=req.charset)

    def load_querystring(self, req: Request, schema: ma.Schema) -> typing.Any:
        """Return query params from the request as a MultiDictProxy."""
        return self._makeproxy(req.GET, schema)

    def load_form(self, req: Request, schema: ma.Schema) -> typing.Any:
        """Return form values from the request as a MultiDictProxy."""
        return self._makeproxy(req.POST, schema)

    def load_cookies(self, req: Request, schema: ma.Schema) -> typing.Any:
        """Return cookies from the request as a MultiDictProxy."""
        return self._makeproxy(req.cookies, schema)

    def load_headers(self, req: Request, schema: ma.Schema) -> typing.Any:
        """Return headers from the request as a MultiDictProxy."""
        return self._makeproxy(req.headers, schema)

    def load_files(self, req: Request, schema: ma.Schema) -> typing.Any:
        """Return files from the request as a MultiDictProxy."""
        files = ((k, v) for k, v in req.POST.items() if hasattr(v, "file"))
        return self._makeproxy(MultiDict(files), schema)

    def load_matchdict(self, req: Request, schema: ma.Schema) -> typing.Any:
        """Return the request's ``matchdict`` as a MultiDictProxy."""
        return self._makeproxy(req.matchdict, schema)

    def handle_error(
        self,
        error: ma.ValidationError,
        req: Request,
        schema: ma.Schema,
        *,
        error_status_code: int | None,
        error_headers: typing.Mapping[str, str] | None,
    ) -> typing.NoReturn:
        """Handles errors during parsing. Aborts the current HTTP request and
        responds with a 400 error.
        """
        status_code = error_status_code or self.DEFAULT_VALIDATION_STATUS
        response = exception_response(
            status_code,
            detail=str(error),
            headers=error_headers,
            content_type="application/json",
        )
        body = json.dumps(error.messages)
        response.body = body.encode("utf-8") if isinstance(body, str) else body
        raise response

    def _handle_invalid_json_error(
        self,
        error: json.JSONDecodeError | UnicodeDecodeError,
        req: Request,
        *args: typing.Any,
        **kwargs: typing.Any,
    ) -> typing.NoReturn:
        messages = {"json": ["Invalid JSON body."]}
        response = exception_response(
            400, detail=str(messages), content_type="application/json"
        )
        body = json.dumps(messages)
        response.body = body.encode("utf-8") if isinstance(body, str) else body
        raise response

    def use_args(
        self,
        argmap: core.ArgMap,
        req: Request | None = None,
        *,
        location: str | None = core.Parser.DEFAULT_LOCATION,
        unknown: str | None = None,
        as_kwargs: bool = False,
        arg_name: str | None = None,
        validate: core.ValidateArg = None,
        error_status_code: int | None = None,
        error_headers: typing.Mapping[str, str] | None = None,
    ) -> typing.Callable[..., typing.Callable]:
        """Decorator that injects parsed arguments into a view callable.
        Supports the *Class-based View* pattern where `request` is saved as an instance
        attribute on a view class.

        :param dict argmap: Either a `marshmallow.Schema`, a `dict`
            of argname -> `marshmallow.fields.Field` pairs, or a callable
            which accepts a request and returns a `marshmallow.Schema`.
        :param req: The request object to parse. Pulled off of the view by default.
        :param str location: Where on the request to load values.
        :param str unknown: A value to pass for ``unknown`` when calling the
            schema's ``load`` method.
        :param bool as_kwargs: Whether to insert arguments as keyword arguments.
        :param str arg_name: Keyword argument name to use for arguments. Mutually
            exclusive with as_kwargs.
        :param callable validate: Validation function that receives the dictionary
            of parsed arguments. If the function returns ``False``, the parser
            will raise a :exc:`ValidationError`.
        :param int error_status_code: Status code passed to error handler functions when
            a `ValidationError` is raised.
        :param dict error_headers: Headers passed to error handler functions when a
            a `ValidationError` is raised.
        """
        location = location or self.location

        if arg_name is not None and as_kwargs:
            raise ValueError("arg_name and as_kwargs are mutually exclusive")
        if arg_name is None and not self.USE_ARGS_POSITIONAL:
            arg_name = f"{location}_args"

        # Optimization: If argmap is passed as a dictionary, we only need
        # to generate a Schema once
        if isinstance(argmap, Mapping):
            if not isinstance(argmap, dict):
                argmap = dict(argmap)
            argmap = self.schema_class.from_dict(argmap)()

        def decorator(func: F) -> F:
            @functools.wraps(func)
            def wrapper(
                obj: typing.Any, *args: typing.Any, **kwargs: typing.Any
            ) -> typing.Any:
                # The first argument is either `self` or `request`
                try:  # get self.request
                    request = req or obj.request
                except AttributeError:  # first arg is request
                    request = obj
                # NOTE: At this point, argmap may be a Schema, callable, or dict
                parsed_args = self.parse(
                    argmap,
                    req=request,
                    location=location,
                    unknown=unknown,
                    validate=validate,
                    error_status_code=error_status_code,
                    error_headers=error_headers,
                )
                args, kwargs = self._update_args_kwargs(
                    args, kwargs, parsed_args, as_kwargs, arg_name
                )
                return func(obj, *args, **kwargs)

            wrapper.__wrapped__ = func
            return wrapper  # type: ignore[return-value]

        return decorator


parser = PyramidParser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs
