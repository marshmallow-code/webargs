import asyncio

import aiohttp
from aiohttp.web import json_response
import marshmallow as ma

from webargs import fields, ValidationError
from webargs.aiohttpparser import parser, use_args, use_kwargs

hello_args = {
    'name': fields.Str(missing='World', validate=lambda n: len(n) >= 3),
}
hello_multiple = {
    'name': fields.List(fields.Str())
}

class HelloSchema(ma.Schema):
    name = fields.Str(missing='World', validate=lambda n: len(n) >= 3)

hello_many_schema = HelloSchema(strict=True, many=True)

##### Handlers #####

@asyncio.coroutine
def echo(request):
    parsed = yield from parser.parse(hello_args, request)
    return json_response(parsed)

@asyncio.coroutine
def echo_query(request):
    parsed = yield from parser.parse(hello_args, request, locations=('query', ))
    return json_response(parsed)

@asyncio.coroutine
@use_args(hello_args)
def echo_use_args(request, args):
    return json_response(args)

@asyncio.coroutine
@use_kwargs(hello_args)
def echo_use_kwargs(request, name):
    return json_response({'name': name})

@asyncio.coroutine
@use_args({'value': fields.Int()}, validate=lambda args: args['value'] > 42)
def echo_use_args_validated(request, args):
    return json_response(args)

@asyncio.coroutine
def echo_multi(request):
    parsed = yield from parser.parse(hello_multiple, request)
    return json_response(parsed)

@asyncio.coroutine
def echo_many_schema(request):
    parsed = yield from parser.parse(hello_many_schema, request, locations=('json', ))
    return json_response(parsed)

@asyncio.coroutine
@use_args({'value': fields.Int()})
def echo_use_args_with_path_param(request, args):
    return json_response(args)

@asyncio.coroutine
@use_kwargs({'value': fields.Int()})
def echo_use_kwargs_with_path_param(request, value):
    return json_response({'value': value})

@asyncio.coroutine
def always_error(request):
    def always_fail(value):
        raise ValidationError('something went wrong')
    args = {'text': fields.Str(validate=always_fail)}
    parsed = yield from parser.parse(args, request)
    return json_response(parsed)

@asyncio.coroutine
def error400(request):
    def always_fail(value):
        raise ValidationError('something went wrong', status_code=400)
    args = {'text': fields.Str(validate=always_fail)}
    parsed = yield from parser.parse(args, request)
    return json_response(parsed)

@asyncio.coroutine
def error_invalid(request):
    def always_fail(value):
        raise ValidationError('something went wrong', status_code=12345)
    args = {'text': fields.Str(validate=always_fail)}
    parsed = yield from parser.parse(args, request)
    return json_response(parsed)

@asyncio.coroutine
def echo_headers(request):
    parsed = yield from parser.parse(hello_args, request, locations=('headers', ))
    return json_response(parsed)

@asyncio.coroutine
def echo_cookie(request):
    parsed = yield from parser.parse(hello_args, request, locations=('cookies', ))
    return json_response(parsed)

@asyncio.coroutine
def echo_nested(request):
    args = {
        'name': fields.Nested({'first': fields.Str(),
                     'last': fields.Str()})
    }
    parsed = yield from parser.parse(args, request)
    return json_response(parsed)

@asyncio.coroutine
def echo_nested_many(request):
    args = {
        'users': fields.Nested({'id': fields.Int(), 'name': fields.Str()}, many=True)
    }
    parsed = yield from parser.parse(args, request)
    return json_response(parsed)

@asyncio.coroutine
def echo_nested_many_load_from(request):
    args = {
        'x_field': fields.Nested({'id': fields.Int()}, load_from='X-Field', many=True)
    }
    parsed = yield from parser.parse(args, request)
    return json_response(parsed)

@asyncio.coroutine
def echo_match_info(request):
    parsed = yield from parser.parse({'mymatch': fields.Int(location='match_info')}, request)
    return json_response(parsed)

class EchoHandler:

    @asyncio.coroutine
    @use_args(hello_args)
    def get(self, request, args):
        return json_response(args)

##### App factory #####

def add_route(app, methods, route, handler):
    for method in methods:
        app.router.add_route(method, route, handler)

def create_app():
    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(loop)
    app = aiohttp.web.Application(loop=loop)

    add_route(app, ['GET', 'POST'], '/echo', echo)
    add_route(app, ['GET'], '/echo_query', echo_query)
    add_route(app, ['GET', 'POST'], '/echo_use_args', echo_use_args)
    add_route(app, ['GET', 'POST'], '/echo_use_kwargs', echo_use_kwargs)
    add_route(app, ['GET', 'POST'], '/echo_use_args_validated', echo_use_args_validated)
    add_route(app, ['GET', 'POST'], '/echo_multi', echo_multi)
    add_route(app, ['GET', 'POST'], '/echo_many_schema', echo_many_schema)
    add_route(app, ['GET', 'POST'], '/echo_use_args_with_path_param/{name}',
              echo_use_args_with_path_param)
    add_route(app, ['GET', 'POST'], '/echo_use_kwargs_with_path_param/{name}',
              echo_use_kwargs_with_path_param)
    add_route(app, ['GET', 'POST'], '/error', always_error)
    add_route(app, ['GET', 'POST'], '/error400', error400)
    add_route(app, ['GET'], '/error_invalid', error_invalid)
    add_route(app, ['GET'], '/echo_headers', echo_headers)
    add_route(app, ['GET'], '/echo_cookie', echo_cookie)
    add_route(app, ['POST'], '/echo_nested', echo_nested)
    add_route(app, ['POST'], '/echo_nested_many', echo_nested_many)
    add_route(app, ['POST'], '/echo_nested_many_load_from', echo_nested_many_load_from)
    add_route(app, ['GET'], '/echo_match_info/{mymatch}', echo_match_info)
    add_route(app, ['GET'], '/echo_method', EchoHandler().get)

    return app
