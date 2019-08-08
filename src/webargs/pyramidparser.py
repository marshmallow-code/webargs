# -*- coding: utf-8 -*-
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
import collections
import functools

from webob.multidict import MultiDict
from pyramid.httpexceptions import exception_response, HTTPException

from webargs import core
from webargs.core import json
from webargs.compat import text_type


class PyramidParser(core.Parser):
    """Pyramid request argument parser."""

    __location_map__ = dict(
        matchdict="parse_matchdict",
        path="parse_matchdict",
        **core.Parser.__location_map__
    )

    def _load_files_mdict(self, req):
        return MultiDict((k, v) for k, v in req.POST.items() if hasattr(v, "file"))

    def _load_json_data(self, req):
        json_data = self._cache.get("json")
        if json_data is None:
            try:
                self._cache["json"] = json_data = core.parse_json(req.body, req.charset)
            except json.JSONDecodeError as e:
                if e.doc == "":
                    return core.missing
                else:
                    return self.handle_invalid_json_error(e, req)
            if json_data is None:
                return core.missing
        return json_data

    def get_args_by_location(self, req, locations):
        result = {}
        if "matchdict" in locations:
            result["matchdict"] = req.matchdict.keys()
        if "path" in locations:
            result["path"] = req.matchdict.keys()
        if "json" in locations:
            try:
                data = self._load_json_data(req)
            except HTTPException:
                data = core.missing
            if isinstance(data, dict):
                data = data.keys()
            # this is slightly unintuitive, but if we parse JSON which is
            # not a dict, we don't know any arg names
            else:
                data = core.missing
            result["json"] = data
        if "querystring" in locations:
            result["querystring"] = req.GET.keys()
        if "query" in locations:
            result["query"] = req.GET.keys()
        if "form" in locations:
            result["form"] = req.POST.keys()
        if "headers" in locations:
            result["headers"] = req.headers.keys()
        if "cookies" in locations:
            result["cookies"] = req.cookies.keys()
        if "files" in locations:
            result["files"] = self._load_files_mdict(req).keys()
        return result

    def parse_querystring(self, req, name, field):
        """Pull a querystring value from the request."""
        return core.get_value(req.GET, name, field)

    def parse_form(self, req, name, field):
        """Pull a form value from the request."""
        return core.get_value(req.POST, name, field)

    def parse_json(self, req, name, field):
        """Pull a json value from the request."""
        json_data = self._load_json_data(req)
        return core.get_value(json_data, name, field, allow_many_nested=True)

    def parse_cookies(self, req, name, field):
        """Pull the value from the cookiejar."""
        return core.get_value(req.cookies, name, field)

    def parse_headers(self, req, name, field):
        """Pull a value from the header data."""
        return core.get_value(req.headers, name, field)

    def parse_files(self, req, name, field):
        """Pull a file from the request."""
        return core.get_value(self._load_files_mdict(req), name, field)

    def parse_matchdict(self, req, name, field):
        """Pull a value from the request's `matchdict`."""
        return core.get_value(req.matchdict, name, field)

    def handle_error(self, error, req, schema, error_status_code, error_headers):
        """Handles errors during parsing. Aborts the current HTTP request and
        responds with a 400 error.
        """
        status_code = error_status_code or self.DEFAULT_VALIDATION_STATUS
        response = exception_response(
            status_code,
            detail=text_type(error),
            headers=error_headers,
            content_type="application/json",
        )
        body = json.dumps(error.messages)
        response.body = body.encode("utf-8") if isinstance(body, text_type) else body
        raise response

    def handle_invalid_json_error(self, error, req, *args, **kwargs):
        messages = {"json": ["Invalid JSON body."]}
        response = exception_response(
            400, detail=text_type(messages), content_type="application/json"
        )
        body = json.dumps(messages)
        response.body = body.encode("utf-8") if isinstance(body, text_type) else body
        raise response

    def use_args(
        self,
        argmap,
        req=None,
        locations=core.Parser.DEFAULT_LOCATIONS,
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
        :param tuple locations: Where on the request to search for values.
        :param bool as_kwargs: Whether to insert arguments as keyword arguments.
        :param callable validate: Validation function that receives the dictionary
            of parsed arguments. If the function returns ``False``, the parser
            will raise a :exc:`ValidationError`.
        :param int error_status_code: Status code passed to error handler functions when
            a `ValidationError` is raised.
        :param dict error_headers: Headers passed to error handler functions when a
            a `ValidationError` is raised.
        """
        locations = locations or self.locations
        # Optimization: If argmap is passed as a dictionary, we only need
        # to generate a Schema once
        if isinstance(argmap, collections.Mapping):
            argmap = core.dict2schema(argmap, self.schema_class)()

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
                    locations=locations,
                    validate=validate,
                    error_status_code=error_status_code,
                    error_headers=error_headers,
                )
                if as_kwargs:
                    kwargs.update(parsed_args)
                    return func(obj, *args, **kwargs)
                else:
                    return func(obj, parsed_args, *args, **kwargs)

            wrapper.__wrapped__ = func
            return wrapper

        return decorator


parser = PyramidParser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs
