# -*- coding: utf-8 -*-

import json
try:
    from urllib import urlencode  # python2
except ImportError:
    from urllib.parse import urlencode  # python3

import mock
import pytest

import tornado.web
import tornado.httputil
import tornado.httpserver
import tornado.http1connection
import tornado.concurrent
import tornado.ioloop
from tornado.testing import AsyncHTTPTestCase

from webargs import fields, missing, ValidationError
from webargs.tornadoparser import parser, use_args, use_kwargs, get_value
from webargs.core import parse_json

name = 'name'
value = 'value'

def test_get_value_basic():
    field, multifield = fields.Field(), fields.List(fields.Str())
    assert get_value({'foo': 42}, 'foo', field) == 42
    assert get_value({'foo': 42}, 'bar', field) is missing
    assert get_value({'foos': ['a', 'b']}, 'foos', multifield) == ['a', 'b']
    # https://github.com/sloria/webargs/pull/30
    assert get_value({'foos': ['a', 'b']}, 'bar', multifield) is missing

class TestQueryArgs(object):

    def setup_method(self, method):
        parser.clear_cache()

    def test_it_should_get_single_values(self):
        query = [(name, value)]
        field = fields.Field()
        request = make_get_request(query)

        result = parser.parse_querystring(request, name, field)

        assert result == value

    def test_it_should_get_multiple_values(self):
        query = [(name, value), (name, value)]
        field = fields.List(fields.Field())
        request = make_get_request(query)

        result = parser.parse_querystring(request, name, field)

        assert result == [value, value]

    def test_it_should_return_missing_if_not_present(self):
        query = []
        field = fields.Field()
        field2 = fields.List(fields.Int())
        request = make_get_request(query)

        result = parser.parse_querystring(request, name, field)
        result2 = parser.parse_querystring(request, name, field2)

        assert result is missing
        assert result2 is missing

    def test_it_should_return_empty_list_if_multiple_and_not_present(self):
        query = []
        field = fields.List(fields.Field())
        request = make_get_request(query)

        result = parser.parse_querystring(request, name, field)

        assert result is missing


class TestFormArgs:

    def setup_method(self, method):
        parser.clear_cache()

    def test_it_should_get_single_values(self):
        query = [(name, value)]
        field = fields.Field()
        request = make_form_request(query)

        result = parser.parse_form(request, name, field)

        assert result == value

    def test_it_should_get_multiple_values(self):
        query = [(name, value), (name, value)]
        field = fields.List(fields.Field())
        request = make_form_request(query)

        result = parser.parse_form(request, name, field)

        assert result == [value, value]

    def test_it_should_return_missing_if_not_present(self):
        query = []
        field = fields.Field()
        request = make_form_request(query)

        result = parser.parse_form(request, name, field)

        assert result is missing

    def test_it_should_return_empty_list_if_multiple_and_not_present(self):
        query = []
        field = fields.List(fields.Field())
        request = make_form_request(query)

        result = parser.parse_form(request, name, field)

        assert result is missing


class TestJSONArgs(object):

    def setup_method(self, method):
        parser.clear_cache()

    def test_it_should_get_single_values(self):
        query = {name: value}
        field = fields.Field()
        request = make_json_request(query)
        result = parser.parse_json(request, name, field)

        assert result == value

    def test_parsing_request_with_vendor_content_type(self):
        query = {name: value}
        field = fields.Field()
        request = make_json_request(query, content_type='application/vnd.api+json; charset=UTF-8')
        result = parser.parse_json(request, name, field)

        assert result == value

    def test_it_should_get_multiple_values(self):
        query = {name: [value, value]}
        field = fields.List(fields.Field())
        request = make_json_request(query)
        result = parser.parse_json(request, name, field)

        assert result == [value, value]

    def test_it_should_get_multiple_nested_values(self):
        query = {name: [{'id': 1, 'name': 'foo'}, {'id': 2, 'name': 'bar'}]}
        field = fields.List(fields.Nested({'id': fields.Field(), 'name': fields.Field()}))
        request = make_json_request(query)
        result = parser.parse_json(request, name, field)
        assert result == [{'id': 1, 'name': 'foo'}, {'id': 2, 'name': 'bar'}]

    def test_it_should_return_missing_if_not_present(self):
        query = {}
        field = fields.Field()
        request = make_json_request(query)
        result = parser.parse_json(request, name, field)

        assert result is missing

    def test_it_should_return_empty_list_if_multiple_and_not_present(self):
        query = {}
        field = fields.List(fields.Field())
        request = make_json_request(query)
        result = parser.parse_json(request, name, field)

        assert result is missing

    def test_it_should_handle_type_error_on_parse_json(self):
        field = fields.Field()
        request = make_request(
            body=tornado.concurrent.Future,
            headers={'Content-Type': 'application/json'},
        )
        result = parser.parse_json(request, name, field)
        assert parser._cache['json'] == {}
        assert result is missing

    def test_it_should_handle_value_error_on_parse_json(self):
        field = fields.Field()
        request = make_request('this is json not')
        result = parser.parse_json(request, name, field)
        assert parser._cache['json'] == {}
        assert result is missing


