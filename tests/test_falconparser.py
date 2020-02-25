import pytest
import falcon.testing

from webargs.testing import CommonTestCase
from tests.apps.falcon_app import create_app


class TestFalconParser(CommonTestCase):
    def create_app(self):
        return create_app()

    @pytest.mark.skip(reason="files location not supported for falconparser")
    def test_parse_files(self, testapp):
        pass

    def test_use_args_hook(self, testapp):
        assert testapp.get("/echo_use_args_hook?name=Fred").json == {"name": "Fred"}

    # https://github.com/marshmallow-code/webargs/issues/427
    def test_parse_json_with_nonutf8_chars(self, testapp):
        res = testapp.post(
            "/echo_json",
            b"\xfe",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            expect_errors=True,
        )

        assert res.status_code == 400
        assert res.json["errors"] == {"json": ["Invalid JSON body."]}

    # https://github.com/sloria/webargs/issues/329
    def test_invalid_json(self, testapp):
        res = testapp.post(
            "/echo_json",
            '{"foo": "bar", }',
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            expect_errors=True,
        )
        assert res.status_code == 400
        assert res.json["errors"] == {"json": ["Invalid JSON body."]}

    # Falcon converts headers to all-caps
    def test_parsing_headers(self, testapp):
        res = testapp.get("/echo_headers", headers={"name": "Fred"})
        assert res.json == {"NAME": "Fred"}

    # `falcon.testing.TestClient.simulate_request` parses request with `wsgiref`
    def test_body_parsing_works_with_simulate(self):
        app = self.create_app()
        client = falcon.testing.TestClient(app)
        res = client.simulate_post("/echo_json", json={"name": "Fred"},)
        assert res.json == {"name": "Fred"}
