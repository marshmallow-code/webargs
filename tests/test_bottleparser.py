# -*- coding: utf-8 -*-

import pytest
from bottle import Bottle, debug, request, response
from webtest import TestApp

from webargs import ValidationError, fields
from webargs.bottleparser import BottleParser

hello_args = {
    'name': fields.Str(missing='World', validate=lambda n: len(n) >= 3),
}
hello_multiple = {
    'name': fields.List(fields.Str())
}

parser = BottleParser()


@pytest.fixture
def app():
    app = Bottle()

    @app.route('/echo', method=['GET', 'POST'])
    def index():
        return parser.parse(hello_args, request)

    @app.route('/echomulti/', method=['GET', 'POST'])
    def multi():
        return parser.parse(hello_multiple, request)
    debug(True)
    return app

@pytest.fixture
def testapp(app):
    return TestApp(app)

def test_parse_querystring_args(testapp):
    assert testapp.get('/echo?name=Fred').json == {'name': 'Fred'}

def test_parse_querystring_multiple(testapp):
    expected = {'name': ['steve', 'Loria']}
    assert testapp.get('/echomulti/?name=steve&name=Loria').json == expected

def test_parse_form_multiple(testapp):
    expected = {'name': ['steve', 'Loria']}
    assert testapp.post('/echomulti/', {'name': ['steve', 'Loria']}).json == expected

def test_parse_form(testapp):
    assert testapp.post('/echo', {'name': 'Joe'}).json == {'name': 'Joe'}

def test_parse_json(testapp):
    assert testapp.post_json('/echo', {'name': 'Fred'}).json == {'name': 'Fred'}

def test_parse_json_default(testapp):
    assert testapp.post_json('/echo', {}).json == {'name': 'World'}

def test_parsing_form_default(testapp):
    assert testapp.post('/echo', {}).json == {'name': 'World'}

def test_abort_called_on_validation_error(testapp):
    res = testapp.post('/echo', {'name': 'b'}, expect_errors=True)
    assert res.status_code == 422

def test_validator_that_raises_validation_error(app):
    def always_fail(value):
        raise ValidationError('something went wrong')
    args = {'text': fields.Str(validate=always_fail)}

    @app.route('/validated', method=['POST'])
    def validated_route():
        parser.parse(args)
    vtestapp = TestApp(app)
    res = vtestapp.post_json('/validated', {'text': 'bar'}, expect_errors=True)
    assert res.status_code == 422

def test_use_args_decorator(app, testapp):
    @app.route('/foo/', method=['GET', 'POST'])
    @parser.use_args({'myvalue': fields.Int()})
    def echo2(args):
        return args
    assert testapp.post('/foo/', {'myvalue': 23}).json == {'myvalue': 23}

def test_use_args_with_validation(app, testapp):
    @app.route('/foo/', method=['GET', 'POST'])
    @parser.use_args({'myvalue': fields.Int()}, validate=lambda args: args['myvalue'] > 42)
    def echo(args):
        return args
    result = testapp.post('/foo/', {'myvalue': 43}, expect_errors=True)
    assert result.status_code == 200
    result = testapp.post('/foo/', {'myvalue': 41}, expect_errors=True)
    assert result.status_code == 422

def test_use_args_with_url_params(app, testapp):
    @app.route('/foo/<name>')
    @parser.use_args({'myvalue': fields.Int()})
    def foo(args, name):
        return args
    assert testapp.get('/foo/Fred?myvalue=42').json == {'myvalue': 42}

def test_use_kwargs_decorator(app, testapp):
    @app.route('/foo/', method=['GET', 'POST'])
    @parser.use_kwargs({'myvalue': fields.Int()})
    def echo2(myvalue):
        return {'myvalue': myvalue}
    assert testapp.post('/foo/', {'myvalue': 23}).json == {'myvalue': 23}

def test_use_kwargs_with_url_params(app, testapp):
    @app.route('/foo/<name>')
    @parser.use_kwargs({'myvalue': fields.Int()})
    def foo(myvalue, name):
        return {'myvalue': myvalue}
    assert testapp.get('/foo/Fred?myvalue=42').json == {'myvalue': 42}

def test_parsing_headers(app, testapp):
    @app.route('/echo2')
    def echo2():
        args = parser.parse(hello_args, request, locations=('headers',))
        return args
    res = testapp.get('/echo2', headers={'name': 'Fred'}).json
    assert res == {'name': 'Fred'}

def test_parsing_cookies(app, testapp):
    @app.route('/setcookie')
    def setcookie():
        response.set_cookie('name', 'Fred')
        return {}

    @app.route('/echocookie')
    def echocookie():
        args = parser.parse(hello_args, request, locations=('cookies',))
        return args
    testapp.get('/setcookie')
    assert testapp.get('/echocookie').json == {'name': 'Fred'}

def test_arg_specific_locations(app, testapp):
    testargs = {
        'name': fields.Str(location='json'),
        'age': fields.Int(location='querystring'),
    }

    @app.route('/echo', method=['POST'])
    def echo():
        args = parser.parse(testargs, request)
        return args
    resp = testapp.post_json('/echo?age=42', {'name': 'Fred'})
    assert resp.json['age'] == 42
    assert resp.json['name'] == 'Fred'
