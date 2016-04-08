# -*- coding: utf-8 -*-

import webtest_aiohttp
import pytest

from tests.common import CommonTestCase
from tests.apps.aiohttp_app import create_app


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

    def test_invalid_status_code_passed_to_validation_error(self, testapp):
        with pytest.raises(LookupError) as excinfo:
            testapp.get('/error_invalid?text=foo')
        assert excinfo.value.args[0] == 'No exception for 12345'