class TestHeadersArgs(object):

    def setup_method(self, method):
        parser.clear_cache()

    def test_it_should_get_single_values(self):
        query = {name: value}
        field = fields.Field()
        request = make_request(headers=query)

        result = parser.parse_headers(request, name, field)

        assert result == value

    def test_it_should_get_multiple_values(self):
        query = {name: [value, value]}
        field = fields.List(fields.Field())
        request = make_request(headers=query)

        result = parser.parse_headers(request, name, field)

        assert result == [value, value]

    def test_it_should_return_missing_if_not_present(self):
        field = fields.Field(multiple=False)
        request = make_request()

        result = parser.parse_headers(request, name, field)

        assert result is missing

    def test_it_should_return_empty_list_if_multiple_and_not_present(self):
        query = {}
        field = fields.List(fields.Field())
        request = make_request(headers=query)

        result = parser.parse_headers(request, name, field)

        assert result is missing


class TestFilesArgs(object):

    def setup_method(self, method):
        parser.clear_cache()

    def test_it_should_get_single_values(self):
        query = [(name, value)]
        field = fields.Field()
        request = make_files_request(query)

        result = parser.parse_files(request, name, field)

        assert result == value

    def test_it_should_get_multiple_values(self):
        query = [(name, value), (name, value)]
        field = fields.List(fields.Field())
        request = make_files_request(query)

        result = parser.parse_files(request, name, field)

        assert result == [value, value]

    def test_it_should_return_missing_if_not_present(self):
        query = []
        field = fields.Field()
        request = make_files_request(query)

        result = parser.parse_files(request, name, field)

        assert result is missing

    def test_it_should_return_empty_list_if_multiple_and_not_present(self):
        query = []
        field = fields.List(fields.Field())
        request = make_files_request(query)

        result = parser.parse_files(request, name, field)

        assert result is missing


class TestErrorHandler(object):
    def test_it_should_raise_httperror_on_failed_validation(self):
        args = {'foo': fields.Field(validate=lambda x: False)}
        with pytest.raises(tornado.web.HTTPError):
            parser.parse(args, make_json_request({'foo': 42}))


