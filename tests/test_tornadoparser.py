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

from webargs import Arg, Missing, ValidationError
from webargs.tornadoparser import parser, use_args, use_kwargs, parse_json, get_value

name = 'name'
bvalue = b'value'
value = 'value'

def test_get_value_basic():
    assert get_value({'foo': 42}, 'foo', False) == 42
    assert get_value({'foo': 42}, 'bar', False) is Missing
    assert get_value({'foos': ['a', 'b']}, 'foos', True) == ['a', 'b']
    # https://github.com/sloria/webargs/pull/30
    assert get_value({'foos': ['a', 'b']}, 'bar', True) is Missing

class TestQueryArgs(object):

    def setup_method(self, method):
        parser.clear_cache()

    def test_it_should_get_single_values(self):
        query = [(name, value)]
        arg = Arg(multiple=False)
        request = make_get_request(query)

        result = parser.parse_querystring(request, name, arg)

        assert result == bvalue

    def test_it_should_get_multiple_values(self):
        query = [(name, value), (name, value)]
        arg = Arg(multiple=True)
        request = make_get_request(query)

        result = parser.parse_querystring(request, name, arg)

        assert result == [bvalue, bvalue]

    def test_it_should_return_missing_if_not_present(self):
        query = []
        arg = Arg(multiple=False)
        arg2 = Arg(int, multiple=False)
        request = make_get_request(query)

        result = parser.parse_querystring(request, name, arg)
        result2 = parser.parse_querystring(request, name, arg2)

        assert result is Missing
        assert result2 is Missing

    def test_it_should_return_empty_list_if_multiple_and_not_present(self):
        query = []
        arg = Arg(multiple=True)
        request = make_get_request(query)

        result = parser.parse_querystring(request, name, arg)

        assert result is Missing


class TestFormArgs(object):

    def setup_method(self, method):
        parser.clear_cache()

    def test_it_should_get_single_values(self):
        query = [(name, value)]
        arg = Arg(multiple=False)
        request = make_form_request(query)

        result = parser.parse_form(request, name, arg)

        assert result == bvalue

    def test_it_should_get_multiple_values(self):
        query = [(name, value), (name, value)]
        arg = Arg(multiple=True)
        request = make_form_request(query)

        result = parser.parse_form(request, name, arg)

        assert result == [bvalue, bvalue]

    def test_it_should_return_missing_if_not_present(self):
        query = []
        arg = Arg(multiple=False)
        request = make_form_request(query)

        result = parser.parse_form(request, name, arg)

        assert result is Missing

    def test_it_should_return_empty_list_if_multiple_and_not_present(self):
        query = []
        arg = Arg(multiple=True)
        request = make_form_request(query)

        result = parser.parse_form(request, name, arg)

        assert result is Missing


class TestJSONArgs(object):

    def setup_method(self, method):
        parser.clear_cache()

    def test_it_should_get_single_values(self):
        query = {name: value}
        arg = Arg(multiple=False)
        request = make_json_request(query)
        result = parser.parse_json(request, name, arg)

        assert result == value

    def test_it_should_get_multiple_values(self):
        query = {name: [value, value]}
        arg = Arg(multiple=True)
        request = make_json_request(query)
        result = parser.parse_json(request, name, arg)

        assert result == [value, value]

    def test_it_should_get_multiple_nested_values(self):
        query = {name: [{'id': 1, 'name': 'foo'}, {'id': 2, 'name': 'bar'}]}
        arg = Arg({'id': Arg(), 'name': Arg()}, multiple=True)
        request = make_json_request(query)
        result = parser.parse_json(request, name, arg)
        assert result == [{'id': 1, 'name': 'foo'}, {'id': 2, 'name': 'bar'}]

    def test_it_should_return_missing_if_not_present(self):
        query = {}
        arg = Arg(multiple=False)
        request = make_json_request(query)
        result = parser.parse_json(request, name, arg)

        assert result is Missing

    def test_it_should_return_empty_list_if_multiple_and_not_present(self):
        query = {}
        arg = Arg(multiple=True)
        request = make_json_request(query)
        result = parser.parse_json(request, name, arg)

        assert result is Missing

    def test_it_should_handle_type_error_on_parse_json(self):
        arg = Arg()
        request = make_request(
            body=tornado.concurrent.Future,
            headers={'Content-Type': 'application/json'},
        )
        result = parser.parse_json(request, name, arg)
        assert parser._cache['json'] == {}
        assert result is Missing

    def test_it_should_handle_value_error_on_parse_json(self):
        arg = Arg()
        request = make_request('this is json not')
        result = parser.parse_json(request, name, arg)
        assert parser._cache['json'] == {}
        assert result is Missing


