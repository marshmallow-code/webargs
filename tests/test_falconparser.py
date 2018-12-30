# -*- coding: utf-8 -*-
import pytest

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

    # https://github.com/sloria/webargs/issues/329
    def test_invalid_json(self, testapp):
        res = testapp.post(
            "/echo",
            '{"foo": "bar", }',
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            expect_errors=True,
        )
        assert res.status_code == 400
        assert res.json["errors"] == {"json": ["Invalid JSON body."]}
