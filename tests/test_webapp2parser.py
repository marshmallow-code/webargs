# -*- coding: utf-8 -*-
"""Tests for the webapp2 parser"""
import urllib
import json

import pytest
from marshmallow import fields
from marshmallow.compat import PY2
from webargs import ValidationError

pytestmark = pytest.mark.skipif(not PY2, reason='webapp2 is only compatible with Python 2')

import webtest

if PY2:
    # everything should be skipped via `pytestmark` here so it is OK
    import webapp2
    from webargs.webapp2parser import parser

hello_args = {
    'name': fields.Str(missing='World'),
}

hello_multiple = {
    'name': fields.List(fields.Str()),
}

hello_validate = {
    'num': fields.Int(validate=lambda n: n != 3,
        error_messages={'validator_failed': "Houston, we've had a problem."}),
}


def test_parse_querystring_args():
    request = webapp2.Request.blank('/echo?name=Fred')
    assert parser.parse(hello_args, req=request) == {'name': 'Fred'}


def test_parse_querystring_multiple():
    expected = {'name': ['steve', 'Loria']}
    request = webapp2.Request.blank('/echomulti?name=steve&name=Loria')
    assert parser.parse(hello_multiple, req=request) == expected


def test_parse_form():
    expected = {'name': 'Joe'}
    request = webapp2.Request.blank('/echo', POST=expected)
    assert parser.parse(hello_args, req=request) == expected


def test_parse_form_multiple():
    expected = {'name': ['steve', 'Loria']}
    request = webapp2.Request.blank('/echo', POST=urllib.urlencode(expected, doseq=True))
    assert parser.parse(hello_multiple, req=request) == expected


def test_parsing_form_default():
    request = webapp2.Request.blank('/echo', POST='')
    assert parser.parse(hello_args, req=request) == {'name': 'World'}


def test_parse_json():
    expected = {'name': 'Fred'}
    request = webapp2.Request.blank('/echo', POST=json.dumps(expected),
        headers={'content-type': 'application/json'})
    assert parser.parse(hello_args, req=request) == expected

def test_parse_json_with_vendor_media_type():
    expected = {'name': 'Fred'}
    request = webapp2.Request.blank('/echo', POST=json.dumps(expected),
        headers={'content-type': 'application/vnd.api+json'})
    assert parser.parse(hello_args, req=request) == expected


def test_parse_json_default():
    request = webapp2.Request.blank('/echo', POST='',
        headers={'content-type': 'application/json'})
    assert parser.parse(hello_args, req=request) == {'name': 'World'}


def test_parsing_cookies():
    # whitespace is not valid in a cookie name or value per RFC 6265
    # http://tools.ietf.org/html/rfc6265#section-4.1.1
    expected = {'name': 'Jean-LucPicard'}
    response = webapp2.Response()
    response.set_cookie('name', expected['name'])
    request = webapp2.Request.blank('/', headers={'Cookie': response.headers['Set-Cookie']})
    assert parser.parse(hello_args, req=request, locations=('cookies',)) == expected


def test_parsing_headers():
    expected = {'name': 'Fred'}
    request = webapp2.Request.blank('/', headers=expected)
    assert parser.parse(hello_args, req=request, locations=('headers',)) == expected


def test_parse_files():
    """Test parsing file upload using WebTest since I don't know how to mock
    that using a webob.Request
    """
    class Handler(webapp2.RequestHandler):
        @parser.use_args({'myfile': fields.List(fields.Field())}, locations=('files',))
        def post(self, args):
            self.response.content_type = 'application/json'
            _value = lambda f: f.getvalue().decode('utf-8')
            data = dict((i.filename, _value(i.file)) for i in args['myfile'])
            self.response.write(json.dumps(data))
    app = webapp2.WSGIApplication([('/', Handler)])
    testapp = webtest.TestApp(app)
    payload = [('myfile', 'baz.txt', b'bar'), ('myfile', 'moo.txt', b'zoo')]
    res = testapp.post('/', upload_files=payload)
    assert res.json == {'baz.txt': 'bar', 'moo.txt': 'zoo'}


def test_exception_on_validation_error():
    request = webapp2.Request.blank('/', POST={'num': '3'})
    with pytest.raises(ValidationError):
        parser.parse(hello_validate, req=request)


def test_validation_error_with_message():
    request = webapp2.Request.blank('/', POST={'num': '3'})
    with pytest.raises(ValidationError) as exc:
        parser.parse(hello_validate, req=request)
        assert "Houston, we've had a problem." in exc.value


def test_default_app_request():
    """Test that parser.parse uses the request from webapp2.get_request() if no
    request is passed
    """
    expected = {'name': 'Joe'}
    request = webapp2.Request.blank('/echo', POST=expected)
    app = webapp2.WSGIApplication([])
    app.set_globals(app, request)
    assert parser.parse(hello_args) == expected
