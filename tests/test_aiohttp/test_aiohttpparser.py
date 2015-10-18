# -*- coding: utf-8 -*-
import json
import pytest

from webargs import fields

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


@pytest.mark.run_loop
def test_parsing_querystring(create_app_and_client):
    app, client = yield from create_app_and_client()
    configure_app(app)

    res = yield from client.get('/')
    assert res.status == 200
    text = yield from res.text()
    assert json.loads(text) == {'name': 'Steve'}

    res = yield from client.get('/?name=Joe')
    assert res.status == 200
    json_data = yield from res.json()
    assert json_data == {'name': 'Joe'}


@pytest.mark.run_loop
def test_parsing_form(create_app_and_client):
    app, client = yield from create_app_and_client()
    configure_app(app)

    res = yield from client.post('/', data={'name': 'Joe'})
    assert res.status == 200
    json_data = yield from res.json()
    assert json_data == {'name': 'Joe'}

@pytest.mark.run_loop
def test_parsing_json(create_app_and_client):
    app, client = yield from create_app_and_client()
    configure_app(app)

    res = yield from client.post(
        '/',
        data=json.dumps({'name': 'Joe'}),
        headers={'Content-Type': 'application/json'}
    )
    assert res.status == 200
    json_data = yield from res.json()
    assert json_data == {'name': 'Joe'}

@pytest.mark.run_loop
def test_parsing_headers(create_app_and_client):
    app, client = yield from create_app_and_client()

    @asyncio.coroutine
    def echo_header(request):
        parsed = yield from parser.parse({'myheader': fields.Field(location='headers')}, request)
        return jsonify(parsed)

    app.router.add_route('GET', '/echoheader', echo_header)

    res = yield from client.get('/echoheader', headers={'myheader': 'foo'})
    assert res.status == 200
    json_data = yield from res.json()
    assert json_data == {'myheader': 'foo'}


@pytest.mark.run_loop
def test_parsing_cookies(create_app_and_client):
    app, client = yield from create_app_and_client(client_params={'cookies': {'mycookie': 'foo'}})

    @asyncio.coroutine
    def echo_cookie(request):
        parsed = yield from parser.parse({'mycookie': fields.Field(location='cookies')}, request)
        return jsonify(parsed)

    app.router.add_route('GET', '/echocookie', echo_cookie)

    res = yield from client.get('/echocookie')
    assert res.status == 200
    json_data = yield from res.json()
    assert json_data == {'mycookie': 'foo'}


@pytest.mark.run_loop
def test_use_args(create_app_and_client):
    app, client = yield from create_app_and_client()

    @asyncio.coroutine
    @use_args({'name': fields.Field(missing='Steve')})
    def echo_use_args(request, args):
        return jsonify(args)

    app.router.add_route('GET', '/', echo_use_args)

    res = yield from client.get('/')
    assert res.status == 200
    json_data = yield from res.json()
    assert json_data == {'name': 'Steve'}

    res = yield from client.get('/?name=Joe')
    assert res.status == 200
    json_data = yield from res.json()
    assert json_data == {'name': 'Joe'}

@pytest.mark.run_loop
def test_use_kwargs_on_method(create_app_and_client):
    app, client = yield from create_app_and_client()

    class Handler:

        @asyncio.coroutine
        @use_args({'name': fields.Field(missing='Steve')})
        def get(self, request, args):
            return jsonify(args)

    handler = Handler()
    app.router.add_route('GET', '/', handler.get)

    res = yield from client.get('/')
    assert res.status == 200
    json_data = yield from res.json()
    assert json_data == {'name': 'Steve'}

    res = yield from client.get('/?name=Joe')
    assert res.status == 200
    json_data = yield from res.json()
    assert json_data == {'name': 'Joe'}

@pytest.mark.run_loop
def test_use_kwargs(create_app_and_client):
    app, client = yield from create_app_and_client()

    @use_kwargs({'name': fields.Field(missing='Steve')})
    def echo_use_kwargs(request, name):
        return jsonify({'name': name})

    app.router.add_route('GET', '/', echo_use_kwargs)

    res = yield from client.get('/')
    assert res.status == 200
    json_data = yield from res.json()
    assert json_data == {'name': 'Steve'}

    res = yield from client.get('/?name=Joe')
    assert res.status == 200
    json_data = yield from res.json()
    assert json_data == {'name': 'Joe'}


@pytest.mark.run_loop
def test_handling_error(create_app_and_client):
    app, client = yield from create_app_and_client()

    @asyncio.coroutine
    def validated(request):
        parsed = yield from parser.parse({'name': fields.Field(required=True)}, request)
        return jsonify(parsed)

    app.router.add_route('GET', '/', validated)

    res = yield from client.get('/')
    assert res.status == 422
    json_data = yield from res.json()
    assert 'name' in json_data
    assert json_data['name'] == ['Missing data for required field.']
