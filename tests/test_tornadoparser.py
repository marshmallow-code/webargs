import marshmallow as ma
import pytest
import tornado.concurrent
import tornado.http1connection
import tornado.httpserver
import tornado.httputil
import tornado.ioloop
import tornado.web
from tornado.testing import AsyncHTTPTestCase
from webargs import fields, missing
from webargs.core import MARSHMALLOW_VERSION_INFO, json, parse_json
from webargs.tornadoparser import (
    WebArgsTornadoMultiDictProxy,
    parser,
    use_args,
    use_kwargs,
)

from urllib.parse import urlencode

try:
    # Python 3.5
    import mock
except ImportError:
    # Python 3.6+
    from unittest import mock


name = "name"
value = "value"


class AuthorSchema(ma.Schema):
    name = fields.Str(missing="World", validate=lambda n: len(n) >= 3)
    works = fields.List(fields.Str())


strict_kwargs = {"strict": True} if MARSHMALLOW_VERSION_INFO[0] < 3 else {}
author_schema = AuthorSchema(**strict_kwargs)


def test_tornado_multidictproxy():
    for dictval, fieldname, expected in (
        ({"name": "Sophocles"}, "name", "Sophocles"),
        ({"name": "Sophocles"}, "works", missing),
        ({"works": ["Antigone", "Oedipus Rex"]}, "works", ["Antigone", "Oedipus Rex"]),
        ({"works": ["Antigone", "Oedipus at Colonus"]}, "name", missing),
    ):
        proxy = WebArgsTornadoMultiDictProxy(dictval, author_schema)
        assert proxy.get(fieldname) == expected


class TestQueryArgs:
    def test_it_should_get_single_values(self):
        query = [("name", "Aeschylus")]
        request = make_get_request(query)
        result = parser.load_querystring(request, author_schema)
        assert result["name"] == "Aeschylus"

    def test_it_should_get_multiple_values(self):
        query = [("works", "Agamemnon"), ("works", "Nereids")]
        request = make_get_request(query)
        result = parser.load_querystring(request, author_schema)
        assert result["works"] == ["Agamemnon", "Nereids"]

    def test_it_should_return_missing_if_not_present(self):
        query = []
        request = make_get_request(query)
        result = parser.load_querystring(request, author_schema)
        assert result["name"] is missing
        assert result["works"] is missing


class TestFormArgs:
    def test_it_should_get_single_values(self):
        query = [("name", "Aristophanes")]
        request = make_form_request(query)
        result = parser.load_form(request, author_schema)
        assert result["name"] == "Aristophanes"

    def test_it_should_get_multiple_values(self):
        query = [("works", "The Wasps"), ("works", "The Frogs")]
        request = make_form_request(query)
        result = parser.load_form(request, author_schema)
        assert result["works"] == ["The Wasps", "The Frogs"]

    def test_it_should_return_missing_if_not_present(self):
        query = []
        request = make_form_request(query)
        result = parser.load_form(request, author_schema)
        assert result["name"] is missing
        assert result["works"] is missing


class TestJSONArgs:
    def test_it_should_get_single_values(self):
        query = {"name": "Euripides"}
        request = make_json_request(query)
        result = parser.load_json(request, author_schema)
        assert result["name"] == "Euripides"

    def test_parsing_request_with_vendor_content_type(self):
        query = {"name": "Euripides"}
        request = make_json_request(
            query, content_type="application/vnd.api+json; charset=UTF-8"
        )
        result = parser.load_json(request, author_schema)
        assert result["name"] == "Euripides"

    def test_it_should_get_multiple_values(self):
        query = {"works": ["Medea", "Electra"]}
        request = make_json_request(query)
        result = parser.load_json(request, author_schema)
        assert result["works"] == ["Medea", "Electra"]

    def test_it_should_get_multiple_nested_values(self):
        class CustomSchema(ma.Schema):
            works = fields.List(
                fields.Nested({"author": fields.Str(), "workname": fields.Str()})
            )

        custom_schema = CustomSchema(**strict_kwargs)

        query = {
            "works": [
                {"author": "Euripides", "workname": "Hecuba"},
                {"author": "Aristophanes", "workname": "The Birds"},
            ]
        }
        request = make_json_request(query)
        result = parser.load_json(request, custom_schema)
        assert result["works"] == [
            {"author": "Euripides", "workname": "Hecuba"},
            {"author": "Aristophanes", "workname": "The Birds"},
        ]

    def test_it_should_not_include_fieldnames_if_not_present(self):
        query = {}
        request = make_json_request(query)
        result = parser.load_json(request, author_schema)
        assert result == {}

    def test_it_should_handle_type_error_on_load_json(self):
        # but this is different from the test above where the payload was valid
        # and empty -- missing vs {}
        request = make_request(
            body=tornado.concurrent.Future(),
            headers={"Content-Type": "application/json"},
        )
        result = parser.load_json(request, author_schema)
        assert result is missing

    def test_it_should_handle_value_error_on_parse_json(self):
        request = make_request("this is json not")
        result = parser.load_json(request, author_schema)
        assert result is missing