class TestParse(object):

    def setup_method(self, method):
        parser.clear_cache()

    def test_it_should_parse_query_arguments(self):
        attrs = {
            'string': fields.Field(),
            'integer': fields.List(fields.Int())
        }

        request = make_get_request([
            ('string', 'value'), ('integer', '1'), ('integer', '2')
        ])

        parsed = parser.parse(attrs, request)

        assert parsed['integer'] == [1, 2]
        assert parsed['string'] == value

    def test_parsing_clears_cache(self):
        request = make_json_request({
            'string': 'value',
            'integer': [1, 2]
        })
        string_result = parser.parse_json(request, 'string', fields.Str())
        assert string_result == 'value'
        assert 'json' in parser._cache
        assert 'string' in parser._cache['json']
        assert 'integer' in parser._cache['json']
        attrs = {'string': fields.Str(), 'integer': fields.List(fields.Int())}
        parser.parse(attrs, request)
        assert parser._cache == {}

    def test_it_should_parse_form_arguments(self):
        attrs = {
            'string': fields.Field(),
            'integer': fields.List(fields.Int()),
        }

        request = make_form_request([
            ('string', 'value'), ('integer', '1'), ('integer', '2')
        ])

        parsed = parser.parse(attrs, request)

        assert parsed['integer'] == [1, 2]
        assert parsed['string'] == value

    def test_it_should_parse_json_arguments(self):
        attrs = {
            'string': fields.Str(),
            'integer': fields.List(fields.Int()),
        }

        request = make_json_request({
            'string': 'value',
            'integer': [1, 2]
        })

        parsed = parser.parse(attrs, request)

        assert parsed['integer'] == [1, 2]
        assert parsed['string'] == value

    def test_it_should_parse_header_arguments(self):
        attrs = {
            'string': fields.Str(),
            'integer': fields.List(fields.Int()),
        }

        request = make_request(headers={
            'string': 'value',
            'integer': ['1', '2']
        })

        parsed = parser.parse(attrs, request, locations=['headers'])

        assert parsed['string'] == value
        assert parsed['integer'] == [1, 2]

    def test_it_should_parse_cookies_arguments(self):
        attrs = {
            'string': fields.Str(),
            'integer': fields.List(fields.Int()),
        }

        request = make_cookie_request([
            ('string', 'value'), ('integer', '1'), ('integer', '2')
        ])

        parsed = parser.parse(attrs, request, locations=['cookies'])

        assert parsed['string'] == value
        assert parsed['integer'] == [2]

    def test_it_should_parse_files_arguments(self):
        attrs = {
            'string': fields.Str(),
            'integer': fields.List(fields.Int()),
        }

        request = make_files_request([
            ('string', 'value'), ('integer', '1'), ('integer', '2')
        ])

        parsed = parser.parse(attrs, request, locations=['files'])

        assert parsed['string'] == value
        assert parsed['integer'] == [1, 2]

    def test_it_should_parse_required_arguments(self):
        args = {
            'foo': fields.Field(required=True),
        }

        request = make_json_request({})

        with pytest.raises(tornado.web.HTTPError) as excinfo:
            parser.parse(args, request)
        assert 'Missing data for required field.' in str(excinfo)

    def test_it_should_parse_multiple_arg_required(self):
        args = {
            'foo': fields.List(fields.Int(), required=True)
        }
        request = make_json_request({})
        with pytest.raises(tornado.web.HTTPError) as excinfo:
            parser.parse(args, request)
        assert 'Missing data for required field.' in str(excinfo)


class TestUseArgs(object):

    def setup_method(self, method):
        parser.clear_cache()

    def test_it_should_pass_parsed_as_first_argument(self):
        class Handler(object):
            request = make_json_request({'key': 'value'})

            @use_args({'key': fields.Field()})
            def get(self, *args, **kwargs):
                assert args[0] == {'key': 'value'}
                assert kwargs == {}
                return True

        handler = Handler()
        result = handler.get()

        assert result is True

    def test_it_should_pass_parsed_as_kwargs_arguments(self):
        class Handler(object):
            request = make_json_request({'key': 'value'})

            @use_kwargs({'key': fields.Field()})
            def get(self, *args, **kwargs):
                assert args == ()
                assert kwargs == {'key': 'value'}
                return True

        handler = Handler()
        result = handler.get()

        assert result is True

    def test_it_should_be_validate_arguments_when_validator_is_passed(self):
        class Handler(object):
            request = make_json_request({'foo': 41})

            @use_kwargs({'foo': fields.Int()}, validate=lambda args: args['foo'] > 42)
            def get(self, args):
                return True

        handler = Handler()
        with pytest.raises(tornado.web.HTTPError):
            handler.get()


def make_uri(args):
    return '/test?' + urlencode(args)


def make_form_body(args):
    return urlencode(args)


def make_json_body(args):
    return json.dumps(args)


def make_get_request(args):
    return make_request(uri=make_uri(args))


def make_form_request(args):
    return make_request(
        body=make_form_body(args),
        headers={
            'Content-Type': 'application/x-www-form-urlencoded'
        }
    )


def make_json_request(args, content_type='application/json; charset=UTF-8'):
    return make_request(
        body=make_json_body(args),
        headers={
            'Content-Type': content_type,
        }
    )


def make_cookie_request(args):
    return make_request(
        headers={
            'Cookie': ' ;'.join('='.join(pair) for pair in args)
        }
    )


def make_files_request(args):
    files = {}

    for key, value in args:
        if isinstance(value, list):
            files.setdefault(key, []).extend(value)
        else:
            files.setdefault(key, []).append(value)

    return make_request(files=files)


