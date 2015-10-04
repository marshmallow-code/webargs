"""A simple number and datetime addition JSON API.
Run the app:

    $ python examples/tornado_example.py

Try the following with httpie (a cURL-like utility, http://httpie.org):

    $ pip install httpie
    $ http GET :5001/
    $ http GET :5001/ name==Ada
    $ http POST :5001/add x=40 y=2
    $ http POST :5001/dateadd value=1973-04-10 addend=63
    $ http POST :5001/dateadd value=2014-10-23 addend=525600 unit=minutes
"""
import datetime as dt

import tornado.ioloop
from tornado.web import RequestHandler
from webargs import fields, validate
from webargs.tornadoparser import use_args, use_kwargs


class BaseRequestHandler(RequestHandler):

    def write_error(self, status_code, **kwargs):
        """Write errors as JSON."""
        self.set_header('Content-Type', 'application/json')
        if 'exc_info' in kwargs:
            etype, exc, traceback = kwargs['exc_info']
            if hasattr(exc, 'messages'):
                self.write({'errors': exc.messages})
                self.finish()

class HelloHandler(BaseRequestHandler):
    """A welcome page."""

    hello_args = {
        'name': fields.Str(missing='Friend')
    }

    @use_args(hello_args)
    def get(self, args):
        response = {'message': 'Welcome, {}!'.format(args['name'])}
        self.write(response)


class AdderHandler(BaseRequestHandler):
    """An addition endpoint."""

    add_args = {
        'x': fields.Float(required=True),
        'y': fields.Float(required=True),
    }

    @use_kwargs(add_args)
    def post(self, x, y):
        self.write({'result': x + y})


class DateAddHandler(BaseRequestHandler):
    """A datetime adder endpoint."""

    dateadd_args = {
        'value': fields.DateTime(required=False),
        'addend': fields.Int(required=True, validate=validate.Range(min=1)),
        'unit': fields.Str(missing='days', validate=validate.OneOf(['minutes', 'days']))
    }

    @use_kwargs(dateadd_args)
    def post(self, value, addend, unit):
        """A datetime adder endpoint."""
        value = value or dt.datetime.utcnow()
        if unit == 'minutes':
            delta = dt.timedelta(minutes=addend)
        else:
            delta = dt.timedelta(days=addend)
        result = value + delta
        self.write({'result': result.isoformat()})

if __name__ == '__main__':
    app = tornado.web.Application([
        (r'/', HelloHandler),
        (r'/add', AdderHandler),
        (r'/dateadd', DateAddHandler),
    ], debug=True)
    app.listen(5001)
    tornado.ioloop.IOLoop.instance().start()
