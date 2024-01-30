import falcon.testing
import pytest

from tests.apps.falcon_app import FALCON_SUPPORTS_ASYNC, create_app, create_async_app
from webargs.testing import CommonTestCase


class TestFalconParser(CommonTestCase):
    def create_app(self):
        return create_app()

    @pytest.mark.skip(reason="files location not supported for falconparser")
    def test_parse_files(self, testapp):
        pass

    def test_use_args_hook(self, testapp):
        assert testapp.get("/echo_use_args_hook?name=Fred").json == {"name": "Fred"}

    def test_parse_media(self, testapp):
        assert testapp.post_json("/echo_media", {"name": "Fred"}).json == {
            "name": "Fred"
        }

    def test_parse_media_missing(self, testapp):
        assert testapp.post("/echo_media", "").json == {"name": "World"}

    def test_parse_media_empty(self, testapp):
        assert testapp.post_json("/echo_media", {}).json == {"name": "World"}

    def test_parse_media_error_unexpected_int(self, testapp):
        res = testapp.post_json("/echo_media", 1, expect_errors=True)
        assert res.status_code == 422

    # https://github.com/marshmallow-code/webargs/issues/427
    @pytest.mark.parametrize("path", ["/echo_json", "/echo_media"])
    def test_parse_json_with_nonutf8_chars(self, testapp, path):
        res = testapp.post(
            path,
            b"\xfe",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            expect_errors=True,
        )

        assert res.status_code == 400
        if path.endswith("json"):
            assert res.json["errors"] == {"json": ["Invalid JSON body."]}

    # https://github.com/sloria/webargs/issues/329
    @pytest.mark.parametrize("path", ["/echo_json", "/echo_media"])
    def test_invalid_json(self, testapp, path):
        res = testapp.post(
            path,
            '{"foo": "bar", }',
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            expect_errors=True,
        )
        assert res.status_code == 400
        if path.endswith("json"):
            assert res.json["errors"] == {"json": ["Invalid JSON body."]}

    # Falcon converts headers to all-caps
    def test_parsing_headers(self, testapp):
        res = testapp.get("/echo_headers", headers={"name": "Fred"})
        assert res.json == {"NAME": "Fred"}

    # `falcon.testing.TestClient.simulate_request` parses request with `wsgiref`
    def test_body_parsing_works_with_simulate(self):
        app = self.create_app()
        client = falcon.testing.TestClient(app)
        res = client.simulate_post(
            "/echo_json",
            json={"name": "Fred"},
        )
        assert res.json == {"name": "Fred"}

    @pytest.mark.skipif(
        not FALCON_SUPPORTS_ASYNC, reason="requires a falcon version with async support"
    )
    def test_parse_querystring_args_async(self):
        app = create_async_app()
        client = falcon.testing.TestClient(app)
        assert client.simulate_get("/async_echo?name=Fred").json == {"name": "Fred"}

    @pytest.mark.skipif(
        not FALCON_SUPPORTS_ASYNC, reason="requires a falcon version with async support"
    )
    def test_async_use_args_decorator(self):
        app = create_async_app()
        client = falcon.testing.TestClient(app)
        assert client.simulate_get("/async_echo_use_args?name=Fred").json == {
            "name": "Fred"
        }
