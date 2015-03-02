# -*- coding: utf-8 -*-
"""Pyramid request argument parsing.

Example usage: ::

    from wsgiref.simple_server import make_server
    from pyramid.config import Configurator
    from pyramid.response import Response
    from webargs import Arg
    from webargs.pyramidparser import use_args

    hello_args = {
        'name': Arg(str, default='World')
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

from webargs import core
from webargs.core import text_type

logger = logging.getLogger(__name__)

class PyramidParser(core.Parser):
    """Pyramid request argument parser."""

    def parse_querystring(self, req, name, arg):
        """Pull a querystring value from the request."""
        return core.get_value(req.GET, name, arg.multiple)

    def parse_form(self, req, name, arg):
        """Pull a form value from the request."""
        return core.get_value(req.POST, name, arg.multiple)

    def parse_json(self, req, name, arg):
        """Pull a json value from the request."""
        try:
            json_data = req.json_body
        except ValueError:
            return core.Missing

        return core.get_value(json_data, name, arg.multiple)

    def parse_cookies(self, req, name, arg):
        """Pull the value from the cookiejar."""
        return core.get_value(req.cookies, name, arg.multiple)

    def parse_headers(self, req, name, arg):
        """Pull a value from the header data."""
        return core.get_value(req.headers, name, arg.multiple)

    def parse_files(self, req, name, arg):
        """Pull a file from the request."""
        files = ((k, v) for k, v in req.POST.items() if hasattr(v, 'file'))
        return core.get_value(MultiDict(files), name, arg.multiple)

    def handle_error(self, error):
        """Handles errors during parsing. Aborts the current HTTP request and
        responds with a 400 error.
        """
        logger.error(error)
        status_code = getattr(error, 'status_code', 400)
        data = getattr(error, 'data', {})
        raise exception_response(status_code, detail=text_type(error), **data)

    def use_args(self, argmap, req=None, locations=core.Parser.DEFAULT_LOCATIONS,
                 validate=None):
        """Decorator that injects parsed arguments into a view callable.
        Supports the *Class-based View* pattern where `request` is saved as an instance
        attribute on a view class.

        :param dict argmap: Dictionary of argument_name:Arg object pairs.
        :param req: The request object to parse
        :param tuple locations: Where on the request to search for values.
        :param callable validate:
            Validation function that receives the dictionary of parsed arguments.
            If the function returns ``False``, the parser will raise a
            :exc:`ValidationError`.
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(obj, *args, **kwargs):
                # The first argument is either `self` or `request`
                try:  # get self.request
                    request = obj.request
                except AttributeError:  # first arg is request
                    request = obj
                parsed_args = self.parse(argmap, req=request, locations=locations,
                                         validate=None)
                return func(obj, parsed_args, *args, **kwargs)
            return wrapper
        return decorator

parser = PyramidParser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs
