# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import sys
import json

import pytest
import mock
from marshmallow import fields

from webtest import TestApp
from webargs.djangoparser import DjangoParser

PY26 = sys.version_info[0] == 2 and int(sys.version_info[1]) < 7
if not PY26:
    from tests.testapp.testapp.wsgi import application

pytestmark = pytest.mark.skipif(PY26, reason='Django is not compatible with python 2.6')

@pytest.fixture
def testapp():
    """A webtest app that wraps the django wsgi app.
    """
    return TestApp(application)

@pytest.fixture
def mockrequest():
    return mock.Mock()

# Parametrize each test with a route that uses a function view and a route that
# uses a class-based view

@pytest.mark.parametrize("route", [
    '/simpleview/?name=Fred',
    '/simplecbvview/?name=Fred'
])
def test_parse_querystring(route, testapp):
    res = testapp.get(route)
    assert res.json == {'name': 'Fred'}


@pytest.mark.parametrize("route", [
    '/simpleview/',
    '/simplecbvview/'
])
def test_default(route, testapp):
    res = testapp.get(route)
    assert res.json == {'name': 'World'}

@pytest.mark.parametrize("route", [
    '/simpleview/',
    '/simplecbvview/'
])
def test_parse_form_data(route, testapp):
    res = testapp.post(route, {'name': 'Fred'})
    assert res.json == {'name': 'Fred'}

@pytest.mark.parametrize("route", [
    '/simpleview/',
    '/simplecbvview/'
])
def test_parse_json_data(route, testapp):
    res = testapp.post_json(route, {'name': 'Fred'})
    assert res.json == {'name': 'Fred'}


@pytest.mark.parametrize("route", [
    '/simpleview/',
    '/simplecbvview/'
])
def test_parse_json_data_with_vendor_media_type(route, testapp):
    res = testapp.post(route, json.dumps({'name': 'Fred'}), content_type='application/vnd.api+json')
    assert res.request.content_type == 'application/vnd.api+json'  # sanity check
    assert res.json == {'name': 'Fred'}

@pytest.mark.parametrize("route", [
    '/decoratedview/?name=Fred',
    '/decoratedcbv/?name=Fred'
])
def test_decorated_view(route, testapp):
    res = testapp.get(route)
    assert res.json == {'name': 'Fred'}

@pytest.mark.parametrize("route", [
    '/simpleview/42/?name=Fred',
    '/simplecbvview/42/?name=Fred'
])
def test_decorated_with_url_param(route, testapp):
    res = testapp.get(route)
    assert res.json == {'name': 'Fred'}

def test_parse_headers_raises_not_implemented_error(mockrequest):
    field = fields.Field()
    p = DjangoParser()
    with pytest.raises(NotImplementedError) as excinfo:
        p.parse_arg('foo', field, req=mockrequest, locations=('headers',))
    assert 'Header parsing not supported by DjangoParser' in str(excinfo)

def test_parse_cookies(testapp):
    res = testapp.get('/cookieview/')
    assert res.json == {'name': 'Joe'}

@pytest.mark.parametrize("route", [
    '/simpleview_multi/?name=steve&name=Loria',
    '/simplecbv_multi/?name=steve&name=Loria'
])
def test_parse_multiple_querystring(route, testapp):
    res = testapp.get(route)
    assert res.json == {'name': ['steve', 'Loria']}

@pytest.mark.parametrize('route', [
    '/simpleview_multi/',
    '/simplecbv_multi/'
])
def test_parse_multiple_form(route, testapp):
    payload = {'name': ['steve', 'Loria']}
    res = testapp.post(route, payload)
    assert res.json == {'name': ['steve', 'Loria']}

def test_500_response_returned_if_validation_error(testapp):
    # Endpoint requires 'name'
    url = '/simpleview_required/'
    res = testapp.post_json(url, {}, expect_errors=True)
    assert res.status_code == 500

def test_validated_view(testapp):
    url = '/validatedview/'
    res = testapp.post_json(url, {'validated': 42}, expect_errors=True)
    assert res.status_code == 500
