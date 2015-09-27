# -*- coding: utf-8 -*-
"""Django request argument parsing.

Example usage: ::

    from django.views.generic import View
    from django.http import HttpResponse
    from marshmallow import fields
    from webargs.djangoparser import use_args

    hello_args = {
        'name': fields.Str(missing='World')
    }

    class MyView(View):

        @use_args(hello_args)
        def get(self, args, request):
            return HttpResponse('Hello ' + args['name'])
"""
import json
import functools
import logging

import marshmallow as ma

from webargs import core

logger = logging.getLogger(__name__)

class DjangoParser(core.Parser):
    """Django request argument parser.

    .. warning::

        :class:`DjangoParser` does not override
        :meth:`handle_error <webargs.core.Parser.handle_error>`, so your Django
        views are responsible for catching any :exc:`ValidationErrors` raised by
        the parser and returning the appropriate `HTTPResponse`.
    """

    def parse_querystring(self, req, name, field):
        """Pull the querystring value from the request."""
        return core.get_value(req.GET, name, core.is_multiple(field))

    def parse_form(self, req, name, field):
        """Pull the form value from the request."""
        return core.get_value(req.POST, name, core.is_multiple(field))

    def parse_json(self, req, name, field):
        """Pull a json value from the request body."""
        try:
            reqdata = json.loads(req.body.decode('utf-8'))
            return core.get_value(reqdata, name, core.is_multiple(field))
        except (AttributeError, ValueError):
            pass
        return core.missing

    def parse_cookies(self, req, name, field):
        """Pull the value from the cookiejar."""
        return core.get_value(req.COOKIES, name, core.is_multiple(field))

    def parse_headers(self, req, name, field):
        raise NotImplementedError('Header parsing not supported by {0}'
            .format(self.__class__.__name__))

    def parse_files(self, req, name, field):
        """Pull a file from the request."""
        return core.get_value(req.FILES, name, core.is_multiple(field))

    def use_args(self, argmap, req=None, locations=core.Parser.DEFAULT_LOCATIONS,
                 as_kwargs=False, validate=None):
        """Decorator that injects parsed arguments into a view function or method.

        Example: ::

            @parser.use_args({'name': 'World'})
            def myview(request, args):
                return HttpResponse('Hello ' + args['name'])

        :param dict argmap: Either a `marshmallow.Schema` or a `dict`
            of argname -> `marshmallow.fields.Field` pairs.
        :param req: The request object to parse
        :param tuple locations: Where on the request to search for values.
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
                    request = obj.request
                except AttributeError:  # first arg is request
                    request = obj
                parsed_args = self.parse(schema, req=request, locations=locations,
                                         validate=validate, force_all=as_kwargs)
                return func(obj, parsed_args, *args, **kwargs)
            return wrapper
        return decorator

parser = DjangoParser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs
