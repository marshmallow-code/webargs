# -*- coding: utf-8 -*-
from __future__ import unicode_literals

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

@pytest.fixture
def testapp():
    def echo(request):
        args = parser.parse(hello_args, request)
        return args

    def echomulti(request):
        args = parser.parse(hello_multiple, request)
        return args

    config = Configurator()
    config.add_route('echo', '/echo')
    config.add_route('echomulti', '/echomulti')
    config.add_view(echo, route_name='echo', renderer='json')
    config.add_view(echomulti, route_name='echomulti', renderer='json')
    app = config.make_wsgi_app()

    return TestApp(app)

def test_parse_querystring_args(testapp):
    assert testapp.get('/echo?name=Fred').json == {'name': 'Fred'}

def test_parse_querystring_multiple(testapp):
    expected = {'name': ['steve', 'Loria']}
    assert testapp.get('/echomulti?name=steve&name=Loria').json == expected

def test_parse_form_multiple(testapp):
    expected = {'name': ['steve', 'Loria']}
    assert testapp.post('/echomulti', {'name': ['steve', 'Loria']}).json == expected

def test_parse_form(testapp):
    assert testapp.post('/echo', {'name': 'Joe'}).json == {'name': 'Joe'}

def test_parse_json(testapp):
    assert testapp.post_json('/echo', {'name': 'Fred'}).json == {'name': 'Fred'}

def test_parse_json_default(testapp):
    assert testapp.post_json('/echo', {}).json == {'name': 'World'}

def test_parsing_form_default(testapp):
    assert testapp.post('/echo', {}).json == {'name': 'World'}
