"""Example of using Python 3 function annotations to define
request arguments and output schemas.

Run the app:

    $ python examples/annotations_example.py

Try the following with httpie (a cURL-like utility, http://httpie.org):

    $ pip install httpie
    $ http GET :5001/
    $ http GET :5001/ name==Ada
    $ http POST :5001/add x=40 y=2
    $ http GET :5001/users/42
"""
import random
import functools

from flask import Flask, request
from marshmallow import Schema
from webargs import fields
from webargs.flaskparser import parser


app = Flask(__name__)

##### Routing wrapper ####


def route(*args, **kwargs):
    """Combines `Flask.route` and webargs parsing. Allows arguments to be specified
    as function annotations. An output schema can optionally be specified by a
    return annotation.
    """

    def decorator(func):
        @app.route(*args, **kwargs)
        @functools.wraps(func)
        def wrapped_view(*a, **kw):
            annotations = getattr(func, "__annotations__", {})
            reqargs = {
                name: value
                for name, value in annotations.items()
                if isinstance(value, fields.Field) and name != "return"
            }
            response_schema = annotations.get("return")
            schema_cls = Schema.from_dict(reqargs)
            partial = request.method != "POST"
            parsed = parser.parse(schema_cls(partial=partial), request)
            kw.update(parsed)
            response_data = func(*a, **kw)
            if response_schema:
                return response_schema.dump(response_data)
            else:
                return func(*a, **kw)

        return wrapped_view

    return decorator


##### Fake database and model #####


class Model:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def update(self, **kwargs):
        self.__dict__.update(kwargs)

    @classmethod
    def insert(cls, db, **kwargs):
        collection = db[cls.collection]
        new_id = None
        if "id" in kwargs:  # for setting up fixtures
            new_id = kwargs.pop("id")
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
    collection = "users"


db = {"users": {}}

##### Views #####


@route("/", methods=["GET"])
def index(name: fields.Str(load_default="Friend")):  # noqa: F821
    return {"message": f"Hello, {name}!"}


@route("/add", methods=["POST"])
def add(x: fields.Float(required=True), y: fields.Float(required=True)):
    return {"result": x + y}


class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    first_name = fields.Str()
    last_name = fields.Str()


@route("/users/<int:user_id>", methods=["GET", "PATCH"])
def user_detail(user_id, username: fields.Str(required=True) = None) -> UserSchema():
    user = db["users"].get(user_id)
    if not user:
        return {"message": "User not found"}, 404
    if request.method == "PATCH":
        user.update(username=username)
    return user


# Return validation errors as JSON
@app.errorhandler(422)
@app.errorhandler(400)
def handle_error(err):
    headers = err.data.get("headers", None)
    messages = err.data.get("messages", ["Invalid request."])
    if headers:
        return {"errors": messages}, err.code, headers
    else:
        return {"errors": messages}, err.code


if __name__ == "__main__":
    User.insert(
        db=db, id=42, username="fred", first_name="Freddie", last_name="Mercury"
    )
    app.run(port=5001, debug=True)
