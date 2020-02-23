import asyncio

import aiohttp
from aiohttp.web import json_response
import marshmallow as ma

from webargs import fields
from webargs.aiohttpparser import parser, use_args, use_kwargs
from webargs.core import MARSHMALLOW_VERSION_INFO, json

hello_args = {"name": fields.Str(missing="World", validate=lambda n: len(n) >= 3)}
hello_multiple = {"name": fields.List(fields.Str())}


class HelloSchema(ma.Schema):
    name = fields.Str(missing="World", validate=lambda n: len(n) >= 3)

    if MARSHMALLOW_VERSION_INFO[0] < 3:

        class Meta:
            strict = True


strict_kwargs = {"strict": True} if MARSHMALLOW_VERSION_INFO[0] < 3 else {}
hello_many_schema = HelloSchema(many=True, **strict_kwargs)

# variant which ignores unknown fields
exclude_kwargs = (
    {"strict": True} if MARSHMALLOW_VERSION_INFO[0] < 3 else {"unknown": ma.EXCLUDE}
)
hello_exclude_schema = HelloSchema(**exclude_kwargs)


##### Handlers #####


async def echo(request):
    parsed = await parser.parse(hello_args, request, location="query")
    return json_response(parsed)


async def echo_form(request):
    parsed = await parser.parse(hello_args, request, location="form")
    return json_response(parsed)


async def echo_json(request):
    try:
        parsed = await parser.parse(hello_args, request, location="json")
    except json.JSONDecodeError:
        raise aiohttp.web.HTTPBadRequest(
            body=json.dumps(["Invalid JSON."]).encode("utf-8"),
            content_type="application/json",
        )
    return json_response(parsed)


async def echo_json_or_form(request):
    try:
        parsed = await parser.parse(hello_args, request, location="json_or_form")
    except json.JSONDecodeError:
        raise aiohttp.web.HTTPBadRequest(
            body=json.dumps(["Invalid JSON."]).encode("utf-8"),
            content_type="application/json",
        )
    return json_response(parsed)


@use_args(hello_args, location="query")
async def echo_use_args(request, args):
    return json_response(args)


@use_kwargs(hello_args, location="query")
async def echo_use_kwargs(request, name):
    return json_response({"name": name})


@use_args(
    {"value": fields.Int()}, validate=lambda args: args["value"] > 42, location="form"
)
async def echo_use_args_validated(request, args):
    return json_response(args)


async def echo_ignoring_extra_data(request):
    return json_response(await parser.parse(hello_exclude_schema, request))


async def echo_multi(request):
    parsed = await parser.parse(hello_multiple, request, location="query")
    return json_response(parsed)


async def echo_multi_form(request):
    parsed = await parser.parse(hello_multiple, request, location="form")
    return json_response(parsed)


async def echo_multi_json(request):
    parsed = await parser.parse(hello_multiple, request)
    return json_response(parsed)


async def echo_many_schema(request):
    parsed = await parser.parse(hello_many_schema, request)
    return json_response(parsed)


@use_args({"value": fields.Int()}, location="query")
async def echo_use_args_with_path_param(request, args):
    return json_response(args)


@use_kwargs({"value": fields.Int()}, location="query")
async def echo_use_kwargs_with_path_param(request, value):
    return json_response({"value": value})


@use_args({"page": fields.Int(), "q": fields.Int()}, location="query")
@use_args({"name": fields.Str()})
async def echo_use_args_multiple(request, query_parsed, json_parsed):
    return json_response({"query_parsed": query_parsed, "json_parsed": json_parsed})


async def always_error(request):
    def always_fail(value):
        raise ma.ValidationError("something went wrong")

    args = {"text": fields.Str(validate=always_fail)}
    parsed = await parser.parse(args, request)
    return json_response(parsed)


async def echo_headers(request):
    parsed = await parser.parse(hello_exclude_schema, request, location="headers")
    return json_response(parsed)


async def echo_cookie(request):
    parsed = await parser.parse(hello_args, request, location="cookies")
    return json_response(parsed)


