"""A simple number and datetime addition JSON API.
Run the app:

    $ python examples/bottle_example.py

Try the following with httpie (a cURL-like utility, http://httpie.org):

    $ pip install httpie
    $ http GET :5001/
    $ http GET :5001/ name==Ada
    $ http POST :5001/add x=40 y=2
    $ http POST :5001/dateadd value=1973-04-10 addend=63
    $ http POST :5001/dateadd value=2014-10-23 addend=525600 unit=minutes
"""
import datetime as dt
import json

from dateutil import parser
from bottle import route, run, error, response
from webargs import Arg, ValidationError
from webargs.bottleparser import use_args, use_kwargs


hello_args = {
    'name': Arg(str, default='Friend')
}
@route('/', method='GET')
@use_args(hello_args)
def index(args):
    """A welcome page.
    """
    return {'message': 'Welcome, {}!'.format(args['name'])}

add_args = {
    'x': Arg(float, required=True),
    'y': Arg(float, required=True),
}
@route('/add', method='POST')
@use_kwargs(add_args)
def add(x, y):
    """An addition endpoint."""
    return {'result': x + y}


def string_to_datetime(val):
    return parser.parse(val)

def validate_unit(val):
    if val not in ['minutes', 'days']:
        raise ValidationError("Unit must be either 'minutes' or 'days'.")

dateadd_args = {
    'value': Arg(default=dt.datetime.utcnow, use=string_to_datetime),
    'addend': Arg(int, required=True, validate=lambda val: val >= 0),
    'unit': Arg(str, validate=validate_unit)
}
@route('/dateadd', method='POST')
@use_kwargs(dateadd_args)
def dateadd(value, addend, unit):
    """A datetime adder endpoint."""
    if unit == 'minutes':
        delta = dt.timedelta(minutes=addend)
    else:
        delta = dt.timedelta(days=addend)
    result = value + delta
    return {'result': result.isoformat()}

# Return validation errors as JSON
@error(400)
def error400(err):
    response.content_type = 'application/json'
    return json.dumps({'message': str(err.body)})

if __name__ == '__main__':
    run(port=5001, reloader=True, debug=True)
