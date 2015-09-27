# -*- coding: utf-8 -*-
"""Tornado request argument parsing module.

Example: ::

    import tornado.web
    from marshmallow import fields
    from webargs.tornadoparser import use_args

    class HelloHandler(tornado.web.RequestHandler):

        @use_args({'name': fields.Str(missing='World')})
        def get(self, args):
            response = {'message': 'Hello {}'.format(args['name'])}
            self.write(response)
"""
import json
import functools
import logging

import marshmallow as ma
import tornado.web

from webargs import core

logger = logging.getLogger(__name__)


class HTTPError(tornado.web.HTTPError):
    """`tornado.web.HTTPError` that stores validation errors."""

    def __init__(self, *args, **kwargs):
        self.messages = kwargs.pop('messages', {})
        super(HTTPError, self).__init__(*args, **kwargs)

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
    value = d.get(name, core.missing)

    if multiple and value is not core.missing:
        return [] if value is core.missing else value

    if value and isinstance(value, (list, tuple)):
        return value[0]

    return value

class TornadoParser(core.Parser):
    """Tornado request argument parser."""

    def __init__(self, *args, **kwargs):
        super(TornadoParser, self).__init__(*args, **kwargs)
        self.json = None

    def parse_json(self, req, name, field):
        """Pull a json value from the request."""
        json_body = self._cache.get('json')
        if json_body is None:
            self._cache['json'] = parse_json_body(req)
        return get_value(self._cache['json'], name, core.is_multiple(field))

    def parse_querystring(self, req, name, field):
        """Pull a querystring value from the request."""
        return get_value(req.query_arguments, name, core.is_multiple(field))

    def parse_form(self, req, name, field):
        """Pull a form value from the request."""
        return get_value(req.body_arguments, name, core.is_multiple(field))

    def parse_headers(self, req, name, field):
        """Pull a value from the header data."""
        return get_value(req.headers, name, core.is_multiple(field))

    def parse_cookies(self, req, name, field):
        """Pull a value from the header data."""
        cookie = req.cookies.get(name)

        if cookie is not None:
            return [cookie.value] if core.is_multiple(field) else cookie.value
        else:
            return [] if core.is_multiple(field) else None

    def parse_files(self, req, name, field):
        """Pull a file from the request."""
        return get_value(req.files, name, core.is_multiple(field))

    def handle_error(self, error):
        """Handles errors during parsing. Raises a `tornado.web.HTTPError`
        with a 400 error.
        """
        logger.error(error)
        status_code = getattr(error, 'status_code', core.DEFAULT_VALIDATION_STATUS)
        if status_code == 422:
            reason = 'Unprocessable Entity'
        else:
            reason = None
        raise HTTPError(status_code, log_message=str(error.messages),
                reason=reason, messages=error.messages)

    def use_args(self, argmap, req=None, locations=core.Parser.DEFAULT_LOCATIONS,
                 as_kwargs=False, validate=None):
        """Decorator that injects parsed arguments into a view function or method.

        :param dict argmap: Either a `marshmallow.Schema` or a `dict`
            of argname -> `marshmallow.fields.Field` pairs.
        :param req: The request object to parse
        :param tuple locations: Where on the request to search for values.
        :param as_kwargs: Whether to pass arguments to the handler as kwargs
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
                parsed_args = self.parse(
                    schema, req=obj.request, locations=locations, validate=validate,
                    force_all=as_kwargs)

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
