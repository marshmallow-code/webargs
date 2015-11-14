# -*- coding: utf-8 -*-
from webargs import fields
from marshmallow import Schema

import asyncio

from webargs.aiohttpparser import parser, use_args, use_kwargs
from tests.test_aiohttp.utils import jsonify


def configure_app(app):
    """Add routes to app."""
    @asyncio.coroutine
    def echo(request):
        parsed = yield from parser.parse({'name': fields.Field(missing='Steve')}, request)
        return jsonify(parsed)

    app.router.add_route('GET', '/', echo)
    app.router.add_route('POST', '/', echo)

def test_parsing_querystring(app, client):
    configure_app(app)

    res = client.get('/')
    assert res.status_code == 200
    assert res.json == {'name': 'Steve'}

    res = client.get('/?name=Joe')
    assert res.status_code == 200
    assert res.json == {'name': 'Joe'}

# regression test for https://github.com/sloria/webargs/issues/80
def test_parse_missing_required_arg_with_extra_data(app, client):
    @asyncio.coroutine
    def parse_required(request):
        parsed = yield from parser.parse({'name': fields.Field(required=True)}, request)
        return jsonify(parsed)

    app.router.add_route('POST', '/', parse_required)

    res = client.post('/', {'abc': 123}, expect_errors=True)
    assert res.status_code == 422
    assert res.json == {'name': ['Missing data for required field.']}

def test_parsing_form(app, client):
    configure_app(app)

    res = client.post('/', {'name': 'Joe'})
    assert res.status_code == 200
    assert res.json == {'name': 'Joe'}

def test_parsing_json(app, client):
    configure_app(app)

    res = client.post_json(
        '/',
        {'name': 'Joe'},
    )
    assert res.status_code == 200
    assert res.json == {'name': 'Joe'}

def test_parsing_headers(app, client):

    @asyncio.coroutine
    def echo_header(request):
        parsed = yield from parser.parse({'myheader': fields.Field(location='headers')}, request)
        return jsonify(parsed)

    app.router.add_route('GET', '/echoheader', echo_header)

    res = client.get('/echoheader', headers={'myheader': 'foo'})
    assert res.status_code == 200
    assert res.json == {'myheader': 'foo'}

def test_parsing_match_info(app, client):

    @asyncio.coroutine
    def echo_match_info(request):
        parsed = yield from parser.parse({'mymatch': fields.Field(location='match_info')}, request)
        return jsonify(parsed)

    app.router.add_route('GET', '/{mymatch}', echo_match_info)

    res = client.get('/foo')
    assert res.status_code == 200
    assert res.json == {'mymatch': 'foo'}

def test_parsing_cookies(app, client):

    @asyncio.coroutine
    def echo_cookie(request):
        parsed = yield from parser.parse({'mycookie': fields.Field(location='cookies')}, request)
        return jsonify(parsed)

    app.router.add_route('GET', '/echocookie', echo_cookie)

    client.set_cookie('mycookie', 'foo')
    res = client.get('/echocookie')
    assert res.status_code == 200
    assert res.json == {'mycookie': 'foo'}

def test_parse_with_callable(app, client):

    class MySchema(Schema):
        foo = fields.Field(missing=42)

    def make_schema(req):
        return MySchema(context={'request': req})

    @asyncio.coroutine
    def echo_parse(request):
        args = yield from parser.parse(make_schema, request)
        return jsonify(args)

    app.router.add_route('GET', '/factory', echo_parse)

    res = client.get('/factory')
    assert res.status_code == 200
    assert res.json == {'foo': 42}


def test_use_args(app, client):

    @asyncio.coroutine
    @use_args({'name': fields.Field(missing='Steve')})
    def echo_use_args(request, args):
        return jsonify(args)

    app.router.add_route('GET', '/', echo_use_args)

    res = client.get('/')
    assert res.status_code == 200
    assert res.json == {'name': 'Steve'}

    res = client.get('/?name=Joe')
    assert res.status_code == 200
    assert res.json == {'name': 'Joe'}


def test_use_args_with_callable(app, client):

    class MySchema(Schema):
        foo = fields.Field(missing=42)

    def make_schema(req):
        return MySchema(context={'request': req})

    @asyncio.coroutine
    @use_args(make_schema)
    def echo_use_args(request, args):
        return jsonify(args)

    app.router.add_route('GET', '/use_args', echo_use_args)

    res = client.get('/use_args')
    assert res.status_code == 200
    assert res.json == {'foo': 42}


def test_use_kwargs_on_method(app, client):
    class Handler:

        @asyncio.coroutine
        @use_args({'name': fields.Field(missing='Steve')})
        def get(self, request, args):
            return jsonify(args)

    handler = Handler()
    app.router.add_route('GET', '/', handler.get)

    res = client.get('/')
    assert res.status_code == 200
    assert res.json == {'name': 'Steve'}

    res = client.get('/?name=Joe')
    assert res.status_code == 200
    json_data = res.json
    assert json_data == {'name': 'Joe'}

def test_use_kwargs(app, client):

    @use_kwargs({'name': fields.Field(missing='Steve')})
    def echo_use_kwargs(request, name):
        return jsonify({'name': name})

    app.router.add_route('GET', '/', echo_use_kwargs)

    res = client.get('/')
    assert res.status_code == 200
    assert res.json == {'name': 'Steve'}

    res = client.get('/?name=Joe')
    assert res.status_code == 200
    assert res.json == {'name': 'Joe'}

def test_handling_error(app, client):

    @asyncio.coroutine
    def validated(request):
        parsed = yield from parser.parse({'name': fields.Field(required=True)}, request)
        return jsonify(parsed)

    app.router.add_route('GET', '/', validated)

    res = client.get('/', expect_errors=True)
    assert res.status_code == 422
    assert 'name' in res.json
    assert res.json['name'] == ['Missing data for required field.']

def test_use_args_with_variable_routes(app, client):

    @asyncio.coroutine
    @use_args({'letters2': fields.Str()})
    def handler(request, args):
        return jsonify({
            'letters1': request.match_info['letters1'],
            'letters2': args['letters2'],
        })

    app.router.add_route('GET', '/{letters1}/', handler)

    res = client.get('/abc/?letters2=def')
    assert res.status_code == 200
    assert res.json['letters1'] == 'abc'
    assert res.json['letters2'] == 'def'
