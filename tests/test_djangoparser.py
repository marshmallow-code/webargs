import pytest

from tests.apps.django_app import DJANGO_SUPPORTS_ASYNC
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

    @pytest.mark.skipif(
        not DJANGO_SUPPORTS_ASYNC, reason="requires a django version with async support"
    )
    def test_parse_querystring_args_async(self, testapp):
        assert testapp.get("/async_echo?name=Fred").json == {"name": "Fred"}

    @pytest.mark.skipif(
        not DJANGO_SUPPORTS_ASYNC, reason="requires a django version with async support"
    )
    def test_async_use_args_decorator(self, testapp):
        assert testapp.get("/async_echo_use_args?name=Fred").json == {"name": "Fred"}
