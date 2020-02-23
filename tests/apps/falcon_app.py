import falcon
import marshmallow as ma

from webargs import fields
from webargs.core import MARSHMALLOW_VERSION_INFO, json
from webargs.falconparser import parser, use_args, use_kwargs

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


class Echo:
    def on_get(self, req, resp):
        parsed = parser.parse(hello_args, req, location="query")
        resp.body = json.dumps(parsed)


class EchoForm:
    def on_post(self, req, resp):
        parsed = parser.parse(hello_args, req, location="form")
        resp.body = json.dumps(parsed)


class EchoJSON:
    def on_post(self, req, resp):
        parsed = parser.parse(hello_args, req, location="json")
        resp.body = json.dumps(parsed)


class EchoJSONOrForm:
    def on_post(self, req, resp):
        parsed = parser.parse(hello_args, req, location="json_or_form")
        resp.body = json.dumps(parsed)


class EchoUseArgs:
    @use_args(hello_args, location="query")
    def on_get(self, req, resp, args):
        resp.body = json.dumps(args)


class EchoUseKwargs:
    @use_kwargs(hello_args, location="query")
    def on_get(self, req, resp, name):
        resp.body = json.dumps({"name": name})


class EchoUseArgsValidated:
    @use_args(
        {"value": fields.Int()},
        validate=lambda args: args["value"] > 42,
        location="form",
    )
    def on_post(self, req, resp, args):
        resp.body = json.dumps(args)


class EchoJSONIgnoreExtraData:
    def on_post(self, req, resp):
        resp.body = json.dumps(parser.parse(hello_exclude_schema, req))


class EchoMulti:
    def on_get(self, req, resp):
        resp.body = json.dumps(parser.parse(hello_multiple, req, location="query"))


class EchoMultiForm:
    def on_post(self, req, resp):
        resp.body = json.dumps(parser.parse(hello_multiple, req, location="form"))


class EchoMultiJSON:
    def on_post(self, req, resp):
        resp.body = json.dumps(parser.parse(hello_multiple, req))


class EchoManySchema:
    def on_post(self, req, resp):
        resp.body = json.dumps(parser.parse(hello_many_schema, req))


class EchoUseArgsWithPathParam:
    @use_args({"value": fields.Int()}, location="query")
    def on_get(self, req, resp, args, name):
        resp.body = json.dumps(args)


class EchoUseKwargsWithPathParam:
    @use_kwargs({"value": fields.Int()}, location="query")
    def on_get(self, req, resp, value, name):
        resp.body = json.dumps({"value": value})


class AlwaysError:
    def on_get(self, req, resp):
        def always_fail(value):
            raise ma.ValidationError("something went wrong")

        args = {"text": fields.Str(validate=always_fail)}
        resp.body = json.dumps(parser.parse(args, req))

    on_post = on_get


class EchoHeaders:
    def on_get(self, req, resp):
        class HeaderSchema(ma.Schema):
            NAME = fields.Str(missing="World")

        resp.body = json.dumps(
            parser.parse(HeaderSchema(**exclude_kwargs), req, location="headers")
        )


class EchoCookie:
    def on_get(self, req, resp):
        resp.body = json.dumps(parser.parse(hello_args, req, location="cookies"))


class EchoNested:
    def on_post(self, req, resp):
        args = {"name": fields.Nested({"first": fields.Str(), "last": fields.Str()})}
        resp.body = json.dumps(parser.parse(args, req))


class EchoNestedMany:
    def on_post(self, req, resp):
        args = {
            "users": fields.Nested(
                {"id": fields.Int(), "name": fields.Str()}, many=True
            )
        }
        resp.body = json.dumps(parser.parse(args, req))


def use_args_hook(args, context_key="args", **kwargs):
    def hook(req, resp, resource, params):
        parsed_args = parser.parse(args, req=req, **kwargs)
        req.context[context_key] = parsed_args

    return hook


@falcon.before(use_args_hook(hello_args, location="query"))
class EchoUseArgsHook:
    def on_get(self, req, resp):
        resp.body = json.dumps(req.context["args"])


def create_app():
    app = falcon.API()
    app.add_route("/echo", Echo())
    app.add_route("/echo_form", EchoForm())
    app.add_route("/echo_json", EchoJSON())
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
