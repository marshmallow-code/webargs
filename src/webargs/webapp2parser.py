# -*- coding: utf-8 -*-
"""Webapp2 request argument parsing module.

Example: ::

    import webapp2

    from marshmallow import fields
    from webargs.webobparser import use_args

    hello_args = {
        'name': fields.Str(missing='World')
    }

    class MainPage(webapp2.RequestHandler):

        @use_args(hello_args)
        def get_args(self, args):
            self.response.write('Hello, {name}!'.format(name=args['name']))

        @use_kwargs(hello_args)
        def get_kwargs(self, name=None):
            self.response.write('Hello, {name}!'.format(name=name))

    app = webapp2.WSGIApplication([
        webapp2.Route(r'/hello', MainPage, handler_method='get_args'),
        webapp2.Route(r'/hello_dict', MainPage, handler_method='get_kwargs'),
    ], debug=True)
"""
import webapp2
import webob.multidict

from webargs import core
from webargs.core import json


class Webapp2Parser(core.Parser):
    """webapp2 request argument parser."""

    def _load_files_mdict(self, req):
        return webob.multidict.MultiDict(
            (k, v) for k, v in req.POST.items() if hasattr(v, "file")
        )

    def _load_json_data(self, req):
        json_data = self._cache.get("json")
        if json_data is None:
            try:
                self._cache["json"] = json_data = core.parse_json(req.body)
            except json.JSONDecodeError as e:
                if e.doc == "":
                    return core.missing
                else:
                    raise
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
            result["headers"] = req.headers.keys()
        if "cookies" in locations:
            result["cookies"] = req.cookies.keys()
        if "files" in locations:
            result["files"] = self._load_files_mdict(req).keys()
        return result

    def parse_json(self, req, name, field):
        """Pull a json value from the request."""
        json_data = self._load_json_data(req)
        return core.get_value(json_data, name, field, allow_many_nested=True)

    def parse_querystring(self, req, name, field):
        """Pull a querystring value from the request."""
        return core.get_value(req.GET, name, field)

    def parse_form(self, req, name, field):
        """Pull a form value from the request."""
        return core.get_value(req.POST, name, field)

    def parse_cookies(self, req, name, field):
        """Pull the value from the cookiejar."""
        return core.get_value(req.cookies, name, field)

    def parse_headers(self, req, name, field):
        """Pull a value from the header data."""
        return core.get_value(req.headers, name, field)

    def parse_files(self, req, name, field):
        """Pull a file from the request."""
        return core.get_value(self._load_files_mdict(req), name, field)

    def get_default_request(self):
        return webapp2.get_request()


parser = Webapp2Parser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs
