import json

import falcon
import marshmallow as ma
from webargs import fields, ValidationError
from webargs.falconparser import parser, use_args, use_kwargs

hello_args = {
    'name': fields.Str(missing='World', validate=lambda n: len(n) >= 3),
}
hello_multiple = {
    'name': fields.List(fields.Str())
}

class HelloSchema(ma.Schema):
    name = fields.Str(missing='World', validate=lambda n: len(n) >= 3)

hello_many_schema = HelloSchema(strict=True, many=True)

class Echo(object):
    def on_get(self, req, resp):
        parsed = parser.parse(hello_args, req)
        resp.body = json.dumps(parsed)

    on_post = on_get

class EchoQuery(object):
    def on_get(self, req, resp):
        parsed = parser.parse(hello_args, req, locations=('query', ))
        resp.body = json.dumps(parsed)


class EchoUseArgs(object):
    @use_args(hello_args)
    def on_get(self, req, resp, args):
        resp.body = json.dumps(args)

    on_post = on_get


class EchoUseKwargs(object):
    @use_kwargs(hello_args)
    def on_get(self, req, resp, name):
        resp.body = json.dumps({'name': name})

    on_post = on_get

class EchoUseArgsValidated(object):
    @use_args({'value': fields.Int()}, validate=lambda args: args['value'] > 42)
    def on_get(self, req, resp, args):
        resp.body = json.dumps(args)

    on_post = on_get

class EchoMulti(object):
    def on_get(self, req, resp):
        resp.body = json.dumps(parser.parse(hello_multiple, req))

    on_post = on_get

class EchoManySchema(object):
    def on_get(self, req, resp):
        resp.body = json.dumps(parser.parse(hello_many_schema, req, locations=('json', )))

    on_post = on_get

class EchoUseArgsWithPathParam(object):
    @use_args({'value': fields.Int()})
    def on_get(self, req, resp, args, name):
        resp.body = json.dumps(args)

class EchoUseKwargsWithPathParam(object):
    @use_kwargs({'value': fields.Int()})
    def on_get(self, req, resp, value, name):
        resp.body = json.dumps({'value': value})


class AlwaysError(object):
    def on_get(self, req, resp):
        def always_fail(value):
            raise ValidationError('something went wrong')
        args = {'text': fields.Str(validate=always_fail)}
        resp.body = json.dumps(parser.parse(args, req))
    on_post = on_get

class Error400(object):
    def on_get(self, req, resp):
        def always_fail(value):
            raise ValidationError('something went wrong', status_code=400)
        args = {'text': fields.Str(validate=always_fail)}
        resp.body = json.dumps(parser.parse(args, req))
    on_post = on_get

class ErrorInvalid(object):
    def on_get(self, req, resp):
        def always_fail(value):
            raise ValidationError('something went wrong', status_code=12345)
        args = {'text': fields.Str(validate=always_fail)}
        resp.body = json.dumps(parser.parse(args, req))

class EchoHeaders(object):
    def on_get(self, req, resp):
        resp.body = json.dumps(parser.parse(hello_args, req, locations=('headers', )))

class EchoCookie(object):
    def on_get(self, req, resp):
        resp.body = json.dumps(parser.parse(hello_args, req, locations=('cookies', )))


class EchoNested(object):
    def on_post(self, req, resp):
        args = {
            'name': fields.Nested({'first': fields.Str(),
                'last': fields.Str()})
        }
        resp.body = json.dumps(parser.parse(args, req))

class EchoNestedMany(object):
    def on_post(self, req, resp):
        args = {
            'users': fields.Nested({'id': fields.Int(), 'name': fields.Str()}, many=True)
        }
        resp.body = json.dumps(parser.parse(args, req))

def use_args_hook(args, context_key='args', **kwargs):
    def hook(req, resp, params):
        parsed_args = parser.parse(args, req=req, **kwargs)
        req.context[context_key] = parsed_args
    return hook

@falcon.before(use_args_hook(hello_args))
class EchoUseArgsHook(object):
    def on_get(self, req, resp):
        resp.body = json.dumps(req.context['args'])

def create_app():
    app = falcon.API()
    app.add_route('/echo', Echo())
    app.add_route('/echo_query', EchoQuery())
    app.add_route('/echo_use_args', EchoUseArgs())
    app.add_route('/echo_use_kwargs', EchoUseKwargs())
    app.add_route('/echo_use_args_validated', EchoUseArgsValidated())
    app.add_route('/echo_multi', EchoMulti())
    app.add_route('/echo_many_schema', EchoManySchema())
    app.add_route('/echo_use_args_with_path_param/{name}', EchoUseArgsWithPathParam())
    app.add_route('/echo_use_kwargs_with_path_param/{name}', EchoUseKwargsWithPathParam())
    app.add_route('/error', AlwaysError())
    app.add_route('/error400', Error400())
    app.add_route('/echo_headers', EchoHeaders())
    app.add_route('/echo_cookie', EchoCookie())
    app.add_route('/echo_nested', EchoNested())
    app.add_route('/echo_nested_many', EchoNestedMany())
    app.add_route('/echo_use_args_hook', EchoUseArgsHook())
    app.add_route('/error_invalid', ErrorInvalid())
    return app
