import importlib.metadata

import falcon
import marshmallow as ma

from webargs import fields, validate
from webargs.core import json
from webargs.falconparser import parser, use_args, use_kwargs

hello_args = {"name": fields.Str(load_default="World", validate=validate.Length(min=3))}
hello_multiple = {"name": fields.List(fields.Str())}

FALCON_MAJOR_VERSION = int(importlib.metadata.version("falcon").split(".")[0])
FALCON_SUPPORTS_ASYNC = FALCON_MAJOR_VERSION >= 3


class HelloSchema(ma.Schema):
    name = fields.Str(load_default="World", validate=validate.Length(min=3))


hello_many_schema = HelloSchema(many=True)

# variant which ignores unknown fields
hello_exclude_schema = HelloSchema(unknown=ma.EXCLUDE)


def set_text(resp, value):
    if FALCON_MAJOR_VERSION >= 3:
        resp.text = value
    else:
        resp.body = value


class Echo:
    def on_get(self, req, resp):
        parsed = parser.parse(hello_args, req, location="query")
        set_text(resp, json.dumps(parsed))


class AsyncEcho:
    async def on_get(self, req, resp):
        parsed = await parser.async_parse(hello_args, req, location="query")
        set_text(resp, json.dumps(parsed))


class EchoForm:
    def on_post(self, req, resp):
        parsed = parser.parse(hello_args, req, location="form")
        set_text(resp, json.dumps(parsed))


class EchoJSON:
    def on_post(self, req, resp):
        parsed = parser.parse(hello_args, req, location="json")
        set_text(resp, json.dumps(parsed))


class EchoMedia:
    def on_post(self, req, resp):
        parsed = parser.parse(hello_args, req, location="media")
        set_text(resp, json.dumps(parsed))


class EchoJSONOrForm:
    def on_post(self, req, resp):
        parsed = parser.parse(hello_args, req, location="json_or_form")
        set_text(resp, json.dumps(parsed))


class EchoUseArgs:
    @use_args(hello_args, location="query")
    def on_get(self, req, resp, args):
        set_text(resp, json.dumps(args))


class AsyncEchoUseArgs:
    @use_args(hello_args, location="query")
    async def on_get(self, req, resp, args):
        set_text(resp, json.dumps(args))


class EchoUseKwargs:
    @use_kwargs(hello_args, location="query")
    def on_get(self, req, resp, name):
        set_text(resp, json.dumps({"name": name}))


class EchoUseArgsValidated:
    @use_args(
        {"value": fields.Int()},
        validate=lambda args: args["value"] > 42,
        location="form",
    )
    def on_post(self, req, resp, args):
        set_text(resp, json.dumps(args))


class EchoJSONIgnoreExtraData:
    def on_post(self, req, resp):
        set_text(
            resp, json.dumps(parser.parse(hello_exclude_schema, req, unknown=None))
        )


class EchoMulti:
    def on_get(self, req, resp):
        set_text(resp, json.dumps(parser.parse(hello_multiple, req, location="query")))


class EchoMultiForm:
    def on_post(self, req, resp):
        set_text(resp, json.dumps(parser.parse(hello_multiple, req, location="form")))


class EchoMultiJSON:
    def on_post(self, req, resp):
        set_text(resp, json.dumps(parser.parse(hello_multiple, req)))


class EchoManySchema:
    def on_post(self, req, resp):
        set_text(resp, json.dumps(parser.parse(hello_many_schema, req)))


class EchoUseArgsWithPathParam:
    @use_args({"value": fields.Int()}, location="query")
    def on_get(self, req, resp, args, name):
        set_text(resp, json.dumps(args))


class EchoUseKwargsWithPathParam:
    @use_kwargs({"value": fields.Int()}, location="query")
    def on_get(self, req, resp, value, name):
        set_text(resp, json.dumps({"value": value}))


class AlwaysError:
    def on_get(self, req, resp):
        def always_fail(value):
            raise ma.ValidationError("something went wrong")

        args = {"text": fields.Str(validate=always_fail)}
        set_text(resp, json.dumps(parser.parse(args, req)))

    on_post = on_get


class EchoHeaders:
    def on_get(self, req, resp):
        class HeaderSchema(ma.Schema):
            NAME = fields.Str(load_default="World")

        set_text(
            resp, json.dumps(parser.parse(HeaderSchema(), req, location="headers"))
        )


class EchoCookie:
    def on_get(self, req, resp):
        set_text(resp, json.dumps(parser.parse(hello_args, req, location="cookies")))


class EchoNested:
    def on_post(self, req, resp):
        args = {"name": fields.Nested({"first": fields.Str(), "last": fields.Str()})}
        set_text(resp, json.dumps(parser.parse(args, req)))


class EchoNestedMany:
    def on_post(self, req, resp):
        args = {
            "users": fields.Nested(
                {"id": fields.Int(), "name": fields.Str()}, many=True
            )
        }
        set_text(resp, json.dumps(parser.parse(args, req)))


def use_args_hook(args, context_key="args", **kwargs):
    def hook(req, resp, resource, params):
        parsed_args = parser.parse(args, req=req, **kwargs)
        req.context[context_key] = parsed_args

    return hook


@falcon.before(use_args_hook(hello_args, location="query"))
class EchoUseArgsHook:
    def on_get(self, req, resp):
        set_text(resp, json.dumps(req.context["args"]))


def create_app():
    if FALCON_MAJOR_VERSION >= 3:
        app = falcon.App()
    else:
        app = falcon.API()

    app.add_route("/echo", Echo())
    app.add_route("/echo_form", EchoForm())
    app.add_route("/echo_json", EchoJSON())
    app.add_route("/echo_media", EchoMedia())
    app.add_route("/echo_json_or_form", EchoJSONOrForm())
    app.add_route("/echo_use_args", EchoUseArgs())
    app.add_route("/echo_use_kwargs", EchoUseKwargs())
    app.add_route("/echo_use_args_validated", EchoUseArgsValidated())
    app.add_route("/echo_ignoring_extra_data", EchoJSONIgnoreExtraData())
    app.add_route("/echo_multi", EchoMulti())
    app.add_route("/echo_multi_form", EchoMultiForm())
    app.add_route("/echo_multi_json", EchoMultiJSON())
    app.add_route("/echo_many_schema", EchoManySchema())
    app.add_route("/echo_use_args_with_path_param/{name}", EchoUseArgsWithPathParam())
    app.add_route(
        "/echo_use_kwargs_with_path_param/{name}", EchoUseKwargsWithPathParam()
    )
    app.add_route("/error", AlwaysError())
    app.add_route("/echo_headers", EchoHeaders())
    app.add_route("/echo_cookie", EchoCookie())
    app.add_route("/echo_nested", EchoNested())
    app.add_route("/echo_nested_many", EchoNestedMany())
    app.add_route("/echo_use_args_hook", EchoUseArgsHook())
    return app


def create_async_app():
    # defer import (async-capable versions only)
    import falcon.asgi

    app = falcon.asgi.App()
    app.add_route("/async_echo", AsyncEcho())
    app.add_route("/async_echo_use_args", AsyncEchoUseArgs())
    return app
