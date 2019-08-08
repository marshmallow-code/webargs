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
from webargs.core import json


class DjangoParser(core.Parser):
    """Django request argument parser.

    .. warning::

        :class:`DjangoParser` does not override
        :meth:`handle_error <webargs.core.Parser.handle_error>`, so your Django
        views are responsible for catching any :exc:`ValidationErrors` raised by
        the parser and returning the appropriate `HTTPResponse`.
    """

    def _load_json_data(self, req):
        json_data = self._cache.get("json")
        if json_data is None:
            try:
                self._cache["json"] = json_data = core.parse_json(req.body)
            except AttributeError:
                return core.missing
            except json.JSONDecodeError as e:
                if e.doc == "":
                    return core.missing
                else:
                    return self.handle_invalid_json_error(e, req)
        return json_data

    def get_args_by_location(self, req, locations):
        result = {}
        if "json" in locations:
            try:
                data = self._load_json_data(req)
            except json.JSONDecodeError:
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
            raise NotImplementedError(
                "Header parsing not supported by {0}".format(self.__class__.__name__)
            )
        if "cookies" in locations:
            result["cookies"] = req.COOKIES.keys()
        if "files" in locations:
            result["files"] = req.FILES.keys()
        return result

    def parse_querystring(self, req, name, field):
        """Pull the querystring value from the request."""
        return core.get_value(req.GET, name, field)

    def parse_form(self, req, name, field):
        """Pull the form value from the request."""
        return core.get_value(req.POST, name, field)

    def parse_json(self, req, name, field):
        """Pull a json value from the request body."""
        json_data = self._load_json_data(req)
        return core.get_value(json_data, name, field, allow_many_nested=True)

    def parse_cookies(self, req, name, field):
        """Pull the value from the cookiejar."""
        return core.get_value(req.COOKIES, name, field)

    def parse_headers(self, req, name, field):
        raise NotImplementedError(
            "Header parsing not supported by {0}".format(self.__class__.__name__)
        )

    def parse_files(self, req, name, field):
        """Pull a file from the request."""
        return core.get_value(req.FILES, name, field)

    def get_request_from_view_args(self, view, args, kwargs):
        # The first argument is either `self` or `request`
        try:  # self.request
            return args[0].request
        except AttributeError:  # first arg is request
            return args[0]

    def handle_invalid_json_error(self, error, req, *args, **kwargs):
        raise error


parser = DjangoParser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs
