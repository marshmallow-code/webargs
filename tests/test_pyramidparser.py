# -*- coding: utf-8 -*-
from .common import CommonTestCase
from .apps.pyramid_app import create_app

class TestPyramidParser(CommonTestCase):

    def create_app(self):
        return create_app()

    def test_use_args_with_callable_view(self, testapp):
        assert testapp.get('/echo_callable?value=42').json == {'value': 42}

    def test_parse_matchdict(self, testapp):
        assert testapp.get('/echo_matchdict/42').json == {'mymatch': 42}
