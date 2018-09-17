from sanic import Sanic
from sanic.response import json as J
from sanic.views import HTTPMethodView


import marshmallow as ma
from webargs import fields, ValidationError, missing
from webargs.sanicparser import parser, use_args, use_kwargs, HandleValidationError
from webargs.core import MARSHMALLOW_VERSION_INFO


class TestAppConfig:
    TESTING = True


hello_args = {"name": fields.Str(missing="World", validate=lambda n: len(n) >= 3)}
hello_multiple = {"name": fields.List(fields.Str())}


class HelloSchema(ma.Schema):
    name = fields.Str(missing="World", validate=lambda n: len(n) >= 3)


strict_kwargs = {"strict": True} if MARSHMALLOW_VERSION_INFO[0] < 3 else {}
hello_many_schema = HelloSchema(many=True, **strict_kwargs)

app = Sanic(__name__)
app.config.from_object(TestAppConfig)


@app.route("/echo", methods=["GET", "POST"])
async def echo(request):
    parsed = await parser.parse(hello_args, request)
    return J(parsed)


@app.route("/echo_query")
async def echo_query(request):
    parsed = await parser.parse(hello_args, request, locations=("query",))
    return J(parsed)


@app.route("/echo_use_args", methods=["GET", "POST"])
@use_args(hello_args)
async def echo_use_args(request, args):
    return J(args)


@app.route("/echo_use_args_validated", methods=["GET", "POST"])
@use_args({"value": fields.Int(required=True)}, validate=lambda args: args["value"] > 42)
async def echo_use_args_validated(request, args):
    return J(args)


@app.route("/echo_use_kwargs", methods=["GET", "POST"])
@use_kwargs(hello_args)
async def echo_use_kwargs(request, name):
    return J({"name": name})


@app.route("/echo_multi", methods=["GET", "POST"])
async def multi(request):
    parsed = await parser.parse(hello_multiple, request)
    return J(parsed)


@app.route("/echo_many_schema", methods=["GET", "POST"])
async def many_nested(request):
    parsed = await parser.parse(hello_many_schema, request, locations=("json",))
    return J(parsed, content_type="application/json")


@app.route("/echo_use_args_with_path_param/<name>")
@use_args({"value": fields.Int()})
async def echo_use_args_with_path(request, args, name):
    return J(args)


@app.route("/echo_use_kwargs_with_path_param/<name>")
@use_kwargs({"value": fields.Int()})
async def echo_use_kwargs_with_path(request, name, value):
    return J({"value": value})


@app.route("/error", methods=["GET", "POST"])
async def error(request):
    def always_fail(value):
        raise ValidationError("something went wrong")

    args = {"text": fields.Str(validate=always_fail)}
    parsed = await parser.parse(args, request)
    return J(parsed)


@app.route("/error400", methods=["GET", "POST"])
async def error400(request):
    def always_fail(value):
        raise ValidationError("something went wrong", status_code=400)

    args = {"text": fields.Str(validate=always_fail)}
    parsed = await parser.parse(args, request)

    return J(parsed)


@app.route("/echo_headers")
async def echo_headers(request):
    parsed = await parser.parse(hello_args, request, locations=("headers",))
    return J(parsed)


@app.route("/echo_cookie")
async def echo_cookie(request):
    parsed = await parser.parse(hello_args, request, locations=("cookies",))
    return J(parsed)


@app.route("/echo_file", methods=["POST"])
async def echo_file(request):
    args = {"myfile": fields.Field()}
    result = await parser.parse(args, request, locations=("files",))
    fp = result["myfile"]
    content = fp.body.decode("utf8")
    return J({"myfile": content})


@app.route("/echo_view_arg/<view_arg>")
async def echo_view_arg(request, view_arg):
    parsed = await parser.parse({"view_arg": fields.Int()}, request, locations=("view_args",))
    return J(parsed)


@app.route("/echo_view_arg_use_args/<view_arg>")
@use_args({"view_arg": fields.Int(location="view_args")})
async def echo_view_arg_with_use_args(request, args, **kwargs):
    return J(args)


@app.route("/echo_nested", methods=["POST"])
async def echo_nested(request):
    args = {"name": fields.Nested({"first": fields.Str(), "last": fields.Str()})}
    parsed = await parser.parse(args, request)
    return J(parsed)


@app.route("/echo_nested_many", methods=["POST"])
async def echo_nested_many(request):
    args = {
        "users": fields.Nested({"id": fields.Int(), "name": fields.Str()}, many=True)
    }
    parsed = await parser.parse(args, request)
    return J(parsed)


@app.route("/echo_nested_many_data_key", methods=["POST"])
async def echo_nested_many_with_data_key(request):
    data_key_kwarg = {
        "load_from" if (MARSHMALLOW_VERSION_INFO[0] < 3) else "data_key": "X-Field"
    }
    args = {"x_field": fields.Nested({"id": fields.Int()}, many=True, **data_key_kwarg)}
    parsed = await parser.parse(args, request)
    return J(parsed)


class EchoMethodViewUseArgs(HTTPMethodView):
    @use_args({"val": fields.Int()})
    async def post(self, request, args):
        return J(args)

app.add_route(EchoMethodViewUseArgs.as_view(), '/echo_method_view_use_args')



class EchoMethodViewUseKwargs(HTTPMethodView):
    @use_kwargs({"val": fields.Int()})
    async def post(self, request, val):
        return J({"val": val})

app.add_route(EchoMethodViewUseKwargs.as_view(), '/echo_method_view_use_kwargs')


@app.route("/echo_use_kwargs_missing", methods=["POST"])
@use_kwargs({"username": fields.Str(), "password": fields.Str()})
async def echo_use_kwargs_missing(request, username, password):
    assert password is missing
    return J({"username": username})

# Return validation errors as JSON
@app.exception(HandleValidationError)
async def handle_validation_error(request, err):
    assert isinstance(err.data["schema"], ma.Schema)
    return J({"errors": err.exc.messages}, status=422)