class TestHeadersArgs:
    def test_it_should_get_single_values(self):
        query = {"name": "Euphorion"}
        request = make_request(headers=query)
        result = parser.load_headers(request, author_schema)
        assert result["name"] == "Euphorion"

    def test_it_should_get_multiple_values(self):
        query = {"works": ["Prometheus Bound", "Prometheus Unbound"]}
        request = make_request(headers=query)
        result = parser.load_headers(request, author_schema)
        assert result["works"] == ["Prometheus Bound", "Prometheus Unbound"]

    def test_it_should_return_missing_if_not_present(self):
        request = make_request()
        result = parser.load_headers(request, author_schema)
        assert result["name"] is missing
        assert result["works"] is missing


class TestFilesArgs:
    def test_it_should_get_single_values(self):
        query = [("name", "Sappho")]
        request = make_files_request(query)
        result = parser.load_files(request, author_schema)
        assert result["name"] == "Sappho"

    def test_it_should_get_multiple_values(self):
        query = [("works", "Sappho 31"), ("works", "Ode to Aphrodite")]
        request = make_files_request(query)
        result = parser.load_files(request, author_schema)
        assert result["works"] == ["Sappho 31", "Ode to Aphrodite"]

    def test_it_should_return_missing_if_not_present(self):
        query = []
        request = make_files_request(query)
        result = parser.load_files(request, author_schema)
        assert result["name"] is missing
        assert result["works"] is missing


class TestErrorHandler:
    def test_it_should_raise_httperror_on_failed_validation(self):
        args = {"foo": fields.Field(validate=lambda x: False)}
        with pytest.raises(tornado.web.HTTPError):
            parser.parse(args, make_json_request({"foo": 42}))


class TestParse:
    def test_it_should_parse_query_arguments(self):
        attrs = {"string": fields.Field(), "integer": fields.List(fields.Int())}

        request = make_get_request(
            [("string", "value"), ("integer", "1"), ("integer", "2")]
        )

        parsed = parser.parse(attrs, request, location="query")

        assert parsed["integer"] == [1, 2]
        assert parsed["string"] == value

    def test_it_should_parse_form_arguments(self):
        attrs = {"string": fields.Field(), "integer": fields.List(fields.Int())}

        request = make_form_request(
            [("string", "value"), ("integer", "1"), ("integer", "2")]
        )

        parsed = parser.parse(attrs, request, location="form")

        assert parsed["integer"] == [1, 2]
        assert parsed["string"] == value

    def test_it_should_parse_json_arguments(self):
        attrs = {"string": fields.Str(), "integer": fields.List(fields.Int())}

        request = make_json_request({"string": "value", "integer": [1, 2]})

        parsed = parser.parse(attrs, request)

        assert parsed["integer"] == [1, 2]
        assert parsed["string"] == value

    def test_it_should_raise_when_json_is_invalid(self):
        attrs = {"foo": fields.Str()}

        request = make_request(
            body='{"foo": 42,}', headers={"Content-Type": "application/json"}
        )
        with pytest.raises(tornado.web.HTTPError) as excinfo:
            parser.parse(attrs, request)
        error = excinfo.value
        assert error.status_code == 400
        assert error.messages == {"json": ["Invalid JSON body."]}

    def test_it_should_parse_header_arguments(self):
        attrs = {"string": fields.Str(), "integer": fields.List(fields.Int())}

        request = make_request(headers={"string": "value", "integer": ["1", "2"]})

        parsed = parser.parse(attrs, request, location="headers")

        assert parsed["string"] == value
        assert parsed["integer"] == [1, 2]

    def test_it_should_parse_cookies_arguments(self):
        attrs = {"string": fields.Str(), "integer": fields.List(fields.Int())}

        request = make_cookie_request(
            [("string", "value"), ("integer", "1"), ("integer", "2")]
        )

        parsed = parser.parse(attrs, request, location="cookies")

        assert parsed["string"] == value
        assert parsed["integer"] == [2]

    def test_it_should_parse_files_arguments(self):
        attrs = {"string": fields.Str(), "integer": fields.List(fields.Int())}

        request = make_files_request(
            [("string", "value"), ("integer", "1"), ("integer", "2")]
        )

        parsed = parser.parse(attrs, request, location="files")

        assert parsed["string"] == value
        assert parsed["integer"] == [1, 2]

    def test_it_should_parse_required_arguments(self):
        args = {"foo": fields.Field(required=True)}

        request = make_json_request({})

        msg = "Missing data for required field."
        with pytest.raises(tornado.web.HTTPError, match=msg):
            parser.parse(args, request)

    def test_it_should_parse_multiple_arg_required(self):
        args = {"foo": fields.List(fields.Int(), required=True)}
        request = make_json_request({})
        msg = "Missing data for required field."
        with pytest.raises(tornado.web.HTTPError, match=msg):
            parser.parse(args, request)


class TestUseArgs:
    def test_it_should_pass_parsed_as_first_argument(self):
        class Handler:
            request = make_json_request({"key": "value"})

            @use_args({"key": fields.Field()})
            def get(self, *args, **kwargs):
                assert args[0] == {"key": "value"}
                assert kwargs == {}
                return True

        handler = Handler()
        result = handler.get()

        assert result is True

    def test_it_should_pass_parsed_as_kwargs_arguments(self):
        class Handler:
            request = make_json_request({"key": "value"})

            @use_kwargs({"key": fields.Field()})
            def get(self, *args, **kwargs):
                assert args == ()
                assert kwargs == {"key": "value"}
                return True

        handler = Handler()
        result = handler.get()

        assert result is True

    def test_it_should_be_validate_arguments_when_validator_is_passed(self):
        class Handler:
            request = make_json_request({"foo": 41})

            @use_kwargs({"foo": fields.Int()}, validate=lambda args: args["foo"] > 42)
            def get(self, args):
                return True

        handler = Handler()
        with pytest.raises(tornado.web.HTTPError):
            handler.get()


def make_uri(args):
    return "/test?" + urlencode(args)


def make_form_body(args):
    return urlencode(args)


def make_json_body(args):
    return json.dumps(args)


def make_get_request(args):
    return make_request(uri=make_uri(args))


def make_form_request(args):
    return make_request(
        body=make_form_body(args),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )


def make_json_request(args, content_type="application/json; charset=UTF-8"):
    return make_request(
        body=make_json_body(args), headers={"Content-Type": content_type}
    )


def make_cookie_request(args):
    return make_request(headers={"Cookie": " ;".join("=".join(pair) for pair in args)})


def make_files_request(args):
    files = {}

    for key, value in args:
        if isinstance(value, list):
            files.setdefault(key, []).extend(value)
        else:
            files.setdefault(key, []).append(value)

    return make_request(files=files)


def make_request(uri=None, body=None, headers=None, files=None):
    uri = uri if uri is not None else ""
    body = body if body is not None else ""
    method = "POST" if body else "GET"
    # Need to make a mock connection right now because Tornado 4.0 requires a
    # remote_ip in the context attribute. 4.1 addresses this, and this
    # will be unnecessary once it is released
    # https://github.com/tornadoweb/tornado/issues/1118
    mock_connection = mock.Mock(spec=tornado.http1connection.HTTP1Connection)
    mock_connection.context = mock.Mock()
    mock_connection.remote_ip = None
    content_type = headers.get("Content-Type", "") if headers else ""
    request = tornado.httputil.HTTPServerRequest(
        method=method,
        uri=uri,
        body=body,
        headers=headers,
        files=files,
        connection=mock_connection,
    )

    tornado.httputil.parse_body_arguments(
        content_type=content_type,
        body=body.encode("latin-1") if hasattr(body, "encode") else body,
        arguments=request.body_arguments,
        files=request.files,
    )

    return request


class EchoHandler(tornado.web.RequestHandler):
    ARGS = {"name": fields.Str()}

    @use_args(ARGS, location="query")
    def get(self, args):
        self.write(args)


class EchoFormHandler(tornado.web.RequestHandler):
    ARGS = {"name": fields.Str()}

    @use_args(ARGS, location="form")
    def post(self, args):
        self.write(args)


class EchoJSONHandler(tornado.web.RequestHandler):
    ARGS = {"name": fields.Str()}

    @use_args(ARGS)
    def post(self, args):
        self.write(args)


class EchoWithParamHandler(tornado.web.RequestHandler):
    ARGS = {"name": fields.Str()}

    @use_args(ARGS, location="query")
    def get(self, id, args):
        self.write(args)


echo_app = tornado.web.Application(
    [
        (r"/echo", EchoHandler),
        (r"/echo_form", EchoFormHandler),
        (r"/echo_json", EchoJSONHandler),
        (r"/echo_with_param/(\d+)", EchoWithParamHandler),
    ]
)


class TestApp(AsyncHTTPTestCase):
    def get_app(self):
        return echo_app

    def test_post(self):
        res = self.fetch(
            "/echo_json",
            method="POST",
            headers={"Content-Type": "application/json"},
            body=json.dumps({"name": "Steve"}),
        )
        json_body = parse_json(res.body)
        assert json_body["name"] == "Steve"
        res = self.fetch(
            "/echo_json",
            method="POST",
            headers={"Content-Type": "application/json"},
            body=json.dumps({}),
        )
        json_body = parse_json(res.body)
        assert "name" not in json_body

    def test_get_with_no_json_body(self):
        res = self.fetch(
            "/echo", method="GET", headers={"Content-Type": "application/json"}
        )
        json_body = parse_json(res.body)
        assert "name" not in json_body

    def test_get_path_param(self):
        res = self.fetch(
            "/echo_with_param/42?name=Steve",
            method="GET",
            headers={"Content-Type": "application/json"},
        )
        json_body = parse_json(res.body)
        assert json_body == {"name": "Steve"}


class ValidateHandler(tornado.web.RequestHandler):
    ARGS = {"name": fields.Str(required=True)}

    @use_args(ARGS)
    def post(self, args):
        self.write(args)

    @use_kwargs(ARGS, location="query")
    def get(self, name):
        self.write({"status": "success"})


def always_fail(val):
    raise ma.ValidationError("something went wrong")


class AlwaysFailHandler(tornado.web.RequestHandler):
    ARGS = {"name": fields.Str(validate=always_fail)}

    @use_args(ARGS)
    def post(self, args):
        self.write(args)


validate_app = tornado.web.Application(
    [(r"/echo", ValidateHandler), (r"/alwaysfail", AlwaysFailHandler)]
)


class TestValidateApp(AsyncHTTPTestCase):
    def get_app(self):
        return validate_app

    def test_required_field_provided(self):
        res = self.fetch(
            "/echo",
            method="POST",
            headers={"Content-Type": "application/json"},
            body=json.dumps({"name": "johnny"}),
        )
        json_body = parse_json(res.body)
        assert json_body["name"] == "johnny"

    def test_missing_required_field_throws_422(self):
        res = self.fetch(
            "/echo",
            method="POST",
            headers={"Content-Type": "application/json"},
            body=json.dumps({"occupation": "pizza"}),
        )
        assert res.code == 422

    def test_user_validator_returns_422_by_default(self):
        res = self.fetch(
            "/alwaysfail",
            method="POST",
            headers={"Content-Type": "application/json"},
            body=json.dumps({"name": "Steve"}),
        )
        assert res.code == 422

    def test_use_kwargs_with_error(self):
        res = self.fetch("/echo", method="GET")
        assert res.code == 422


if __name__ == "__main__":
    echo_app.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
