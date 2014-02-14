# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest
from webtest import TestApp

from tests.testapp.testapp.wsgi import application


@pytest.fixture
def testapp():
    """A webtest app that wraps the django wsgi app.
    """
    return TestApp(application)

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
