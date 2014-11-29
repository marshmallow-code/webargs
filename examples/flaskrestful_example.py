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

from dateutil import parser as dateparser
from flask import Flask
from flask.ext import restful

from webargs import Arg, ValidationError
from webargs.flaskparser import use_args, use_kwargs, parser

app = Flask(__name__)
api = restful.Api(app)


class IndexResource(restful.Resource):
    """A welcome page."""

    hello_args = {
        'name': Arg(str, default='Friend')
    }

    @use_args(hello_args)
    def get(self, args):
        return {'message': 'Welcome, {}!'.format(args['name'])}


class AddResource(restful.Resource):
    """An addition endpoint."""

    add_args = {
        'x': Arg(float, required=True),
        'y': Arg(float, required=True),
    }

    @use_kwargs(add_args)
    def post(self, x, y):
        """An addition endpoint."""
        return {'result': x + y}


def string_to_datetime(val):
    return dateparser.parse(val)

def validate_unit(val):
    if val not in ['minutes', 'days']:
        raise ValidationError("Unit must be either 'minutes' or 'days'.")

class DateAddResource(restful.Resource):

    dateadd_args = {
        'value': Arg(default=dt.datetime.utcnow, use=string_to_datetime),
        'addend': Arg(int, required=True, validate=lambda val: val >= 0),
        'unit': Arg(str, validate=validate_unit)
    }

    @use_kwargs(dateadd_args)
    def post(self, value, addend, unit):
        """A datetime adder endpoint."""
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
    code, msg = getattr(err, 'status_code', 400), getattr(err, 'message', 'Invalid Request')
    restful.abort(code, message=msg)

if __name__ == '__main__':
    api.add_resource(IndexResource, '/')
    api.add_resource(AddResource, '/add')
    api.add_resource(DateAddResource, '/dateadd')
    app.run(port=5001, debug=True)
