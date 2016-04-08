# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import sys

import pytest

PY26 = sys.version_info[0] == 2 and int(sys.version_info[1]) < 7
PY33 = sys.version_info[0] == 3 and int(sys.version_info[1]) < 4
if not PY26 and not PY33:
    from tests.apps.django_app.base.wsgi import application

pytestmark = pytest.mark.skipif(PY26 or PY33,
                                reason='Django is not compatible with python 2.6 or 3.3')

from tests.common import CommonTestCase

class TestDjangoParser(CommonTestCase):
    def create_app(self):
        return application

    @pytest.mark.skip(reason='skipping because DjangoParser does not implement handle_error')
    def test_use_args_with_validation(self):
        pass

    @pytest.mark.skip(reason='headers location not supported by DjangoParser')
    def test_parsing_headers(self, testapp):
        pass

    def test_parsing_in_class_based_view(self, testapp):
        assert testapp.get('/echo_cbv?name=Fred').json == {'name': 'Fred'}
        assert testapp.post('/echo_cbv', {'name': 'Fred'}).json == {'name': 'Fred'}

    def test_use_args_in_class_based_view(self, testapp):
        res = testapp.get('/echo_use_args_cbv?name=Fred')
        assert res.json == {'name': 'Fred'}
        res = testapp.post('/echo_use_args_cbv', {'name': 'Fred'})
        assert res.json == {'name': 'Fred'}

    def test_use_args_in_class_based_view_with_path_param(self, testapp):
        res = testapp.get('/echo_use_args_with_path_param_cbv/42?name=Fred')
        assert res.json == {'name': 'Fred'}
