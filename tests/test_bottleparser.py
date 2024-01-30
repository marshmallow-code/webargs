import pytest

from webargs.testing import CommonTestCase

from .apps.bottle_app import app


class TestBottleParser(CommonTestCase):
    def create_app(self):
        return app

    @pytest.mark.skip(reason="Parsing vendor media types is not supported in bottle")
    def test_parse_json_with_vendor_media_type(self, testapp):
        pass
