# -*- coding: utf-8 -*-
import mock

import pytest
from bottle import Bottle, debug, request, response
from webtest import TestApp

from webargs import Arg
from webargs.bottleparser import BottleParser

from .compat import text_type, b

hello_args = {
    'name': Arg(text_type, default='World', validate=lambda n: len(n) >= 3),
}

parser = BottleParser()


@pytest.fixture
def app():
    app = Bottle()
    @app.route('/echo', method=['GET', 'POST'])
    def index():
        return parser.parse(hello_args, request)
    debug(True)
    return app

@pytest.fixture
def testapp(app):
    return TestApp(app)

def test_parse_querystring_args(testapp):
    assert testapp.get('/echo?name=Fred').json == {'name': 'Fred'}

def test_parse_form(testapp):
    assert testapp.post('/echo', {'name': 'Joe'}).json == {'name': 'Joe'}

def test_parse_json(testapp):
    assert testapp.post_json('/echo', {'name': 'Fred'}).json == {'name': 'Fred'}

def test_parse_json_default(testapp):
    assert testapp.post_json('/echo', {}).json == {'name': 'World'}

def test_parsing_form_default(testapp):
    assert testapp.post('/echo', {}).json == {'name': 'World'}

@mock.patch('webargs.bottleparser.abort')
def test_abort_called_on_validation_error(abort, testapp):
    testapp.post('/echo', {'name': 'b'})
    assert abort.called

def test_use_args_decorator(app, testapp):
    @app.route('/foo/', method=['GET', 'POST'])
    @parser.use_args({'myvalue': Arg(int)})
    def echo2(args):
        return args
    assert testapp.post('/foo/', {'myvalue': 23}).json == {'myvalue': 23}

def test_use_args_with_url_params(app, testapp):
    @app.route('/foo/<name>')
    @parser.use_args({'myvalue': Arg(int)})
    def foo(args, name):
        return args
    assert testapp.get('/foo/Fred?myvalue=42').json == {'myvalue': 42}

def test_parsing_headers(app, testapp):
    @app.route('/echo2')
    def echo2():
        args = parser.parse(hello_args, request, targets=('headers',))
        return args
    assert testapp.get('/echo2', headers={'name': b('Fred')}).json \
            == {'name': 'Fred'}

def test_parsing_cookies(app, testapp):
    @app.route('/setcookie')
    def setcookie():
        response.set_cookie('name', 'Fred')
        return {}

    @app.route('/echocookie')
    def echocookie():
        args = parser.parse(hello_args, request, targets=('cookies',))
        return args
    testapp.get('/setcookie')
    assert testapp.get('/echocookie').json == {'name': 'Fred'}
