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

from webargs import core


class DjangoParser(core.Parser):
    """Django request argument parser.

    .. warning::

        :class:`DjangoParser` does not override
        :meth:`handle_error <webargs.core.Parser.handle_error>`, so your Django
        views are responsible for catching any :exc:`ValidationErrors` raised by
        the parser and returning the appropriate `HTTPResponse`.
    """

    def parse_querystring(self, req):
        """Pull the querystring value from the request."""
        return self._flatten_multidict(req.GET)

    def parse_form(self, req):
        """Pull the form value from the request."""
        return self._flatten_multidict(req.POST)

    def parse_json(self, req):
        """Pull a json value from the request body."""
        try:
            json_data = json.loads(req.body.decode('utf-8'))
        except (AttributeError, ValueError):
            return {}
        return json_data

    def parse_cookies(self, req):
        """Pull the value from the cookiejar."""
        return req.COOKIES

    def parse_headers(self, req):
        raise NotImplementedError('Header parsing not supported by {0}'
            .format(self.__class__.__name__))

    def parse_files(self, req):
        """Pull a file from the request."""
        return self._flatten_multidict(req.FILES)

    def get_request_from_view_args(self, view, args, kwargs):
        # The first argument is either `self` or `request`
        try:  # self.request
            return args[0].request
        except AttributeError:  # first arg is request
            return args[0]

    def _flatten_multidict(self, multidict):
        flat = {}
        for key, value in multidict.lists():
            count = len(value)
            if count == 1:
                flat[key] = value[0]
            elif count > 1:
                flat[key] = value
        return flat

parser = DjangoParser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs
