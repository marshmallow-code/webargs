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
from webargs import core
from webargs.multidictproxy import MultiDictProxy


class DjangoParser(core.Parser):
    """Django request argument parser.

    .. warning::

        :class:`DjangoParser` does not override
        :meth:`handle_error <webargs.core.Parser.handle_error>`, so your Django
        views are responsible for catching any :exc:`ValidationErrors` raised by
        the parser and returning the appropriate `HTTPResponse`.
    """

    def _raw_load_json(self, req):
        """Read a json payload from the request for the core parser's load_json"""
        return core.parse_json(req.body)

    def load_querystring(self, req, schema):
        """Return query params from the request as a MultiDictProxy."""
        return MultiDictProxy(req.GET, schema)

    def load_form(self, req, schema):
        """Return form values from the request as a MultiDictProxy."""
        return MultiDictProxy(req.POST, schema)

    def load_cookies(self, req, schema):
        """Return cookies from the request."""
        return req.COOKIES

    def load_headers(self, req, schema):
        raise NotImplementedError(
            "Header parsing not supported by {0}".format(self.__class__.__name__)
        )

    def load_files(self, req, schema):
        """Return files from the request as a MultiDictProxy."""
        return MultiDictProxy(req.FILES, schema)

    def get_request_from_view_args(self, view, args, kwargs):
        # The first argument is either `self` or `request`
        try:  # self.request
            return args[0].request
        except AttributeError:  # first arg is request
            return args[0]


parser = DjangoParser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs
