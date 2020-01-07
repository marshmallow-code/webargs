import pytest
from tests.apps.django_app.base.wsgi import application

from webargs.testing import CommonTestCase


class TestDjangoParser(CommonTestCase):
    def create_app(self):
        return application

    @pytest.mark.skip(
        reason="skipping because DjangoParser does not implement handle_error"
    )
    def test_use_args_with_validation(self):
        pass

    @pytest.mark.skip(reason="headers location not supported by DjangoParser")
    def test_parsing_headers(self, testapp):
        pass

    def test_parsing_in_class_based_view(self, testapp):
        assert testapp.get("/echo_cbv?name=Fred").json == {"name": "Fred"}
        assert testapp.post_json("/echo_cbv", {"name": "Fred"}).json == {"name": "Fred"}

    def test_use_args_in_class_based_view(self, testapp):
        res = testapp.get("/echo_use_args_cbv?name=Fred")
        assert res.json == {"name": "Fred"}
        res = testapp.post_json("/echo_use_args_cbv", {"name": "Fred"})
        assert res.json == {"name": "Fred"}

    def test_use_args_in_class_based_view_with_path_param(self, testapp):
        res = testapp.get("/echo_use_args_with_path_param_cbv/42?name=Fred")
        assert res.json == {"name": "Fred"}
