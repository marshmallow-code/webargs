"""A simple number and datetime addition JSON API.
Demonstrates different strategies for parsing arguments
with the FalconParser.

Run the app:

    $ pip install gunicorn
    $ gunicorn examples.falcon_example:app

Try the following with httpie (a cURL-like utility, http://httpie.org):

    $ pip install httpie
    $ http GET :8000/
    $ http GET :8000/ name==Ada
    $ http POST :8000/add x=40 y=2
    $ http POST :8000/dateadd value=1973-04-10 addend=63
    $ http POST :8000/dateadd value=2014-10-23 addend=525600 unit=minutes
"""
import datetime as dt
try:
    import simplejson as json
except ImportError:
    import json

import falcon
from webargs import fields, validate
from webargs.falconparser import use_args, use_kwargs, parser

### Middleware and hooks ###

class JSONTranslator(object):
    def process_response(self, req, resp, resource):
        if 'result' not in req.context:
            return
        resp.body = json.dumps(req.context['result'])


def add_args(argmap, **kwargs):
    def hook(req, resp, params):
        req.context['args'] = parser.parse(argmap, req=req, **kwargs)
    return hook

### Resources ###

class HelloResource(object):
    """A welcome page."""

    hello_args = {
        'name': fields.Str(missing='Friend', location='query')
    }

    @use_args(hello_args)
    def on_get(self, req, resp, args):
        req.context['result'] = {'message': 'Welcome, {}!'.format(args['name'])}

class AdderResource(object):
    """An addition endpoint."""

    adder_args = {
        'x': fields.Float(required=True),
        'y': fields.Float(required=True),
    }

    @use_kwargs(adder_args)
    def on_post(self, req, resp, x, y):
        req.context['result'] = {'result': x + y}


class DateAddResource(object):
    """A datetime adder endpoint."""

    dateadd_args = {
        'value': fields.DateTime(required=False),
        'addend': fields.Int(required=True, validate=validate.Range(min=1)),
        'unit': fields.Str(missing='days', validate=validate.OneOf(['minutes', 'days']))
    }

    @falcon.before(add_args(dateadd_args))
    def on_post(self, req, resp):
        """A datetime adder endpoint."""
        args = req.context['args']
        value = args['value'] or dt.datetime.utcnow()
        if args['unit'] == 'minutes':
            delta = dt.timedelta(minutes=args['addend'])
        else:
            delta = dt.timedelta(days=args['addend'])
        result = value + delta
        req.context['result'] = {'result': result.isoformat()}

app = falcon.API(middleware=[
    JSONTranslator()
])
app.add_route('/', HelloResource())
app.add_route('/add', AdderResource())
app.add_route('/dateadd', DateAddResource())
