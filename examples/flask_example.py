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

from flask import Flask, jsonify
from webargs import fields, validate
from webargs.flaskparser import use_args, use_kwargs

app = Flask(__name__)

hello_args = {
    'name': fields.Str(missing='Friend')
}
@app.route('/', methods=['GET'])
@use_args(hello_args)
def index(args):
    """A welcome page.
    """
    return jsonify({'message': 'Welcome, {}!'.format(args['name'])})

add_args = {
    'x': fields.Float(required=True),
    'y': fields.Float(required=True),
}
@app.route('/add', methods=['POST'])
@use_kwargs(add_args)
def add(x, y):
    """An addition endpoint."""
    return jsonify({'result': x + y})

dateadd_args = {
    'value': fields.DateTime(required=False),
    'addend': fields.Int(required=True, validate=validate.Range(min=1)),
    'unit': fields.Str(missing='days', validate=validate.OneOf(['minutes', 'days']))
}
@app.route('/dateadd', methods=['POST'])
@use_kwargs(dateadd_args)
def dateadd(value, addend, unit):
    """A datetime adder endpoint."""
    value = value or dt.datetime.utcnow()
    if unit == 'minutes':
        delta = dt.timedelta(minutes=addend)
    else:
        delta = dt.timedelta(days=addend)
    result = value + delta
    return jsonify({'result': result.isoformat()})

# Return validation errors as JSON
@app.errorhandler(422)
def handle_validation_error(err):
    exc = err.exc
    return jsonify({'errors': exc.messages}), 422


if __name__ == '__main__':
    app.run(port=5001, debug=True)
