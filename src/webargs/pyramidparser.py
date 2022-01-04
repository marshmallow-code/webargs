"""Pyramid request argument parsing.

Example usage: ::

    from wsgiref.simple_server import make_server
    from pyramid.config import Configurator
    from pyramid.response import Response
    from marshmallow import fields
    from webargs.pyramidparser import use_args

    hello_args = {
        'name': fields.Str(missing='World')
    }

    @use_args(hello_args)
    def hello_world(request, args):
        return Response('Hello ' + args['name'])

    if __name__ == '__main__':
        config = Configurator()
        config.add_route('hello', '/')
        config.add_view(hello_world, route_name='hello')
        app = config.make_wsgi_app()
        server = make_server('0.0.0.0', 6543, app)
        server.serve_forever()
"""
from __future__ import annotations

import functools
from collections.abc import Mapping

from webob.multidict import MultiDict
from pyramid.httpexceptions import exception_response

import marshmallow as ma

from webargs import core
from webargs.core import json


def is_json_request(req):
    return core.is_json(req.headers.get("content-type"))


class PyramidParser(core.Parser):
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

    def _raw_load_json(self, req):
        """Return a json payload from the request for the core parser's load_json

        Checks the input mimetype and may return 'missing' if the mimetype is
        non-json, even if the request body is parseable as json."""
        if not is_json_request(req):
            return core.missing

        return core.parse_json(req.body, encoding=req.charset)

    def load_querystring(self, req, schema):
        """Return query params from the request as a MultiDictProxy."""
        return self._makeproxy(req.GET, schema)

    def load_form(self, req, schema):
        """Return form values from the request as a MultiDictProxy."""
        return self._makeproxy(req.POST, schema)

    def load_cookies(self, req, schema):
        """Return cookies from the request as a MultiDictProxy."""
        return self._makeproxy(req.cookies, schema)

    def load_headers(self, req, schema):
        """Return headers from the request as a MultiDictProxy."""
        return self._makeproxy(req.headers, schema)

    def load_files(self, req, schema):
        """Return files from the request as a MultiDictProxy."""
        files = ((k, v) for k, v in req.POST.items() if hasattr(v, "file"))
        return self._makeproxy(MultiDict(files), schema)

    def load_matchdict(self, req, schema):
        """Return the request's ``matchdict`` as a MultiDictProxy."""
        return self._makeproxy(req.matchdict, schema)

    def handle_error(self, error, req, schema, *, error_status_code, error_headers):
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

    def _handle_invalid_json_error(self, error, req, *args, **kwargs):
        messages = {"json": ["Invalid JSON body."]}
        response = exception_response(
            400, detail=str(messages), content_type="application/json"
        )
        body = json.dumps(messages)
        response.body = body.encode("utf-8") if isinstance(body, str) else body
        raise response

    def use_args(
        self,
        argmap,
        req=None,
        *,
        location=core.Parser.DEFAULT_LOCATION,
        unknown=None,
        as_kwargs=False,
        validate=None,
        error_status_code=None,
        error_headers=None,
    ):
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
        :param callable validate: Validation function that receives the dictionary
            of parsed arguments. If the function returns ``False``, the parser
            will raise a :exc:`ValidationError`.
        :param int error_status_code: Status code passed to error handler functions when
            a `ValidationError` is raised.
        :param dict error_headers: Headers passed to error handler functions when a
            a `ValidationError` is raised.
        """
        location = location or self.location
        # Optimization: If argmap is passed as a dictionary, we only need
        # to generate a Schema once
        if isinstance(argmap, Mapping):
            argmap = self.schema_class.from_dict(argmap)()

        def decorator(func):
            @functools.wraps(func)
            def wrapper(obj, *args, **kwargs):
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
                    args, kwargs, parsed_args, as_kwargs
                )
                return func(obj, *args, **kwargs)

            wrapper.__wrapped__ = func
            return wrapper

        return decorator


parser = PyramidParser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs
