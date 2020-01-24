"""Tests for the webapp2 parser"""
from urllib.parse import urlencode
from webargs.core import json

import pytest
import marshmallow as ma
from marshmallow import fields, ValidationError

import webtest
import webapp2
from webargs.webapp2parser import parser
from webargs.core import MARSHMALLOW_VERSION_INFO

hello_args = {"name": fields.Str(missing="World")}

hello_multiple = {"name": fields.List(fields.Str())}

hello_validate = {
    "num": fields.Int(
        validate=lambda n: n != 3,
        error_messages={"validator_failed": "Houston, we've had a problem."},
    )
}


class HelloSchema(ma.Schema):
    name = fields.Str(missing="World", validate=lambda n: len(n) >= 3)


# variant which ignores unknown fields
exclude_kwargs = (
    {"strict": True} if MARSHMALLOW_VERSION_INFO[0] < 3 else {"unknown": ma.EXCLUDE}
)
hello_exclude_schema = HelloSchema(**exclude_kwargs)


def test_parse_querystring_args():
    request = webapp2.Request.blank("/echo?name=Fred")
    assert parser.parse(hello_args, req=request, location="query") == {"name": "Fred"}


def test_parse_querystring_multiple():
    expected = {"name": ["steve", "Loria"]}
    request = webapp2.Request.blank("/echomulti?name=steve&name=Loria")
    assert parser.parse(hello_multiple, req=request, location="query") == expected


def test_parse_form():
    expected = {"name": "Joe"}
    request = webapp2.Request.blank("/echo", POST=expected)
    assert parser.parse(hello_args, req=request, location="form") == expected


def test_parse_form_multiple():
    expected = {"name": ["steve", "Loria"]}
    request = webapp2.Request.blank("/echo", POST=urlencode(expected, doseq=True))
    assert parser.parse(hello_multiple, req=request, location="form") == expected


def test_parsing_form_default():
    request = webapp2.Request.blank("/echo", POST="")
    assert parser.parse(hello_args, req=request, location="form") == {"name": "World"}


def test_parse_json():
    expected = {"name": "Fred"}
    request = webapp2.Request.blank(
        "/echo", POST=json.dumps(expected), headers={"content-type": "application/json"}
    )
    assert parser.parse(hello_args, req=request) == expected


def test_parse_json_content_type_mismatch():
    request = webapp2.Request.blank(
        "/echo_json",
        POST=json.dumps({"name": "foo"}),
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    assert parser.parse(hello_args, req=request) == {"name": "World"}


def test_parse_invalid_json():
    request = webapp2.Request.blank(
        "/echo", POST='{"foo": "bar", }', headers={"content-type": "application/json"}
    )
    with pytest.raises(json.JSONDecodeError):
        parser.parse(hello_args, req=request)


def test_parse_json_with_vendor_media_type():
    expected = {"name": "Fred"}
    request = webapp2.Request.blank(
        "/echo",
        POST=json.dumps(expected),
        headers={"content-type": "application/vnd.api+json"},
    )
    assert parser.parse(hello_args, req=request) == expected


def test_parse_json_default():
    request = webapp2.Request.blank(
        "/echo", POST="", headers={"content-type": "application/json"}
    )
    assert parser.parse(hello_args, req=request) == {"name": "World"}


def test_parsing_cookies():
    # whitespace is not valid in a cookie name or value per RFC 6265
    # http://tools.ietf.org/html/rfc6265#section-4.1.1
    expected = {"name": "Jean-LucPicard"}
    response = webapp2.Response()
    response.set_cookie("name", expected["name"])
    request = webapp2.Request.blank(
        "/", headers={"Cookie": response.headers["Set-Cookie"]}
    )
    assert parser.parse(hello_args, req=request, location="cookies") == expected


def test_parsing_headers():
    expected = {"name": "Fred"}
    request = webapp2.Request.blank("/", headers=expected)
    assert (
        parser.parse(hello_exclude_schema, req=request, location="headers") == expected
    )


def test_parse_files():
    """Test parsing file upload using WebTest since I don't know how to mock
    that using a webob.Request
    """

    class Handler(webapp2.RequestHandler):
        @parser.use_args({"myfile": fields.List(fields.Field())}, location="files")
        def post(self, args):
            self.response.content_type = "application/json"

            def _value(f):
                return f.getvalue().decode("utf-8")

            data = {i.filename: _value(i.file) for i in args["myfile"]}
            self.response.write(json.dumps(data))

    app = webapp2.WSGIApplication([("/", Handler)])
    testapp = webtest.TestApp(app)
    payload = [("myfile", "baz.txt", b"bar"), ("myfile", "moo.txt", b"zoo")]
    res = testapp.post("/", upload_files=payload)
    assert res.json == {"baz.txt": "bar", "moo.txt": "zoo"}


def test_exception_on_validation_error():
    request = webapp2.Request.blank("/", POST={"num": "3"})
    with pytest.raises(ValidationError):
        parser.parse(hello_validate, req=request, location="form")


def test_validation_error_with_message():
    request = webapp2.Request.blank("/", POST={"num": "3"})
    with pytest.raises(ValidationError) as exc:
        parser.parse(hello_validate, req=request, location="form")
        assert "Houston, we've had a problem." in exc.value


def test_default_app_request():
    """Test that parser.parse uses the request from webapp2.get_request() if no
    request is passed
    """
    expected = {"name": "Joe"}
    request = webapp2.Request.blank("/echo", POST=expected)
    app = webapp2.WSGIApplication([])
    app.set_globals(app, request)
    assert parser.parse(hello_args, location="form") == expected
