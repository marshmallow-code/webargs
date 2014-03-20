# -*- coding: utf-8 -*-

import json
import itertools
try:
    from urllib import urlencode  # python2
except ImportError:
    from urllib.parse import urlencode  # python3

import pytest

import tornado.web
import tornado.httputil
import tornado.httpserver

from webargs import Arg
from webargs.tornadoparser import parser, use_args, use_kwargs


class TestQueryArgs(object):
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

    def test_it_should_return_none_if_not_present(self):
        query = []
        arg = Arg(multiple=False)
        request = make_get_request(query)

        result = parser.parse_querystring(request, name, arg)

        assert result == None

    def test_it_should_return_empty_list_if_multiple_and_not_present(self):
        query = []
        arg = Arg(multiple=True)
        request = make_get_request(query)

        result = parser.parse_querystring(request, name, arg)

        assert result == []


class TestFormArgs(object):
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

    def test_it_should_return_none_if_not_present(self):
        query = []
        arg = Arg(multiple=False)
        request = make_form_request(query)

        result = parser.parse_form(request, name, arg)

        assert result == None

    def test_it_should_return_empty_list_if_multiple_and_not_present(self):
        query = []
        arg = Arg(multiple=True)
        request = make_form_request(query)

        result = parser.parse_form(request, name, arg)

        assert result == []


class TestJSONArgs(object):
    def test_it_should_get_single_values(self):
        query = {name: value}
        arg = Arg(multiple=False)
        request = make_json_request(query)

        parser._parse_json_body(request)
        result = parser.parse_json(request, name, arg)

        assert result == value

    def test_it_should_get_multiple_values(self):
        query = {name: [value, value]}
        arg = Arg(multiple=True)
        request = make_json_request(query)

        parser._parse_json_body(request)
        result = parser.parse_json(request, name, arg)

        assert result == [value, value]

    def test_it_should_return_none_if_not_present(self):
        query = {}
        arg = Arg(multiple=False)
        request = make_json_request(query)

        parser._parse_json_body(request)
        result = parser.parse_json(request, name, arg)

        assert result == None

    def test_it_should_return_empty_list_if_multiple_and_not_present(self):
        query = {}
        arg = Arg(multiple=True)
        request = make_json_request(query)

        parser._parse_json_body(request)
        result = parser.parse_json(request, name, arg)

        assert result == []


class TestHeadersArgs(object):
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

    def test_it_should_return_none_if_not_present(self):
        query = {}
        arg = Arg(multiple=False)
        request = make_request(headers=query)

        result = parser.parse_headers(request, name, arg)

        assert result == None

    def test_it_should_return_empty_list_if_multiple_and_not_present(self):
        query = {}
        arg = Arg(multiple=True)
        request = make_request(headers=query)

        result = parser.parse_headers(request, name, arg)

        assert result == []


class TestFilesArgs(object):
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

    def test_it_should_return_none_if_not_present(self):
        query = []
        arg = Arg(multiple=False)
        request = make_files_request(query)

        result = parser.parse_files(request, name, arg)

        assert result == None

    def test_it_should_return_empty_list_if_multiple_and_not_present(self):
        query = []
        arg = Arg(multiple=True)
        request = make_files_request(query)

        result = parser.parse_files(request, name, arg)

        assert result == []


class TestErrorHandler(object):
    def test_it_should_fail_with_bad_request_on_error(self):
        with pytest.raises(tornado.web.HTTPError) as error:
            parser.parse(None, make_request())


class TestParse(object):
    def test_it_should_parse_query_arguments(self):
        attrs = {
            'string': Arg(),
            'integer': Arg(int, multiple=True)
        }

        request = make_get_request([
            ('string', 'value'),('integer', '1'), ('integer', '2')
        ])

        parsed = parser.parse(attrs, request)

        assert parsed['integer'] == [1, 2]
        assert parsed['string'] == bvalue

    def test_it_should_parse_form_arguments(self):
        attrs = {
            'string': Arg(),
            'integer': Arg(int, multiple=True)
        }

        request = make_form_request([
            ('string', 'value'),('integer', '1'), ('integer', '2')
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

        parsed = parser.parse(attrs, request, targets=['headers'])

        assert parsed['string'] == value
        assert parsed['integer'] == [1, 2]

    def test_it_should_parse_cookies_arguments(self):
        attrs = {
            'string': Arg(str),
            'integer': Arg(int, multiple=True)
        }

        request = make_cookie_request([
            ('string', 'value'),('integer', '1'), ('integer', '2')
        ])

        parsed = parser.parse(attrs, request, targets=['cookies'])

        assert parsed['string'] == value
        assert parsed['integer'] == [2]

    def test_it_should_parse_files_arguments(self):
        attrs = {
            'string': Arg(str),
            'integer': Arg(int, multiple=True)
        }

        request = make_files_request([
            ('string', 'value'),('integer', '1'), ('integer', '2')
        ])

        parsed = parser.parse(attrs, request, targets=['files'])

        assert parsed['string'] == value
        assert parsed['integer'] == [1, 2]


class TestUseArgs(object):
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


name = 'name'
bvalue = b'value'
value = 'value'


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
            'Content-Type': 'application/json'
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

    request = tornado.httpserver.HTTPRequest(
        method=method, uri=uri, body=body, headers=headers, files=files)

    content_type = headers.get('Content-Type', u'') if headers else u''

    tornado.httputil.parse_body_arguments(
        content_type=content_type,
        body=body.encode('latin-1'),  # Tornado expects bodies to be latin-1
        arguments=request.body_arguments,
        files=request.files
    )

    return request
