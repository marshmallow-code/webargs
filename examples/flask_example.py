"""A simple number and datetime addition JSON API.
Run the app:

    $ python examples/flask_example.py

Try the following with httpie (a cURL-like utility, http://httpie.org):

    $ pip install httpie
    $ http GET :5001/
    $ http GET :5001/ name==Ada
    $ http POST :5001/add x=40 y=2
    $ http POST :5001/dateadd value=1973-04-10 addend=63
    $ http POST :5001/dateadd value=2014-10-23 addend=525600 unit=minutes
"""
import datetime as dt

from dateutil import parser
from flask import Flask, jsonify
from webargs import Arg, ValidationError
from webargs.flaskparser import use_args, use_kwargs

app = Flask(__name__)

hello_args = {
    'name': Arg(str, default='Friend')
}
@app.route('/', methods=['GET'])
@use_args(hello_args)
def index(args):
    """A welcome page.
    """
    return jsonify({'message': 'Welcome, {}!'.format(args['name'])})

add_args = {
    'x': Arg(float, required=True),
    'y': Arg(float, required=True),
}
@app.route('/add', methods=['POST'])
@use_kwargs(add_args)
def add(x, y):
    """An addition endpoint."""
    return jsonify({'result': x + y})


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
@app.route('/dateadd', methods=['POST'])
@use_kwargs(dateadd_args)
def dateadd(value, addend, unit):
    """A datetime adder endpoint."""
    if unit == 'minutes':
        delta = dt.timedelta(minutes=addend)
    else:
        delta = dt.timedelta(days=addend)
    result = value + delta
    return jsonify({'result': result.isoformat()})

# Return validation errors as JSON
@app.errorhandler(400)
def handle_validation_error(err):
    exc = err.data['exc']
    return jsonify({'message': str(exc)}), 400


if __name__ == '__main__':
    app.run(port=5001, debug=True)