async def echo_nested(request):
    args = {"name": fields.Nested({"first": fields.Str(), "last": fields.Str()})}
    parsed = await parser.parse(args, request)
    return json_response(parsed)


async def echo_multiple_args(request):
    args = {"first": fields.Str(), "last": fields.Str()}
    parsed = await parser.parse(args, request)
    return json_response(parsed)


async def echo_nested_many(request):
    args = {
        "users": fields.Nested({"id": fields.Int(), "name": fields.Str()}, many=True)
    }
    parsed = await parser.parse(args, request)
    return json_response(parsed)


async def echo_nested_many_data_key(request):
    data_key_kwarg = {
        "load_from" if (MARSHMALLOW_VERSION_INFO[0] < 3) else "data_key": "X-Field"
    }
    args = {"x_field": fields.Nested({"id": fields.Int()}, many=True, **data_key_kwarg)}
    parsed = await parser.parse(args, request)
    return json_response(parsed)


async def echo_match_info(request):
    parsed = await parser.parse(
        {"mymatch": fields.Int()}, request, location="match_info"
    )
    return json_response(parsed)


class EchoHandler:
    @use_args(hello_args, location="query")
    async def get(self, request, args):
        return json_response(args)


class EchoHandlerView(aiohttp.web.View):
    @asyncio.coroutine
    @use_args(hello_args, location="query")
    def get(self, args):
        return json_response(args)


@asyncio.coroutine
@use_args(HelloSchema, as_kwargs=True, location="query")
def echo_use_schema_as_kwargs(request, name):
    return json_response({"name": name})


##### App factory #####


def add_route(app, methods, route, handler):
    for method in methods:
        app.router.add_route(method, route, handler)


def create_app():
    app = aiohttp.web.Application()

    add_route(app, ["GET"], "/echo", echo)
    add_route(app, ["POST"], "/echo_form", echo_form)
    add_route(app, ["POST"], "/echo_json", echo_json)
    add_route(app, ["POST"], "/echo_json_or_form", echo_json_or_form)
    add_route(app, ["GET"], "/echo_use_args", echo_use_args)
    add_route(app, ["GET"], "/echo_use_kwargs", echo_use_kwargs)
    add_route(app, ["POST"], "/echo_use_args_validated", echo_use_args_validated)
    add_route(app, ["POST"], "/echo_ignoring_extra_data", echo_ignoring_extra_data)
    add_route(app, ["GET"], "/echo_multi", echo_multi)
    add_route(app, ["POST"], "/echo_multi_form", echo_multi_form)
    add_route(app, ["POST"], "/echo_multi_json", echo_multi_json)
    add_route(app, ["GET", "POST"], "/echo_many_schema", echo_many_schema)
    add_route(
        app,
        ["GET", "POST"],
        "/echo_use_args_with_path_param/{name}",
        echo_use_args_with_path_param,
    )
    add_route(
        app,
        ["GET", "POST"],
        "/echo_use_kwargs_with_path_param/{name}",
        echo_use_kwargs_with_path_param,
    )
    add_route(app, ["POST"], "/echo_use_args_multiple", echo_use_args_multiple)
    add_route(app, ["GET", "POST"], "/error", always_error)
    add_route(app, ["GET"], "/echo_headers", echo_headers)
    add_route(app, ["GET"], "/echo_cookie", echo_cookie)
    add_route(app, ["POST"], "/echo_nested", echo_nested)
    add_route(app, ["POST"], "/echo_multiple_args", echo_multiple_args)
    add_route(app, ["POST"], "/echo_nested_many", echo_nested_many)
    add_route(app, ["POST"], "/echo_nested_many_data_key", echo_nested_many_data_key)
    add_route(app, ["GET"], "/echo_match_info/{mymatch}", echo_match_info)
    add_route(app, ["GET"], "/echo_method", EchoHandler().get)
    add_route(app, ["GET"], "/echo_method_view", EchoHandlerView)
    add_route(app, ["GET"], "/echo_use_schema_as_kwargs", echo_use_schema_as_kwargs)
    return app
