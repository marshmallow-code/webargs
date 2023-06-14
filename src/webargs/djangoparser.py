"""Django request argument parsing.

Example usage: ::

    from django.views.generic import View
    from django.http import HttpResponse
    from marshmallow import fields
    from webargs.djangoparser import use_args

    hello_args = {
        'name': fields.Str(load_default='World')
    }

    class MyView(View):

        @use_args(hello_args)
        def get(self, args, request):
            return HttpResponse('Hello ' + args['name'])
"""
import django

from webargs import core


def is_json_request(req):
    return core.is_json(req.content_type)


class DjangoParser(core.Parser[django.http.HttpRequest]):
    """Django request argument parser.

    .. warning::

        :class:`DjangoParser` does not override
        :meth:`handle_error <webargs.core.Parser.handle_error>`, so your Django
        views are responsible for catching any :exc:`ValidationErrors` raised by
        the parser and returning the appropriate `HTTPResponse`.
    """

    def _raw_load_json(self, req: django.http.HttpRequest):
        """Read a json payload from the request for the core parser's load_json

        Checks the input mimetype and may return 'missing' if the mimetype is
        non-json, even if the request body is parseable as json."""
        if not is_json_request(req):
            return core.missing

        return core.parse_json(req.body)

    def load_querystring(self, req: django.http.HttpRequest, schema):
        """Return query params from the request as a MultiDictProxy."""
        return self._makeproxy(req.GET, schema)

    def load_form(self, req: django.http.HttpRequest, schema):
        """Return form values from the request as a MultiDictProxy."""
        return self._makeproxy(req.POST, schema)

    def load_cookies(self, req: django.http.HttpRequest, schema):
        """Return cookies from the request."""
        return req.COOKIES

    def load_headers(self, req: django.http.HttpRequest, schema):
        """Return headers from the request."""
        # Django's HttpRequest.headers is a case-insensitive dict type, but it
        # isn't a multidict, so this is not proxied
        return req.headers

    def load_files(self, req: django.http.HttpRequest, schema):
        """Return files from the request as a MultiDictProxy."""
        return self._makeproxy(req.FILES, schema)

    def get_request_from_view_args(self, view, args, kwargs):
        # The first argument is either `self` or `request`
        try:  # self.request
            return args[0].request
        except AttributeError:  # first arg is request
            return args[0]


parser = DjangoParser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs
