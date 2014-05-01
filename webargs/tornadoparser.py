# -*- coding: utf-8 -*-

import json
import functools

import tornado.web

from webargs import core


class TornadoParser(core.Parser):
    """Tornado request argument parser."""

    def parse_json(self, req, name, arg):
        """Pull a json value from the request."""
        return self.json.get(name, [] if arg.multiple else None)

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
        raise tornado.web.HTTPError(400, error)

    def _parse_json_body(self, req):
        if req.headers.get('Content-Type') == 'application/json':
            self.json = json.loads(req.body)
        else:
            self.json = {}

    def parse(self, argmap, req, *args, **kwargs):
        """Parses the request using the given arguments map.

        Initializes :attr:`json` attribute.
        """
        self._parse_json_body(req)
        return super(TornadoParser, self).parse(argmap, req, *args, **kwargs)

    def use_args(self, argmap, req=None, targets=core.Parser.DEFAULT_TARGETS,
                as_kwargs=False):
        """Decorator that injects parsed arguments into a view function or method.

        Example: ::

            @parser.use_kwargs({'name': Arg(type_=str)})
            def myview(request, args):
                self.write('Hello ' + args['name'])

        :param dict argmap: Dictionary of argument_name:Arg object pairs.
        :param req: The request object to parse
        :param tuple targets: Where on the request to search for values.
        :param as_kwargs: Wether to pass arguments to the handler as kwargs
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(obj, *args, **kwargs):
                parsed_args = self.parse(
                    argmap, req=obj.request, targets=targets)

                if as_kwargs:
                    kwargs.update(parsed_args)
                else:
                    args = (parsed_args,) + args

                return func(obj, *args, **kwargs)
            return wrapper
        return decorator


def get_value(d, name, multiple):
    """Handle gets from 'multidicts' made of lists

    It handles cases: ``{"key": [value]}`` and ``{"key": value}``
    """
    value = d.get(name)

    if multiple:
        return [] if value is None else value

    if value and isinstance(value, list):
        return value[0]

    return value


parser = TornadoParser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs
