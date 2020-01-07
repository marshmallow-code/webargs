from webargs.testing import CommonTestCase


class TestPyramidParser(CommonTestCase):
    def create_app(self):
        from .apps.pyramid_app import create_app

        return create_app()

    def test_use_args_with_callable_view(self, testapp):
        assert testapp.get("/echo_callable?value=42").json == {"value": 42}

    def test_parse_matchdict(self, testapp):
        assert testapp.get("/echo_matchdict/42").json == {"mymatch": 42}
