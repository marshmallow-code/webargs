# -*- coding: utf-8 -*-

import pytest
from webtest import TestApp
from pyramid.config import Configurator

from webargs import Arg
from webargs.pyramidparser import PyramidParser
from .compat import text_type

parser = PyramidParser()

hello_args = {
    'name': Arg(text_type, default='World'),
}

hello_multiple = {
    'name': Arg(multiple=True),
}

hello_validate = {
    'num': Arg(int, validate=lambda n: n != 3, error="Houston, we've had a problem."),
}

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

    @parser.use_args({'myfile': Arg(multiple=True)}, locations=('files',))
    def echofile(request, args):
        _value = lambda f: f.getvalue().decode('utf-8')
        return dict((i.filename, _value(i.file)) for i in args['myfile'])

    @parser.use_args({'myvalue': Arg(int)})
    def foo(request, args):
        return args

    class Bar(object):
        def __init__(self, request):
            self.request = request

        @parser.use_args({'myvalue': Arg(int)})
        def __call__(self, args):
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

    config.add_view(echo, route_name='echo', renderer='json')
    config.add_view(echomulti, route_name='echomulti', renderer='json')
    config.add_view(validate, route_name='validate', renderer='json')
    config.add_view(echocookie, route_name='echocookie', renderer='json')
    config.add_view(echo2, route_name='echo2', renderer='json')
    config.add_view(echofile, route_name='echofile', renderer='json')
    config.add_view(foo, route_name='foo', renderer='json')
    config.add_view(Bar, route_name='bar', renderer='json')

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
    assert res.status_code == 400

def test_validation_error_with_message(testapp):
    res = testapp.post('/validate', {'num': '3'}, expect_errors=True)
    res.mustcontain("Houston, we've had a problem.")

def test_use_args_decorator(testapp):
    assert testapp.post('/foo', {'myvalue': 23}).json == {'myvalue': 23}

def test_use_args_decorator_class(testapp):
    assert testapp.post('/bar', {'myvalue': 42}).json == {'myvalue': 42}
