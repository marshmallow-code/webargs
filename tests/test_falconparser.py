# -*- coding: utf-8 -*-
import json

import pytest
import falcon
import webtest

from webargs import fields
from webargs.falconparser import parser, use_args, use_kwargs

def use_args_hook(args, context_key='args', **kwargs):
    def hook(req, resp, params):
        parsed_args = parser.parse(args, req=req, **kwargs)
        req.context[context_key] = parsed_args
    return hook

@pytest.fixture()
def api():
    api_ = falcon.API()

    hello_args = {
        'name': fields.Str(required=True)
    }

    class ParseResource(object):

        def on_get(self, req, resp):
            args = parser.parse(hello_args, req=req, locations=('query', 'headers', 'cookies'))
            resp.body = json.dumps(args)

        def on_post(self, req, resp):
            args = parser.parse(hello_args, req=req, locations=('form', ))
            resp.body = json.dumps(args)

        def on_put(self, req, resp):
            args = parser.parse(hello_args, req=req, locations=('json', ))
            resp.body = json.dumps(args)

    class UseArgsResource(object):

        @use_args(hello_args)
        def on_get(self, req, resp, args):
            resp.body = json.dumps(args)

    class UseArgsWithParamResource(object):

        @use_args(hello_args)
        def on_get(self, req, resp, args, _id):
            args['_id'] = int(_id)
            resp.body = json.dumps(args)

    class UseKwargsResource(object):

        @use_kwargs(hello_args)
        def on_get(self, req, resp, name):
            resp.body = json.dumps({'name': name})

    class AlwaysErrorResource(object):
        args = {'bad': fields.Field(validate=lambda x: False)}

        def on_get(self, req, resp):
            parser.parse(self.args, req=req)

    @falcon.before(use_args_hook(hello_args))
    class HookResource(object):

        def on_get(self, req, resp):
            resp.body(req.context['args'])

    api_.add_route('/parse', ParseResource())
    api_.add_route('/use_args', UseArgsResource())
    api_.add_route('/use_args_with_param/{_id}', UseArgsWithParamResource())
    api_.add_route('/use_kwargs', UseKwargsResource())
    api_.add_route('/hook', UseKwargsResource())
    api_.add_route('/error', AlwaysErrorResource())

    return api_

@pytest.fixture()
def testapp(api):
    return webtest.TestApp(api)


class TestParseResource:

    url = '/parse'

    def test_parse_querystring(self, testapp):
        assert testapp.get(self.url + '?name=Fred').json == {'name': 'Fred'}

    def test_parse_form(self, testapp):
        res = testapp.post(self.url, {'name': 'Fred'})
        assert res.json == {'name': 'Fred'}

    def test_parse_json(self, testapp):
        res = testapp.put_json(self.url, {'name': 'Fred'})
        assert res.json == {'name': 'Fred'}

    def test_parse_json_with_vendor_media_type(self, testapp):
        res = testapp.put(
            self.url,
            json.dumps({'name': 'Fred'}),
            content_type='application/vnd.api+json;charset=utf8'
        )
        assert res.json == {'name': 'Fred'}

    def test_parse_headers(self, testapp):
        res = testapp.get(self.url, headers={'name': 'Fred'})
        assert res.json == {'name': 'Fred'}

    def test_parsing_cookies(self, testapp):
        testapp.set_cookie('name', 'Fred')
        assert testapp.get(self.url).json == {'name': 'Fred'}

class TestErrorHandler:

    url = '/error'

    def test_error_handler_returns_422_response(self, testapp):
        res = testapp.get(self.url + '?bad=42', expect_errors=True)
        assert res.status_code == 422
        assert 'errors' in res.json
        assert 'bad' in res.json['errors']
        assert res.json['errors']['bad'] == ['Invalid value.']

class TestUseArgsResource:
    url = '/use_args'

    def test_parse_querystring(self, testapp):
        assert testapp.get(self.url + '?name=Fred').json == {'name': 'Fred'}

class TestUseArgsWithParamResource:
    url = '/use_args_with_param/42'

    def test_parse_querystring(self, testapp):
        assert testapp.get(self.url + '?name=Fred').json == {'name': 'Fred', '_id': 42}

class TestUseKwargsResource:
    url = '/use_kwargs'

    def test_parse_querystring(self, testapp):
        assert testapp.get(self.url + '?name=Fred').json == {'name': 'Fred'}

class TestHookResource:
    url = '/hook'

    def test_parse_querystring(self, testapp):
        assert testapp.get(self.url + '?name=Fred').json == {'name': 'Fred'}
