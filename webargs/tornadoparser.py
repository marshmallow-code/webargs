# -*- coding: utf-8 -*-
"""Tornado request argument parsing module.

Example: ::

    import tornado.web
    from webargs import Arg
    from webargs.tornadoparser import use_args

    class HelloHandler(tornado.web.RequestHandler):

        @use_args({'name': Arg(str, default='World')})
        def get(self, args):
            response = {'message': 'Hello {}'.format(args['name'])}
            self.write(response)
"""

import json
import functools
import logging

import tornado.web

from webargs import core

logger = logging.getLogger(__name__)

def parse_json(s):
    if isinstance(s, bytes):
        s = s.decode('utf-8')
    return json.loads(s)

def parse_json_body(req):
    """Return the decoded JSON body from the request."""
    content_type = req.headers.get('Content-Type')
    if content_type and 'application/json' in req.headers.get('Content-Type'):
        try:
            return parse_json(req.body)
        except (TypeError, ValueError):
            pass
    return {}


def get_value(d, name, multiple):
    """Handle gets from 'multidicts' made of lists

    It handles cases: ``{"key": [value]}`` and ``{"key": value}``
    """
    value = d.get(name, core.Missing)

    if multiple and value is not core.Missing:
        return [] if value is core.Missing else value

    if value and isinstance(value, (list, tuple)):
        return value[0]

    return value

class TornadoParser(core.Parser):
    """Tornado request argument parser."""

    def __init__(self, *args, **kwargs):
        super(TornadoParser, self).__init__(*args, **kwargs)
        self.json = None

    def parse_json(self, req, name, arg):
        """Pull a json value from the request."""
        json_body = self._cache.get('json')
        if json_body is None:
            self._cache['json'] = parse_json_body(req)
        return get_value(self._cache['json'], name, arg.multiple)

    def parse_querystring(self, req, name, arg):
        """Pull a querystring value from the request."""
        return get_value(req.query_arguments, name, arg.multiple)

    def parse_form(self, req, name, arg):
        """Pull a form value from the request."""
        return get_value(req.body_arguments, name, arg.multiple)

    def parse_headers(self, req, name, arg):
        """Pull a value from the header data."""
        return get_value(req.headers, name, arg.multiple)

    def parse_cookies(self, req, name, arg):
        """Pull a value from the header data."""
        cookie = req.cookies.get(name)

        if cookie is not None:
            return [cookie.value] if arg.multiple else cookie.value
        else:
            return [] if arg.multiple else None

    def parse_files(self, req, name, arg):
        """Pull a file from the request."""
        return get_value(req.files, name, arg.multiple)

    def handle_error(self, error):
        """Handles errors during parsing. Raises a `tornado.web.HTTPError`
        with a 400 error.
        """
        logger.error(error)
        status_code = getattr(error, 'status_code', 400)
        data = getattr(error, 'data', {})
        raise tornado.web.HTTPError(status_code, error.args[0], **data)

    def use_args(self, argmap, req=None, locations=core.Parser.DEFAULT_LOCATIONS,
                 as_kwargs=False, validate=None):
        """Decorator that injects parsed arguments into a view function or method.

        :param dict argmap: Dictionary of argument_name:Arg object pairs.
        :param req: The request object to parse
        :param tuple locations: Where on the request to search for values.
        :param as_kwargs: Whether to pass arguments to the handler as kwargs
        :param callable validate: Validation function that receives the dictionary
            of parsed arguments. If the function returns ``False``, the parser
            will raise a :exc:`ValidationError`.
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(obj, *args, **kwargs):
                parsed_args = self.parse(
                    argmap, req=obj.request, locations=locations, validate=validate)

                if as_kwargs:
                    kwargs.update(parsed_args)
                else:
                    args = (parsed_args,) + args

                return func(obj, *args, **kwargs)
            return wrapper
        return decorator


parser = TornadoParser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs
