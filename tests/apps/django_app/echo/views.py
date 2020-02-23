from django.http import HttpResponse
from django.views.generic import View
import marshmallow as ma

from webargs import fields
from webargs.djangoparser import parser, use_args, use_kwargs
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


def json_response(data, **kwargs):
    return HttpResponse(json.dumps(data), content_type="application/json", **kwargs)


def handle_view_errors(f):
    def wrapped(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ma.ValidationError as err:
            return json_response(err.messages, status=422)
        except json.JSONDecodeError:
            return json_response({"json": ["Invalid JSON body."]}, status=400)

    return wrapped


@handle_view_errors
def echo(request):
    return json_response(parser.parse(hello_args, request, location="query"))


@handle_view_errors
def echo_form(request):
    return json_response(parser.parse(hello_args, request, location="form"))


@handle_view_errors
def echo_json(request):
    return json_response(parser.parse(hello_args, request, location="json"))


@handle_view_errors
def echo_json_or_form(request):
    return json_response(parser.parse(hello_args, request, location="json_or_form"))


@handle_view_errors
@use_args(hello_args, location="query")
def echo_use_args(request, args):
    return json_response(args)


@handle_view_errors
@use_args(
    {"value": fields.Int()}, validate=lambda args: args["value"] > 42, location="form"
)
def echo_use_args_validated(args):
    return json_response(args)


@handle_view_errors
def echo_ignoring_extra_data(request):
    return json_response(parser.parse(hello_exclude_schema, request))


@handle_view_errors
@use_kwargs(hello_args, location="query")
def echo_use_kwargs(request, name):
    return json_response({"name": name})


@handle_view_errors
def echo_multi(request):
    return json_response(parser.parse(hello_multiple, request, location="query"))


@handle_view_errors
def echo_multi_form(request):
    return json_response(parser.parse(hello_multiple, request, location="form"))


@handle_view_errors
def echo_multi_json(request):
    return json_response(parser.parse(hello_multiple, request))


@handle_view_errors
def echo_many_schema(request):
    return json_response(parser.parse(hello_many_schema, request))


@handle_view_errors
@use_args({"value": fields.Int()}, location="query")
def echo_use_args_with_path_param(request, args, name):
    return json_response(args)


@handle_view_errors
@use_kwargs({"value": fields.Int()}, location="query")
def echo_use_kwargs_with_path_param(request, value, name):
    return json_response({"value": value})


@handle_view_errors
def always_error(request):
    def always_fail(value):
        raise ma.ValidationError("something went wrong")

    argmap = {"text": fields.Str(validate=always_fail)}
    return parser.parse(argmap, request)


@handle_view_errors
def echo_headers(request):
    return json_response(
        parser.parse(hello_exclude_schema, request, location="headers")
    )


@handle_view_errors
def echo_cookie(request):
    return json_response(parser.parse(hello_args, request, location="cookies"))


@handle_view_errors
def echo_file(request):
    args = {"myfile": fields.Field()}
    result = parser.parse(args, request, location="files")
    myfile = result["myfile"]
    content = myfile.read().decode("utf8")
    return json_response({"myfile": content})


@handle_view_errors
def echo_nested(request):
    argmap = {"name": fields.Nested({"first": fields.Str(), "last": fields.Str()})}
    return json_response(parser.parse(argmap, request))


@handle_view_errors
def echo_nested_many(request):
    argmap = {
        "users": fields.Nested({"id": fields.Int(), "name": fields.Str()}, many=True)
    }
    return json_response(parser.parse(argmap, request))


class EchoCBV(View):
    @handle_view_errors
    def get(self, request):
        location_kwarg = {} if request.method == "POST" else {"location": "query"}
        return json_response(parser.parse(hello_args, self.request, **location_kwarg))

    post = get


class EchoUseArgsCBV(View):
    @handle_view_errors
    @use_args(hello_args, location="query")
    def get(self, request, args):
        return json_response(args)

    @handle_view_errors
    @use_args(hello_args)
    def post(self, request, args):
        return json_response(args)


class EchoUseArgsWithParamCBV(View):
    @handle_view_errors
    @use_args(hello_args, location="query")
    def get(self, request, args, pid):
        return json_response(args)

    @handle_view_errors
    @use_args(hello_args)
    def post(self, request, args, pid):
        return json_response(args)
