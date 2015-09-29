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
import functools
import logging

from webob.multidict import MultiDict
from pyramid.httpexceptions import exception_response

import marshmallow as ma
from marshmallow.compat import text_type
from webargs import core

logger = logging.getLogger(__name__)

class PyramidParser(core.Parser):
    """Pyramid request argument parser."""

    __location_map__ = dict(
        matchdict='parse_matchdict',
        **core.Parser.__location_map__)

    def parse_querystring(self, req, name, field):
        """Pull a querystring value from the request."""
        return core.get_value(req.GET, name, field)

    def parse_form(self, req, name, field):
        """Pull a form value from the request."""
        return core.get_value(req.POST, name, field)

    def parse_json(self, req, name, field):
        """Pull a json value from the request."""
        try:
            json_data = req.json_body
        except ValueError:
            return core.missing

        return core.get_value(json_data, name, field)

    def parse_cookies(self, req, name, field):
        """Pull the value from the cookiejar."""
        return core.get_value(req.cookies, name, field)

    def parse_headers(self, req, name, field):
        """Pull a value from the header data."""
        return core.get_value(req.headers, name, field)

    def parse_files(self, req, name, field):
        """Pull a file from the request."""
        files = ((k, v) for k, v in req.POST.items() if hasattr(v, 'file'))
        return core.get_value(MultiDict(files), name, field)

    def parse_matchdict(self, req, name, field):
        """Pull a value from the request's `matchdict`."""
        return core.get_value(req.matchdict, name, field)

    def handle_error(self, error):
        """Handles errors during parsing. Aborts the current HTTP request and
        responds with a 400 error.
        """
        logger.error(error)
        status_code = getattr(error, 'status_code', 400)
        raise exception_response(status_code, detail=text_type(error))

    def use_args(self, argmap, req=None, locations=core.Parser.DEFAULT_LOCATIONS,
                 as_kwargs=False, validate=None):
        """Decorator that injects parsed arguments into a view callable.
        Supports the *Class-based View* pattern where `request` is saved as an instance
        attribute on a view class.

        :param dict argmap: Either a `marshmallow.Schema` or a `dict`
            of argname -> `marshmallow.fields.Field` pairs.
        :param req: The request object to parse. Pulled off of the view by default.
        :param tuple locations: Where on the request to search for values.
        :param bool as_kwargs: Whether to insert arguments as keyword arguments.
        :param callable validate: Validation function that receives the dictionary
            of parsed arguments. If the function returns ``False``, the parser
            will raise a :exc:`ValidationError`.
        """
        locations = locations or self.locations
        if isinstance(argmap, ma.Schema):
            schema = argmap
        else:
            schema = core.argmap2schema(argmap)()

        def decorator(func):
            @functools.wraps(func)
            def wrapper(obj, *args, **kwargs):
                # The first argument is either `self` or `request`
                try:  # get self.request
                    request = req or obj.request
                except AttributeError:  # first arg is request
                    request = obj
                parsed_args = self.parse(schema, req=request, locations=locations,
                                         validate=validate, force_all=as_kwargs)
                if as_kwargs:
                    kwargs.update(parsed_args)
                    return func(obj, *args, **kwargs)
                else:
                    return func(obj, parsed_args, *args, **kwargs)
            return wrapper
        return decorator

parser = PyramidParser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs
