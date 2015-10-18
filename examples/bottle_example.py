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

from bottle import route, run, error, response
from webargs import fields, validate
from webargs.bottleparser import use_args, use_kwargs


hello_args = {
    'name': fields.Str(missing='Friend')
}
@route('/', method='GET')
@use_args(hello_args)
def index(args):
    """A welcome page.
    """
    return {'message': 'Welcome, {}!'.format(args['name'])}

add_args = {
    'x': fields.Float(required=True),
    'y': fields.Float(required=True),
}
@route('/add', method='POST')
@use_kwargs(add_args)
def add(x, y):
    """An addition endpoint."""
    return {'result': x + y}

dateadd_args = {
    'value': fields.DateTime(required=False),
    'addend': fields.Int(required=True, validate=validate.Range(min=1)),
    'unit': fields.Str(missing='days', validate=validate.OneOf(['minutes', 'days']))
}
@route('/dateadd', method='POST')
@use_kwargs(dateadd_args)
def dateadd(value, addend, unit):
    """A datetime adder endpoint."""
    value = value or dt.datetime.utcnow()
    if unit == 'minutes':
        delta = dt.timedelta(minutes=addend)
    else:
        delta = dt.timedelta(days=addend)
    result = value + delta
    return {'result': result.isoformat()}

# Return validation errors as JSON
@error(422)
def error422(err):
    response.content_type = 'application/json'
    return err.body

if __name__ == '__main__':
    run(port=5001, reloader=True, debug=True)
