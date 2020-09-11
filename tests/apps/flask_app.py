from flask import Flask, jsonify as J, Response, request
from flask.views import MethodView
import marshmallow as ma

from webargs import fields
from webargs.flaskparser import parser, use_args, use_kwargs
from webargs.core import json


class TestAppConfig:
    TESTING = True


hello_args = {"name": fields.Str(missing="World", validate=lambda n: len(n) >= 3)}
hello_multiple = {"name": fields.List(fields.Str())}


class HelloSchema(ma.Schema):
    name = fields.Str(missing="World", validate=lambda n: len(n) >= 3)


hello_many_schema = HelloSchema(many=True)

app = Flask(__name__)
app.config.from_object(TestAppConfig)


@app.route("/echo", methods=["GET"])
def echo():
    return J(parser.parse(hello_args, location="query"))


@app.route("/echo_form", methods=["POST"])
def echo_form():
    return J(parser.parse(hello_args, location="form"))


@app.route("/echo_json", methods=["POST"])
def echo_json():
    return J(parser.parse(hello_args, location="json"))


@app.route("/echo_json_or_form", methods=["POST"])
def echo_json_or_form():
    return J(parser.parse(hello_args, location="json_or_form"))


@app.route("/echo_use_args", methods=["GET"])
@use_args(hello_args, location="query")
def echo_use_args(args):
    return J(args)


@app.route("/echo_use_args_validated", methods=["POST"])
@use_args(
    {"value": fields.Int()}, validate=lambda args: args["value"] > 42, location="form"
)
def echo_use_args_validated(args):
    return J(args)


@app.route("/echo_ignoring_extra_data", methods=["POST"])
def echo_json_ignore_extra_data():
    return J(parser.parse(hello_args, unknown=ma.EXCLUDE))


@app.route("/echo_use_kwargs", methods=["GET"])
@use_kwargs(hello_args, location="query")
def echo_use_kwargs(name):
    return J({"name": name})


@app.route("/echo_multi", methods=["GET"])
def multi():
    return J(parser.parse(hello_multiple, location="query"))


@app.route("/echo_multi_form", methods=["POST"])
def multi_form():
    return J(parser.parse(hello_multiple, location="form"))


@app.route("/echo_multi_json", methods=["POST"])
def multi_json():
    return J(parser.parse(hello_multiple))


@app.route("/echo_many_schema", methods=["GET", "POST"])
def many_nested():
    arguments = parser.parse(hello_many_schema)
    return Response(json.dumps(arguments), content_type="application/json")


@app.route("/echo_use_args_with_path_param/<name>")
@use_args({"value": fields.Int()}, location="query")
def echo_use_args_with_path(args, name):
    return J(args)


@app.route("/echo_use_kwargs_with_path_param/<name>")
@use_kwargs({"value": fields.Int()}, location="query")
def echo_use_kwargs_with_path(name, value):
    return J({"value": value})


@app.route("/error", methods=["GET", "POST"])
def error():
    def always_fail(value):
        raise ma.ValidationError("something went wrong")

    args = {"text": fields.Str(validate=always_fail)}
    return J(parser.parse(args))


@app.route("/echo_headers")
def echo_headers():
    return J(parser.parse(hello_args, location="headers"))


# as above, but in this case, turn off the default `EXCLUDE` behavior for
# `headers`, so that errors will be raised
@app.route("/echo_headers_raising")
@use_args(HelloSchema(), location="headers", unknown=None)
def echo_headers_raising(args):
    return J(args)


@app.route("/echo_cookie")
def echo_cookie():
    return J(parser.parse(hello_args, request, location="cookies"))


@app.route("/echo_file", methods=["POST"])
def echo_file():
    args = {"myfile": fields.Field()}
    result = parser.parse(args, location="files")
    fp = result["myfile"]
    content = fp.read().decode("utf8")
    return J({"myfile": content})


@app.route("/echo_view_arg/<view_arg>")
def echo_view_arg(view_arg):
    return J(parser.parse({"view_arg": fields.Int()}, location="view_args"))


@app.route("/echo_view_arg_use_args/<view_arg>")
@use_args({"view_arg": fields.Int()}, location="view_args")
def echo_view_arg_with_use_args(args, **kwargs):
    return J(args)


@app.route("/echo_nested", methods=["POST"])
def echo_nested():
    args = {"name": fields.Nested({"first": fields.Str(), "last": fields.Str()})}
    return J(parser.parse(args))


@app.route("/echo_nested_many", methods=["POST"])
def echo_nested_many():
    args = {
        "users": fields.Nested({"id": fields.Int(), "name": fields.Str()}, many=True)
    }
    return J(parser.parse(args))


@app.route("/echo_nested_many_data_key", methods=["POST"])
def echo_nested_many_with_data_key():
    args = {
        "x_field": fields.Nested({"id": fields.Int()}, many=True, data_key="X-Field")
    }
    return J(parser.parse(args))


class EchoMethodViewUseArgs(MethodView):
    @use_args({"val": fields.Int()})
    def post(self, args):
        return J(args)


app.add_url_rule(
    "/echo_method_view_use_args",
    view_func=EchoMethodViewUseArgs.as_view("echo_method_view_use_args"),
)


class EchoMethodViewUseKwargs(MethodView):
    @use_kwargs({"val": fields.Int()})
    def post(self, val):
        return J({"val": val})


app.add_url_rule(
    "/echo_method_view_use_kwargs",
    view_func=EchoMethodViewUseKwargs.as_view("echo_method_view_use_kwargs"),
)


@app.route("/echo_use_kwargs_missing", methods=["post"])
@use_kwargs({"username": fields.Str(required=True), "password": fields.Str()})
def echo_use_kwargs_missing(username, **kwargs):
    assert "password" not in kwargs
    return J({"username": username})


# Return validation errors as JSON
@app.errorhandler(422)
@app.errorhandler(400)
def handle_error(err):
    if err.code == 422:
        assert isinstance(err.data["schema"], ma.Schema)

    return J(err.data["messages"]), err.code
