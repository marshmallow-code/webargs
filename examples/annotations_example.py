"""Example of using Python 3 function annotations to define
request arguments and output schemas.
"""
import datetime as dt
import functools

from flask import Flask, jsonify, request
from marshmallow import Schema
from webargs import fields
from webargs.flaskparser import parser

app = Flask(__name__)

def route(*args, response_formatter=jsonify, **kwargs):
    """Combines `Flask.route` and webargs parsing. Allows arguments to be specified
    as function annotations. An output schema can optionally be specified by a
    return annotation.
    """
    def decorator(func):
        @app.route(*args, **kwargs)
        @functools.wraps(func)
        def wrapped_view(*a, **kw):
            annotations = getattr(func, '__annotations__', {})
            reqargs = {name: value for name, value in annotations.items() if
                        isinstance(value, fields.Field) and name != 'return'}
            response_schema = annotations.get('return')
            parsed = parser.parse(reqargs, request, force_all=True)
            kw.update(parsed)
            response_data = func(*a, **kw)
            if response_schema:
                return response_formatter(response_schema.dump(response_data).data)
            else:
                return response_formatter(func(*a, **kw))
        return wrapped_view

    return decorator


@route('/', methods=['GET'])
def index(name: fields.Str(missing='Friend')):
    return {'message': 'Hello, {}!'.format(name)}


@route('/add', methods=['POST'])
def add(x: fields.Float(required=True), y: fields.Float(required=True)):
    return {'result': x + y}


class UserSchema(Schema):
    id = fields.Int()
    name = fields.Str()
    date_created = fields.DateTime(dump_only=True)

class User:
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.date_created = dt.datetime.utcnow()

@route('/users/<int:user_id>', methods=['POST'])
def user_detail(user_id, name: fields.Str(required=True)) -> UserSchema():
    user = User(id=user_id, name=name)
    return user

# Return validation errors as JSON
@app.errorhandler(422)
def handle_validation_error(err):
    exc = err.exc
    return jsonify({'errors': exc.messages}), 422

if __name__ == '__main__':
    app.run(port=5001, debug=True)
