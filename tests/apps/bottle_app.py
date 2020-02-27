from bottle import Bottle, HTTPResponse, debug, request, response

import marshmallow as ma
from webargs import fields
from webargs.bottleparser import parser, use_args, use_kwargs
from webargs.core import json, MARSHMALLOW_VERSION_INFO


hello_args = {"name": fields.Str(missing="World", validate=lambda n: len(n) >= 3)}
hello_multiple = {"name": fields.List(fields.Str())}


class HelloSchema(ma.Schema):
    name = fields.Str(missing="World", validate=lambda n: len(n) >= 3)


strict_kwargs = {"strict": True} if MARSHMALLOW_VERSION_INFO[0] < 3 else {}
hello_many_schema = HelloSchema(many=True, **strict_kwargs)

# variant which ignores unknown fields
exclude_kwargs = (
    {"strict": True} if MARSHMALLOW_VERSION_INFO[0] < 3 else {"unknown": ma.EXCLUDE}
)
hello_exclude_schema = HelloSchema(**exclude_kwargs)


app = Bottle()
debug(True)


@app.route("/echo", method=["GET"])
def echo():
    return parser.parse(hello_args, request, location="query")


@app.route("/echo_form", method=["POST"])
def echo_form():
    return parser.parse(hello_args, location="form")


@app.route("/echo_json", method=["POST"])
def echo_json():
    return parser.parse(hello_args, location="json")


@app.route("/echo_json_or_form", method=["POST"])
def echo_json_or_form():
    return parser.parse(hello_args, location="json_or_form")


@app.route("/echo_use_args", method=["GET"])
@use_args(hello_args, location="query")
def echo_use_args(args):
    return args


@app.route(
    "/echo_use_args_validated",
    method=["POST"],
    apply=use_args(
        {"value": fields.Int()},
        validate=lambda args: args["value"] > 42,
        location="form",
    ),
)
def echo_use_args_validated(args):
    return args


@app.route("/echo_ignoring_extra_data", method=["POST"])
def echo_json_ignore_extra_data():
    return parser.parse(hello_exclude_schema)


@app.route(
    "/echo_use_kwargs", method=["GET"], apply=use_kwargs(hello_args, location="query")
)
def echo_use_kwargs(name):
    return {"name": name}


@app.route("/echo_multi", method=["GET"])
def echo_multi():
    return parser.parse(hello_multiple, request, location="query")


@app.route("/echo_multi_form", method=["POST"])
def multi_form():
    return parser.parse(hello_multiple, location="form")


@app.route("/echo_multi_json", method=["POST"])
def multi_json():
    return parser.parse(hello_multiple)


@app.route("/echo_many_schema", method=["POST"])
def echo_many_schema():
    arguments = parser.parse(hello_many_schema, request)
    return HTTPResponse(body=json.dumps(arguments), content_type="application/json")


@app.route(
    "/echo_use_args_with_path_param/<name>",
    apply=use_args({"value": fields.Int()}, location="query"),
)
def echo_use_args_with_path_param(args, name):
    return args


@app.route(
    "/echo_use_kwargs_with_path_param/<name>",
    apply=use_kwargs({"value": fields.Int()}, location="query"),
)
def echo_use_kwargs_with_path_param(name, value):
    return {"value": value}


@app.route("/error", method=["GET", "POST"])
def always_error():
    def always_fail(value):
        raise ma.ValidationError("something went wrong")

    args = {"text": fields.Str(validate=always_fail)}
    return parser.parse(args)


@app.route("/echo_headers")
def echo_headers():
    # the "exclude schema" must be used in this case because WSGI headers may
    # be populated with many fields not sent by the caller
    return parser.parse(hello_exclude_schema, request, location="headers")


@app.route("/echo_cookie")
def echo_cookie():
    return parser.parse(hello_args, request, location="cookies")


@app.route("/echo_file", method=["POST"])
def echo_file():
    args = {"myfile": fields.Field()}
    result = parser.parse(args, location="files")
    myfile = result["myfile"]
    content = myfile.file.read().decode("utf8")
    return {"myfile": content}


@app.route("/echo_nested", method=["POST"])
def echo_nested():
    args = {"name": fields.Nested({"first": fields.Str(), "last": fields.Str()})}
    return parser.parse(args)


@app.route("/echo_nested_many", method=["POST"])
def echo_nested_many():
    args = {
        "users": fields.Nested({"id": fields.Int(), "name": fields.Str()}, many=True)
    }
    return parser.parse(args)


@app.error(400)
@app.error(422)
def handle_error(err):
    response.content_type = "application/json"
    return err.body