def make_request(uri=None, body=None, headers=None, files=None):
    uri = uri if uri is not None else u''
    body = body if body is not None else u''
    method = 'POST' if body else 'GET'
    # Need to make a mock connection right now because Tornado 4.0 requires a
    # remote_ip in the context attribute. 4.1 addresses this, and this
    # will be unnecessary once it is released
    # https://github.com/tornadoweb/tornado/issues/1118
    mock_connection = mock.Mock(spec=tornado.http1connection.HTTP1Connection)
    mock_connection.context = mock.Mock()
    mock_connection.remote_ip = None
    content_type = headers.get('Content-Type', u'') if headers else u''
    request = tornado.httputil.HTTPServerRequest(
        method=method, uri=uri, body=body, headers=headers, files=files,
        connection=mock_connection
    )

    tornado.httputil.parse_body_arguments(
        content_type=content_type,
        body=body.encode('latin-1') if hasattr(body, 'encode') else body,
        arguments=request.body_arguments,
        files=request.files
    )

    return request

class EchoHandler(tornado.web.RequestHandler):
    ARGS = {
        'name': fields.Str(),
    }

    @use_args(ARGS)
    def get(self, args):
        self.write(args)

    @use_args(ARGS)
    def post(self, args):
        self.write(args)

class EchoWithParamHandler(tornado.web.RequestHandler):
    ARGS = {
        'name': fields.Str(),
    }

    @use_args(ARGS)
    def get(self, id, args):
        self.write(args)

echo_app = tornado.web.Application([
    (r'/echo', EchoHandler),
    (r'/echo_with_param/(\d+)', EchoWithParamHandler),
])

class TestApp(AsyncHTTPTestCase):

    def get_app(self):
        return echo_app

    def test_post(self):
        res = self.fetch('/echo', method='POST', headers={'Content-Type': 'application/json'},
                        body=json.dumps({'name': 'Steve'}))
        json_body = parse_json(res.body)
        assert json_body['name'] == 'Steve'
        res = self.fetch('/echo', method='POST', headers={'Content-Type': 'application/json'},
                        body=json.dumps({}))
        json_body = parse_json(res.body)
        assert 'name' not in json_body

    def test_get_with_no_json_body(self):
        res = self.fetch('/echo', method='GET', headers={'Content-Type': 'application/json'})
        json_body = parse_json(res.body)
        assert 'name' not in json_body

    def test_get_path_param(self):
        res = self.fetch('/echo_with_param/42?name=Steve',
                         method='GET', headers={'Content-Type': 'application/json'})
        json_body = parse_json(res.body)
        assert json_body == {'name': 'Steve'}

class ValidateHandler(tornado.web.RequestHandler):
    ARGS = {
        'name': fields.Str(required=True),
    }

    @use_args(ARGS)
    def post(self, args):
        self.write(args)

    @use_kwargs(ARGS)
    def get(self, name):
        self.write({'status': 'success'})


def always_fail(val):
    raise ValidationError('something went wrong')

class AlwaysFailHandler(tornado.web.RequestHandler):
    ARGS = {
        'name': fields.Str(validate=always_fail)
    }

    @use_args(ARGS)
    def post(self, args):
        self.write(args)


def always_fail_with_400(val):
    raise ValidationError('something went wrong', status_code=400)

class AlwaysFailWith400Handler(tornado.web.RequestHandler):
    ARGS = {
        'name': fields.Str(validate=always_fail_with_400)
    }

    @use_args(ARGS)
    def post(self, args):
        self.write(args)


validate_app = tornado.web.Application([
    (r'/echo', ValidateHandler),
    (r'/alwaysfail', AlwaysFailHandler),
    (r'/alwaysfailwith400', AlwaysFailWith400Handler),
])

class TestValidateApp(AsyncHTTPTestCase):

    def get_app(self):
        return validate_app

    def test_required_field_provided(self):
        res = self.fetch(
            '/echo',
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({'name': 'johnny'}),
        )
        json_body = parse_json(res.body)
        assert json_body['name'] == 'johnny'

    def test_missing_required_field_throws_422(self):
        res = self.fetch(
            '/echo',
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({'occupation': 'pizza'}),
        )
        assert res.code == 422

    def test_user_validator_returns_422_by_default(self):
        res = self.fetch(
            '/alwaysfail',
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({'name': 'Steve'}),
        )
        assert res.code == 422

    def test_user_validator_with_status_code(self):
        res = self.fetch(
            '/alwaysfailwith400',
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({'name': 'Steve'}),
        )
        assert res.code == 400

    def test_use_kwargs_with_error(self):
        res = self.fetch(
            '/echo',
            method='GET',
        )
        assert res.code == 422


if __name__ == '__main__':
    echo_app.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
