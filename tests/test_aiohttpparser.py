# -*- coding: utf-8 -*-

import webtest_aiohttp
import pytest

import marshmallow

from tests.common import CommonTestCase
from tests.apps.aiohttp_app import create_app


MARSHMALLOW_2 = marshmallow.__version__.startswith('2')

class TestAIOHTTPParser(CommonTestCase):
    def create_app(self):
        return create_app()

    def create_testapp(self, app):
        return webtest_aiohttp.TestApp(app)

    @pytest.mark.skip(reason='files location not supported for aiohttpparser')
    def test_parse_files(self, testapp):
        pass

    def test_parse_match_info(self, testapp):
        assert testapp.get('/echo_match_info/42').json == {'mymatch': 42}

    def test_use_args_on_method_handler(self, testapp):
        assert testapp.get('/echo_method').json == {'name': 'World'}
        assert testapp.get('/echo_method?name=Steve').json == {'name': 'Steve'}
        assert testapp.get('/echo_method_view').json == {'name': 'World'}
        assert testapp.get('/echo_method_view?name=Steve').json == {'name': 'Steve'}

    def test_invalid_status_code_passed_to_validation_error(self, testapp):
        with pytest.raises(LookupError) as excinfo:
            testapp.get('/error_invalid?text=foo')
        assert excinfo.value.args[0] == 'No exception for 12345'

    # regression test for https://github.com/sloria/webargs/issues/165
    def test_multiple_args(self, testapp):
        res = testapp.post_json('/echo_multiple_args', {'first': '1', 'last': '2', '_ignore': 0})
        assert res.json == {'first': '1', 'last': '2'}

    # regression test for https://github.com/sloria/webargs/issues/145
    def test_nested_many_with_load_from(self, testapp):
        res = testapp.post_json('/echo_nested_many_load_from', {'x_field': [{'id': 42}]})
        # https://github.com/marshmallow-code/marshmallow/pull/714
        if MARSHMALLOW_2:
            assert res.json == {'x_field': [{'id': 42}]}

        res = testapp.post_json('/echo_nested_many_load_from', {'X-Field': [{'id': 24}]})
        assert res.json == {'x_field': [{'id': 24}]}

        res = testapp.post_json('/echo_nested_many_load_from', {})
        assert res.json == {}

    def test_schema_as_kwargs_view(self, testapp):
        assert testapp.get('/echo_use_schema_as_kwargs').json == {'name': 'World'}
        assert testapp.get('/echo_use_schema_as_kwargs?name=Chandler').json == {'name': 'Chandler'}
