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
from webargs import core
import webapp2
import webapp2_extras.json


class Webapp2Parser(core.Parser):
    """webapp2 request argument parser."""

    def parse_json(self, req):
        """Pull a json value from the request."""
        try:
            json_data = webapp2_extras.json.decode(req.body)
        except ValueError:
            return {}
        return json_data

    def parse_querystring(self, req):
        """Pull a querystring value from the request."""
        return req.GET.mixed()

    def parse_form(self, req):
        """Pull a form value from the request."""
        return req.POST.mixed()

    def parse_cookies(self, req):
        """Pull the value from the cookiejar."""
        return req.cookies

    def parse_headers(self, req):
        """Pull a value from the header data.

        This also does case normalisation which is a problem
        """
        headers = {}
        for key, value in req.headers.items():
            headers[key] = value
        return headers

    def parse_files(self, req):
        """Pull a file from the request."""
        files = ((k, v) for k, v in req.POST.items() if hasattr(v, 'file'))
        files_map = {}
        for key, value in files:
            current = files_map.get(key)
            if current is None:
                files_map[key] = value
            elif isinstance(current, list):
                current.append(value)
            else:
                files_map[key] = [value, current]
        return files_map

    def get_default_request(self):
        return webapp2.get_request()

parser = Webapp2Parser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs
