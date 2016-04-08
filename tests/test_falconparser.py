# -*- coding: utf-8 -*-
import pytest

from tests.common import CommonTestCase
from tests.apps.falcon_app import create_app

class TestFalconParser(CommonTestCase):

    def create_app(self):
        return create_app()

    @pytest.mark.skip(reason='files location not supported for falconparser')
    def test_parse_files(self, testapp):
        pass

    def test_use_args_hook(self, testapp):
        assert testapp.get('/echo_use_args_hook?name=Fred').json == {'name': 'Fred'}

    def test_raises_lookup_error_if_invalid_code_is_passed_to_validation_error(self, testapp):
        with pytest.raises(LookupError) as excinfo:
            testapp.get('/error_invalid?text=foo')
        assert excinfo.value.args[0] == 'Status code 12345 not supported'
