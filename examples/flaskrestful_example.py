# -*- coding: utf-8 -*-
"""A simple number and datetime addition JSON API.
Run the app:

    $ python examples/flaskrestful_example.py

Try the following with httpie (a cURL-like utility, http://httpie.org):

    $ pip install httpie
    $ http GET :5001/
    $ http GET :5001/ name==Ada
    $ http POST :5001/add x=40 y=2
    $ http POST :5001/dateadd value=1973-04-10 addend=63
    $ http POST :5001/dateadd value=2014-10-23 addend=525600 unit=minutes
"""
import datetime as dt

from flask import Flask
from flask.ext import restful

from webargs import fields, validate
from webargs.flaskparser import use_args, use_kwargs, parser

app = Flask(__name__)
api = restful.Api(app)


class IndexResource(restful.Resource):
    """A welcome page."""

    hello_args = {
        'name': fields.Str(missing='Friend')
    }

    @use_args(hello_args)
    def get(self, args):
        return {'message': 'Welcome, {}!'.format(args['name'])}


class AddResource(restful.Resource):
    """An addition endpoint."""

    add_args = {
        'x': fields.Float(required=True),
        'y': fields.Float(required=True),
    }

    @use_kwargs(add_args)
    def post(self, x, y):
        """An addition endpoint."""
        return {'result': x + y}

class DateAddResource(restful.Resource):

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
        return {'result': result.isoformat()}

# This error handler is necessary for usage with Flask-RESTful
@parser.error_handler
def handle_request_parsing_error(err):
    """webargs error handler that uses Flask-RESTful's abort function to return
    a JSON error response to the client.
    """
    restful.abort(422, errors=err.messages)

if __name__ == '__main__':
    api.add_resource(IndexResource, '/')
    api.add_resource(AddResource, '/add')
    api.add_resource(DateAddResource, '/dateadd')
    app.run(port=5001, debug=True)
