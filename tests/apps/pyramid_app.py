from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPBadRequest
import marshmallow as ma

from webargs import fields
from webargs.pyramidparser import parser, use_args, use_kwargs
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


def echo(request):
    return parser.parse(hello_args, request, location="query")


def echo_form(request):
    return parser.parse(hello_args, request, location="form")


def echo_json(request):
    try:
        return parser.parse(hello_args, request, location="json")
    except json.JSONDecodeError:
        error = HTTPBadRequest()
        error.body = json.dumps(["Invalid JSON."]).encode("utf-8")
        error.content_type = "application/json"
        raise error


def echo_json_or_form(request):
    try:
        return parser.parse(hello_args, request, location="json_or_form")
    except json.JSONDecodeError:
        error = HTTPBadRequest()
        error.body = json.dumps(["Invalid JSON."]).encode("utf-8")
        error.content_type = "application/json"
        raise error


def echo_json_ignore_extra_data(request):
    try:
        return parser.parse(hello_exclude_schema, request)
    except json.JSONDecodeError:
        error = HTTPBadRequest()
        error.body = json.dumps(["Invalid JSON."]).encode("utf-8")
        error.content_type = "application/json"
        raise error


def echo_query(request):
    return parser.parse(hello_args, request, location="query")


@use_args(hello_args, location="query")
def echo_use_args(request, args):
    return args


@use_args(
    {"value": fields.Int()}, validate=lambda args: args["value"] > 42, location="form"
)
def echo_use_args_validated(request, args):
    return args


@use_kwargs(hello_args, location="query")
def echo_use_kwargs(request, name):
    return {"name": name}


def echo_multi(request):
    return parser.parse(hello_multiple, request, location="query")


def echo_multi_form(request):
    return parser.parse(hello_multiple, request, location="form")


def echo_multi_json(request):
    return parser.parse(hello_multiple, request)


def echo_many_schema(request):
    return parser.parse(hello_many_schema, request)


@use_args({"value": fields.Int()}, location="query")
def echo_use_args_with_path_param(request, args):
    return args


@use_kwargs({"value": fields.Int()}, location="query")
def echo_use_kwargs_with_path_param(request, value):
    return {"value": value}


def always_error(request):
    def always_fail(value):
        raise ma.ValidationError("something went wrong")

    argmap = {"text": fields.Str(validate=always_fail)}
    return parser.parse(argmap, request)


def echo_headers(request):
    return parser.parse(hello_exclude_schema, request, location="headers")


def echo_cookie(request):
    return parser.parse(hello_args, request, location="cookies")


def echo_file(request):
    args = {"myfile": fields.Field()}
    result = parser.parse(args, request, location="files")
    myfile = result["myfile"]
    content = myfile.file.read().decode("utf8")
    return {"myfile": content}


def echo_nested(request):
    argmap = {"name": fields.Nested({"first": fields.Str(), "last": fields.Str()})}
    return parser.parse(argmap, request)


def echo_nested_many(request):
    argmap = {
        "users": fields.Nested({"id": fields.Int(), "name": fields.Str()}, many=True)
    }
    return parser.parse(argmap, request)


def echo_matchdict(request):
    return parser.parse({"mymatch": fields.Int()}, request, location="matchdict")


class EchoCallable:
    def __init__(self, request):
        self.request = request

    @use_args({"value": fields.Int()}, location="query")
    def __call__(self, args):
        return args


def add_route(config, route, view, route_name=None, renderer="json"):
    """Helper for adding a new route-view pair."""
    route_name = route_name or view.__name__
    config.add_route(route_name, route)
    config.add_view(view, route_name=route_name, renderer=renderer)


def create_app():
    config = Configurator()

    add_route(config, "/echo", echo)
    add_route(config, "/echo_form", echo_form)
    add_route(config, "/echo_json", echo_json)
    add_route(config, "/echo_json_or_form", echo_json_or_form)
    add_route(config, "/echo_query", echo_query)
    add_route(config, "/echo_ignoring_extra_data", echo_json_ignore_extra_data)
    add_route(config, "/echo_use_args", echo_use_args)
    add_route(config, "/echo_use_args_validated", echo_use_args_validated)
    add_route(config, "/echo_use_kwargs", echo_use_kwargs)
    add_route(config, "/echo_multi", echo_multi)
    add_route(config, "/echo_multi_form", echo_multi_form)
    add_route(config, "/echo_multi_json", echo_multi_json)
    add_route(config, "/echo_many_schema", echo_many_schema)
    add_route(
        config, "/echo_use_args_with_path_param/{name}", echo_use_args_with_path_param
    )
    add_route(
        config,
        "/echo_use_kwargs_with_path_param/{name}",
        echo_use_kwargs_with_path_param,
    )
    add_route(config, "/error", always_error)
    add_route(config, "/echo_headers", echo_headers)
    add_route(config, "/echo_cookie", echo_cookie)
    add_route(config, "/echo_file", echo_file)
    add_route(config, "/echo_nested", echo_nested)
    add_route(config, "/echo_nested_many", echo_nested_many)
    add_route(config, "/echo_callable", EchoCallable)
    add_route(config, "/echo_matchdict/{mymatch}", echo_matchdict)

    return config.make_wsgi_app()
