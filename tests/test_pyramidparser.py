# -*- coding: utf-8 -*-
import json

import pytest
from webtest import TestApp
from marshmallow import Schema, post_load
from pyramid.config import Configurator

from webargs import fields
from webargs.pyramidparser import PyramidParser

parser = PyramidParser()

hello_args = {
    'name': fields.Str(missing='World'),
}

hello_multiple = {
    'name': fields.List(fields.Field()),
}

hello_validate = {
    'num': fields.Int(validate=lambda n: n != 3,
        error_messages={'validator_failed': "Houston, we've had a problem."}),
}


class HelloSchema(Schema):
    name = fields.String()

    @post_load
    def greet(self, item):
        item['url'] = self.context['request'].url
        return item

    class Meta(object):
        strict = True


@pytest.fixture
def testapp():
    def echo(request):
        args = parser.parse(hello_args, request)
        return args

    def echomulti(request):
        args = parser.parse(hello_multiple, request)
        return args

    def validate(request):
        args = parser.parse(hello_validate, request)
        return args

    def echocookie(request):
        args = parser.parse(hello_args, request, locations=('cookies',))
        return args

    def echo2(request):
        args = parser.parse(hello_args, request, locations=('headers',))
        return args

    @parser.use_args({'myfile': fields.List(fields.Field())}, locations=('files',))
    def echofile(request, args):
        _value = lambda f: f.getvalue().decode('utf-8')
        return dict((i.filename, _value(i.file)) for i in args['myfile'])

    @parser.use_args({'myvalue': fields.Int()})
    def foo(request, args):
        return args

    class Bar(object):
        def __init__(self, request):
            self.request = request

        @parser.use_args({'myvalue': fields.Int()})
        def __call__(self, args):
            return args

    @parser.use_kwargs({'myvalue': fields.Int()})
    def baz(request, myvalue):
        return {'myvalue': myvalue}

    @parser.use_args({'mymatch': fields.Int()}, locations=('matchdict',))
    def matched(request, args):
        return args

    @parser.use_args(lambda req: HelloSchema(context={'request': req}))
    def constructor(request, args):
        return args

    config = Configurator()

    config.add_route('echo', '/echo')
    config.add_route('echomulti', '/echomulti')
    config.add_route('validate', '/validate')
    config.add_route('echocookie', '/echocookie')
    config.add_route('echo2', '/echo2')
    config.add_route('echofile', '/echofile')
    config.add_route('foo', '/foo')
    config.add_route('bar', '/bar')
    config.add_route('baz', '/baz')
    config.add_route('matched', '/matched/{mymatch:\d+}')
    config.add_route('constructor', '/constructor')

    config.add_view(echo, route_name='echo', renderer='json')
    config.add_view(echomulti, route_name='echomulti', renderer='json')
    config.add_view(validate, route_name='validate', renderer='json')
    config.add_view(echocookie, route_name='echocookie', renderer='json')
    config.add_view(echo2, route_name='echo2', renderer='json')
    config.add_view(echofile, route_name='echofile', renderer='json')
    config.add_view(foo, route_name='foo', renderer='json')
    config.add_view(Bar, route_name='bar', renderer='json')
    config.add_view(baz, route_name='baz', renderer='json')
    config.add_view(matched, route_name='matched', renderer='json')
    config.add_view(constructor, route_name='constructor', renderer='json')

    app = config.make_wsgi_app()

    return TestApp(app)

def test_parse_querystring_args(testapp):
    assert testapp.get('/echo?name=Fred').json == {'name': 'Fred'}

def test_parse_querystring_multiple(testapp):
    expected = {'name': ['steve', 'Loria']}
    assert testapp.get('/echomulti?name=steve&name=Loria').json == expected

def test_parse_form(testapp):
    assert testapp.post('/echo', {'name': 'Joe'}).json == {'name': 'Joe'}

def test_parse_form_multiple(testapp):
    expected = {'name': ['steve', 'Loria']}
    assert testapp.post('/echomulti', {'name': ['steve', 'Loria']}).json == expected

def test_parsing_form_default(testapp):
    assert testapp.post('/echo', {}).json == {'name': 'World'}

def test_parse_json(testapp):
    assert testapp.post_json('/echo', {'name': 'Fred'}).json == {'name': 'Fred'}

def test_parse_json_with_vendor_media_type(testapp):
    res = testapp.post(
        '/echo',
        json.dumps({'name': 'Fred'}),
        content_type='application/vnd.api+json;charset=utf8'
    )
    assert res.request.content_type == 'application/vnd.api+json'  # sanity check
    assert res.json == {'name': 'Fred'}

def test_parse_json_default(testapp):
    assert testapp.post_json('/echo', {}).json == {'name': 'World'}

def test_parsing_cookies(testapp):
    testapp.set_cookie('name', 'Jean-Luc Picard')
    assert testapp.get('/echocookie').json == {'name': 'Jean-Luc Picard'}

def test_parsing_headers(testapp):
    res = testapp.get('/echo2', headers={'name': 'Fred'})
    assert res.json == {'name': 'Fred'}

def test_parse_files(testapp):
    payload = [('myfile', 'baz.txt', b'bar'), ('myfile', 'moo.txt', b'zoo')]
    res = testapp.post('/echofile', upload_files=payload)
    assert res.json == {'baz.txt': 'bar', 'moo.txt': 'zoo'}

def test_exception_on_validation_error(testapp):
    res = testapp.post('/validate', {'num': '3'}, expect_errors=True)
    assert res.status_code == 422

def test_validation_error_with_message(testapp):
    res = testapp.post('/validate', {'num': '3'}, expect_errors=True)
    res.mustcontain("Houston, we've had a problem.")

def test_use_args_decorator(testapp):
    assert testapp.post('/foo', {'myvalue': 23}).json == {'myvalue': 23}

def test_use_args_decorator_class(testapp):
    assert testapp.post('/bar', {'myvalue': 42}).json == {'myvalue': 42}

def test_user_kwargs_decorator(testapp):
    assert testapp.post('/baz', {'myvalue': 42}).json == {'myvalue': 42}

def test_parse_matchdict(testapp):
    res = testapp.get('/matched/1')
    assert res.json == {'mymatch': 1}


def test_use_args_callable(testapp):
    res = testapp.post('/constructor', {'name': 'Jean-Luc Picard'})
    assert res.json == {'name': 'Jean-Luc Picard', 'url': 'http://localhost/constructor'}