class TestHeadersArgs(object):

    def setup_method(self, method):
        parser.clear_cache()

    def test_it_should_get_single_values(self):
        query = {name: value}
        arg = Arg(multiple=False)
        request = make_request(headers=query)

        result = parser.parse_headers(request, name, arg)

        assert result == value

    def test_it_should_get_multiple_values(self):
        query = {name: [value, value]}
        arg = Arg(multiple=True)
        request = make_request(headers=query)

        result = parser.parse_headers(request, name, arg)

        assert result == [value, value]

    def test_it_should_return_missing_if_not_present(self):
        query = {}
        arg = Arg(multiple=False)
        request = make_request(headers=query)

        result = parser.parse_headers(request, name, arg)

        assert result is Missing

    def test_it_should_return_empty_list_if_multiple_and_not_present(self):
        query = {}
        arg = Arg(multiple=True)
        request = make_request(headers=query)

        result = parser.parse_headers(request, name, arg)

        assert result is Missing


class TestFilesArgs(object):

    def setup_method(self, method):
        parser.clear_cache()

    def test_it_should_get_single_values(self):
        query = [(name, value)]
        arg = Arg(multiple=False)
        request = make_files_request(query)

        result = parser.parse_files(request, name, arg)

        assert result == value

    def test_it_should_get_multiple_values(self):
        query = [(name, value), (name, value)]
        arg = Arg(multiple=True)
        request = make_files_request(query)

        result = parser.parse_files(request, name, arg)

        assert result == [value, value]

    def test_it_should_return_missing_if_not_present(self):
        query = []
        arg = Arg(multiple=False)
        request = make_files_request(query)

        result = parser.parse_files(request, name, arg)

        assert result is Missing

    def test_it_should_return_empty_list_if_multiple_and_not_present(self):
        query = []
        arg = Arg(multiple=True)
        request = make_files_request(query)

        result = parser.parse_files(request, name, arg)

        assert result is Missing


class TestErrorHandler(object):
    def test_it_should_raise_httperror_on_failed_validation(self):
        args = {'foo': Arg(validate=lambda x: False)}
        with pytest.raises(tornado.web.HTTPError):
            parser.parse(args, make_json_request({'foo': 42}))


