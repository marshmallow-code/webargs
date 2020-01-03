import asyncio
import webtest
import webtest_aiohttp
import pytest

from io import BytesIO
from webargs.core import MARSHMALLOW_VERSION_INFO
from webargs.testing import CommonTestCase
from tests.apps.aiohttp_app import create_app


class TestAIOHTTPParser(CommonTestCase):
    def create_app(self):
        return create_app()

    def create_testapp(self, app):
        loop = asyncio.get_event_loop()
        self.loop = loop
        return webtest_aiohttp.TestApp(app, loop=loop)

    def after_create_app(self):
        self.loop.close()

    @pytest.mark.skip(reason="files location not supported for aiohttpparser")
    def test_parse_files(self, testapp):
        pass

    def test_parse_match_info(self, testapp):
        assert testapp.get("/echo_match_info/42").json == {"mymatch": 42}

    def test_use_args_on_method_handler(self, testapp):
        assert testapp.get("/echo_method").json == {"name": "World"}
        assert testapp.get("/echo_method?name=Steve").json == {"name": "Steve"}
        assert testapp.get("/echo_method_view").json == {"name": "World"}
        assert testapp.get("/echo_method_view?name=Steve").json == {"name": "Steve"}

    # regression test for https://github.com/marshmallow-code/webargs/issues/165
    def test_multiple_args(self, testapp):
        res = testapp.post_json("/echo_multiple_args", {"first": "1", "last": "2"})
        assert res.json == {"first": "1", "last": "2"}

    # regression test for https://github.com/marshmallow-code/webargs/issues/145
    def test_nested_many_with_data_key(self, testapp):
        # https://github.com/marshmallow-code/marshmallow/pull/714
        # on marshmallow 2, the field name can also be used
        if MARSHMALLOW_VERSION_INFO[0] < 3:
            res = testapp.post_json(
                "/echo_nested_many_data_key", {"x_field": [{"id": 42}]}
            )
            assert res.json == {"x_field": [{"id": 42}]}

        res = testapp.post_json("/echo_nested_many_data_key", {"X-Field": [{"id": 24}]})
        assert res.json == {"x_field": [{"id": 24}]}

        res = testapp.post_json("/echo_nested_many_data_key", {})
        assert res.json == {}

    def test_schema_as_kwargs_view(self, testapp):
        assert testapp.get("/echo_use_schema_as_kwargs").json == {"name": "World"}
        assert testapp.get("/echo_use_schema_as_kwargs?name=Chandler").json == {
            "name": "Chandler"
        }

    # https://github.com/marshmallow-code/webargs/pull/297
    def test_empty_json_body(self, testapp):
        environ = {"CONTENT_TYPE": "application/json", "wsgi.input": BytesIO(b"")}
        req = webtest.TestRequest.blank("/echo", environ)
        resp = testapp.do_request(req)
        assert resp.json == {"name": "World"}

    def test_use_args_multiple(self, testapp):
        res = testapp.post_json(
            "/echo_use_args_multiple?page=2&q=10", {"name": "Steve"}
        )
        assert res.json == {
            "query_parsed": {"page": 2, "q": 10},
            "json_parsed": {"name": "Steve"},
        }
