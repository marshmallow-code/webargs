from io import BytesIO
from unittest import mock

import pytest
import webtest
import webtest_aiohttp

from tests.apps.aiohttp_app import create_app
from webargs import fields
from webargs.aiohttpparser import AIOHTTPParser
from webargs.testing import CommonTestCase


@pytest.fixture
def web_request():
    req = mock.Mock()
    req.query = {}
    yield req
    req.query = {}


class TestAIOHTTPParser(CommonTestCase):
    def create_app(self):
        return create_app()

    def create_testapp(self, app, event_loop):
        return webtest_aiohttp.TestApp(app, loop=event_loop)

    @pytest.fixture
    def testapp(self, event_loop):
        return self.create_testapp(self.create_app(), event_loop)

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

    def test_validation_error_returns_422_response(self, testapp):
        res = testapp.post_json("/echo_json", {"name": "b"}, expect_errors=True)
        assert res.status_code == 422
        assert res.json == {"json": {"name": ["Shorter than minimum length 3."]}}


@pytest.mark.asyncio
async def test_aiohttpparser_synchronous_error_handler(web_request):
    parser = AIOHTTPParser()

    class CustomError(Exception):
        pass

    @parser.error_handler
    def custom_handle_error(error, req, schema, *, error_status_code, error_headers):
        raise CustomError("foo")

    with pytest.raises(CustomError):
        await parser.parse(
            {"foo": fields.Int(required=True)}, web_request, location="query"
        )


@pytest.mark.asyncio
async def test_aiohttpparser_asynchronous_error_handler(web_request):
    parser = AIOHTTPParser()

    class CustomError(Exception):
        pass

    @parser.error_handler
    async def custom_handle_error(
        error, req, schema, *, error_status_code, error_headers
    ):
        async def inner():
            raise CustomError("foo")

        await inner()

    with pytest.raises(CustomError):
        await parser.parse(
            {"foo": fields.Int(required=True)}, web_request, location="query"
        )