class TestParse(object):

    def setup_method(self, method):
        parser.clear_cache()

    def test_it_should_parse_query_arguments(self):
        attrs = {
            'string': Arg(),
            'integer': Arg(int, multiple=True)
        }

        request = make_get_request([
            ('string', 'value'), ('integer', '1'), ('integer', '2')
        ])

        parsed = parser.parse(attrs, request)

        assert parsed['integer'] == [1, 2]
        assert parsed['string'] == bvalue

    def test_parsing_clears_cache(self):
        request = make_json_request({
            'string': 'value',
            'integer': [1, 2]
        })
        string_result = parser.parse_json(request, 'string', Arg(str))
        assert string_result == 'value'
        assert 'json' in parser._cache
        assert 'string' in parser._cache['json']
        assert 'integer' in parser._cache['json']
        attrs = {'string': Arg(str), 'integer': Arg(int, multiple=True)}
        parser.parse(attrs, request)
        assert parser._cache == {}

    def test_it_should_parse_form_arguments(self):
        attrs = {
            'string': Arg(),
            'integer': Arg(int, multiple=True)
        }

        request = make_form_request([
            ('string', 'value'), ('integer', '1'), ('integer', '2')
        ])

        parsed = parser.parse(attrs, request)

        assert parsed['integer'] == [1, 2]
        assert parsed['string'] == bvalue

    def test_it_should_parse_json_arguments(self):
        attrs = {
            'string': Arg(str),
            'integer': Arg(int, multiple=True)
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
            'string': Arg(str),
            'integer': Arg(int, multiple=True)
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
            'string': Arg(str),
            'integer': Arg(int, multiple=True)
        }

        request = make_cookie_request([
            ('string', 'value'), ('integer', '1'), ('integer', '2')
        ])

        parsed = parser.parse(attrs, request, locations=['cookies'])

        assert parsed['string'] == value
        assert parsed['integer'] == [2]

    def test_it_should_parse_files_arguments(self):
        attrs = {
            'string': Arg(str),
            'integer': Arg(int, multiple=True)
        }

        request = make_files_request([
            ('string', 'value'), ('integer', '1'), ('integer', '2')
        ])

        parsed = parser.parse(attrs, request, locations=['files'])

        assert parsed['string'] == value
        assert parsed['integer'] == [1, 2]

    def test_it_should_parse_required_arguments(self):
        args = {
            'foo': Arg(required=True),
        }

        request = make_json_request({})

        with pytest.raises(tornado.web.HTTPError) as excinfo:
            parser.parse(args, request)
        assert 'Required parameter "foo" not found' in str(excinfo)

    def test_it_should_parse_multiple_args_with_conversion(self):
        args = {
            'foo': Arg(int, multiple=True)
        }
        request = make_json_request({})
        result = parser.parse(args, request)
        assert result == {'foo': []}

    def test_it_should_parse_multiple_arg_allowed_missing(self):
        args = {
            'foo': Arg(int, multiple=True, allow_missing=True)
        }
        request = make_json_request({})
        result = parser.parse(args, request)
        assert result == {}

    def test_it_should_parse_multiple_arg_required(self):
        args = {
            'foo': Arg(int, multiple=True, required=True)
        }
        request = make_json_request({})
        with pytest.raises(tornado.web.HTTPError) as excinfo:
            parser.parse(args, request)
        assert 'Required parameter "foo" not found' in str(excinfo)


class TestUseArgs(object):

    def setup_method(self, method):
        parser.clear_cache()

    def test_it_should_pass_parsed_as_first_argument(self):
        class Handler(object):
            request = make_json_request({'key': 'value'})

            @use_args({'key': Arg()})
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

            @use_kwargs({'key': Arg()})
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

            @use_kwargs({'foo': Arg(int)}, validate=lambda args: args['foo'] > 42)
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


def make_json_request(args):
    return make_request(
        body=make_json_body(args),
        headers={
            'Content-Type': 'application/json; charset=UTF-8'
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
        'name': Arg(str)
    }

    @use_args(ARGS)
    def get(self, args):
        self.write(args)

    @use_args(ARGS)
    def post(self, args):
        self.write(args)

echo_app = tornado.web.Application([
    (r'/echo', EchoHandler)
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
        assert json_body['name'] is None

    def test_get_with_no_json_body(self):
        res = self.fetch('/echo', method='GET', headers={'Content-Type': 'application/json'})
        json_body = parse_json(res.body)
        assert json_body['name'] is None

class ValidateHandler(tornado.web.RequestHandler):
    ARGS = {
        'name': Arg(str, required=True)
    }

    @use_args(ARGS)
    def post(self, args):
        self.write(args)

def always_fail(val):
    raise ValidationError('something went wrong', status_code=401, extra='woops')

class AlwaysFailHandler(tornado.web.RequestHandler):
    ARGS = {
        'name': Arg(str, validate=always_fail)
    }

    @use_args(ARGS)
    def post(self, args):
        self.write(args)

validate_app = tornado.web.Application([
    (r'/echo', ValidateHandler),
    (r'/alwaysfail', AlwaysFailHandler),
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

    def test_missing_required_field_throws_400(self):
        res = self.fetch(
            '/echo',
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({'occupation': 'pizza'}),
        )
        assert res.code == 400

    def test_validation_error_with_status_code_and_extra_data(self):
        res = self.fetch(
            '/alwaysfail',
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({'name': 'foo'})
        )
        assert res.code == 401


if __name__ == '__main__':
    echo_app.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
