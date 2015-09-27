#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A Hello, World! example using Webapp2 in a Google App Engine environment

Run the app:

    $ python webapp2_example.py

Try the following with httpie (a cURL-like utility, http://httpie.org):

    $ pip install httpie
    $ http GET :5001/hello
    $ http GET :5001/hello name==Ada
    $ http POST :5001/hello_dict name=awesome
    $ http POST :5001/hello_dict
"""

import webapp2

from webargs import fields
from webargs.webapp2parser import use_args, use_kwargs

hello_args = {
    'name': fields.Str(missing='World')
}

class MainPage(webapp2.RequestHandler):

    @use_args(hello_args)
    def get_args(self, args):
        # args is a dict of parsed items from hello_args
        self.response.write('Hello, {name}!'.format(name=args['name']))

    @use_kwargs(hello_args)
    def get_kwargs(self, name=None):
        self.response.write('Hello, {name}!'.format(name=name))

app = webapp2.WSGIApplication([
    webapp2.Route(r'/hello', MainPage, handler_method='get_args'),
    webapp2.Route(r'/hello_dict', MainPage, handler_method='get_kwargs'),
], debug=True)


if __name__ == '__main__':
    from wsgiref.simple_server import make_server
    httpd = make_server('', 5001, app)
    httpd.serve_forever()
