"""Example implementation of using a marshmallow Schema for both request input
and output with a `use_schema` decorator.
Run the app:

    $ python examples/schema_example.py

Try the following with httpie (a cURL-like utility, http://httpie.org):

    $ pip install httpie
    $ http GET :5001/users/
    $ http GET :5001/users/42
    $ http POST :5001/users/ usename=brian first_name=Brian last_name=May
    $ http PATCH :5001/users/42 username=freddie
    $ http GET :5001/users/ limit==1
"""
import functools
from flask import Flask, request, jsonify
import random

from marshmallow import Schema, fields, post_dump
from webargs.flaskparser import parser, use_kwargs

app = Flask(__name__)

##### Fake database and models #####

class Model:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def update(self, **kwargs):
        self.__dict__.update(kwargs)

    @classmethod
    def insert(cls, db, **kwargs):
        collection = db[cls.collection]
        new_id = None
        if 'id' in kwargs:  # for setting up fixtures
            new_id = kwargs.pop('id')
        else:  # find a new id
            found_id = False
            while not found_id:
                new_id = random.randint(1, 9999)
                if new_id not in collection:
                    found_id = True
        new_record = cls(id=new_id, **kwargs)
        collection[new_id] = new_record
        return new_record

class User(Model):
    collection = 'users'

db = {'users': {}}


##### use_schema #####

def use_schema(schema, list_view=False, locations=None):
    """View decorator for using a marshmallow schema to
        (1) parse a request's input and
        (2) serializing the view's output to a JSON response.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            use_args_wrapper = parser.use_args(schema, locations=locations)
            # Function wrapped with use_args
            func_with_args = use_args_wrapper(func)
            ret = func_with_args(*args, **kwargs)
            # Serialize and jsonify the return value
            return jsonify(schema.dump(ret, many=list_view).data)
        return wrapped
    return decorator

##### Schemas #####

class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str()
    first_name = fields.Str()
    last_name = fields.Str()

    class Meta:
        strict = True

    @post_dump(pass_many=True)
    def wrap_with_envelope(self, data, many):
        return {'data': data}


##### Routes #####

@app.route('/users/<int:user_id>', methods=['GET', 'PATCH'])
@use_schema(UserSchema())
def user_detail(reqargs, user_id):
    user = db['users'].get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    if request.method == 'PATCH' and reqargs:
        user.update(**reqargs)
    return user

# You can add additional arguments with use_kwargs
@app.route('/users/', methods=['GET', 'POST'])
@use_kwargs({'limit': fields.Int(missing=10, location='query')})
@use_schema(UserSchema(), list_view=True)
def user_list(reqargs, limit):
    users = db['users'].values()
    if request.method == 'POST':
        User.insert(db=db, **reqargs)
    return list(users)[:limit]

# Return validation errors as JSON
@app.errorhandler(422)
def handle_validation_error(err):
    exc = err.data['exc']
    return jsonify({'errors': exc.messages}), 422

if __name__ == "__main__":
    User.insert(db=db, id=42, username='fred', first_name='Freddie', last_name='Mercury')
    app.run(port=5001, debug=True)
