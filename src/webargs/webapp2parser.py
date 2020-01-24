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
from webargs.multidictproxy import MultiDictProxy


class Webapp2Parser(core.Parser):
    """webapp2 request argument parser."""

    def _raw_load_json(self, req):
        """Return a json payload from the request for the core parser's load_json."""
        if not core.is_json(req.content_type):
            return core.missing
        return core.parse_json(req.body)

    def load_querystring(self, req, schema):
        """Return query params from the request as a MultiDictProxy."""
        return MultiDictProxy(req.GET, schema)

    def load_form(self, req, schema):
        """Return form values from the request as a MultiDictProxy."""
        return MultiDictProxy(req.POST, schema)

    def load_cookies(self, req, schema):
        """Return cookies from the request as a MultiDictProxy."""
        return MultiDictProxy(req.cookies, schema)

    def load_headers(self, req, schema):
        """Return headers from the request as a MultiDictProxy."""
        return MultiDictProxy(req.headers, schema)

    def load_files(self, req, schema):
        """Return files from the request as a MultiDictProxy."""
        files = ((k, v) for k, v in req.POST.items() if hasattr(v, "file"))
        return MultiDictProxy(webob.multidict.MultiDict(files), schema)

    def get_default_request(self):
        return webapp2.get_request()


parser = Webapp2Parser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs
