import itertools
import datetime

import pytest
from marshmallow import Schema, post_load, pre_load, class_registry, validates_schema
from werkzeug.datastructures import MultiDict as WerkMultiDict
from django.utils.datastructures import MultiValueDict as DjMultiDict
from bottle import MultiDict as BotMultiDict

from webargs import fields, ValidationError
from webargs.core import (
    Parser,
    dict2schema,
    is_json,
    get_mimetype,
    MARSHMALLOW_VERSION_INFO,
)
from webargs.multidictproxy import MultiDictProxy

try:
    # Python 3.5
    import mock
except ImportError:
    # Python 3.6+
    from unittest import mock


strict_kwargs = {"strict": True} if MARSHMALLOW_VERSION_INFO[0] < 3 else {}


class MockHTTPError(Exception):
    def __init__(self, status_code, headers):
        self.status_code = status_code
        self.headers = headers
        super().__init__(self, "HTTP Error occurred")


class MockRequestParser(Parser):
    """A minimal parser implementation that parses mock requests."""

    def load_querystring(self, req, schema):
        return MultiDictProxy(req.query, schema)

    def load_json(self, req, schema):
        return req.json

    def load_cookies(self, req, schema):
        return req.cookies


@pytest.yield_fixture(scope="function")
def web_request():
    req = mock.Mock()
    req.query = {}
    yield req
    req.query = {}


@pytest.fixture
def parser():
    return MockRequestParser()


# Parser tests


@mock.patch("webargs.core.Parser.load_json")
def test_load_json_called_by_parse_default(load_json, web_request):
    schema = dict2schema({"foo": fields.Field()})()
    load_json.return_value = {"foo": 1}
    p = Parser()
    p.parse(schema, web_request)
    load_json.assert_called_with(web_request, schema)


@pytest.mark.parametrize(
    "location", ["querystring", "form", "headers", "cookies", "files"]
)
def test_load_nondefault_called_by_parse_with_location(location, web_request):
    with mock.patch(
        "webargs.core.Parser.load_{}".format(location)
    ) as mock_loadfunc, mock.patch("webargs.core.Parser.load_json") as load_json:
        mock_loadfunc.return_value = {}
        load_json.return_value = {}
        p = Parser()

        # ensure that without location=..., the loader is not called (json is
        # called)
        p.parse({"foo": fields.Field()}, web_request)
        assert mock_loadfunc.call_count == 0
        assert load_json.call_count == 1

        # but when location=... is given, the loader *is* called and json is
        # not called
        p.parse({"foo": fields.Field()}, web_request, location=location)
        assert mock_loadfunc.call_count == 1
        # it was already 1, should not go up
        assert load_json.call_count == 1


def test_parse(parser, web_request):
    web_request.json = {"username": 42, "password": 42}
    argmap = {"username": fields.Field(), "password": fields.Field()}
    ret = parser.parse(argmap, web_request)
    assert {"username": 42, "password": 42} == ret


@pytest.mark.skipif(
    MARSHMALLOW_VERSION_INFO[0] < 3, reason="unknown=... added in marshmallow3"
)
def test_parse_with_unknown_behavior_specified(parser, web_request):
    # This is new in webargs 6.x ; it's the way you can "get back" the behavior
    # of webargs 5.x in which extra args are ignored
    from marshmallow import EXCLUDE, INCLUDE, RAISE

    web_request.json = {"username": 42, "password": 42, "fjords": 42}

    class CustomSchema(Schema):
        username = fields.Field()
        password = fields.Field()

    # with no unknown setting or unknown=RAISE, it blows up
    with pytest.raises(ValidationError, match="Unknown field."):
        parser.parse(CustomSchema(), web_request)
    with pytest.raises(ValidationError, match="Unknown field."):
        parser.parse(CustomSchema(unknown=RAISE), web_request)

    # with unknown=EXCLUDE the data is omitted
    ret = parser.parse(CustomSchema(unknown=EXCLUDE), web_request)
    assert {"username": 42, "password": 42} == ret
    # with unknown=INCLUDE it is added even though it isn't part of the schema
    ret = parser.parse(CustomSchema(unknown=INCLUDE), web_request)
    assert {"username": 42, "password": 42, "fjords": 42} == ret


def test_parse_required_arg_raises_validation_error(parser, web_request):
    web_request.json = {}
    args = {"foo": fields.Field(required=True)}
    with pytest.raises(ValidationError, match="Missing data for required field."):
        parser.parse(args, web_request)


def test_arg_not_required_excluded_in_parsed_output(parser, web_request):
    web_request.json = {"first": "Steve"}
    args = {"first": fields.Str(), "last": fields.Str()}
    result = parser.parse(args, web_request)
    assert result == {"first": "Steve"}


def test_arg_allow_none(parser, web_request):
    web_request.json = {"first": "Steve", "last": None}
    args = {"first": fields.Str(), "last": fields.Str(allow_none=True)}
    result = parser.parse(args, web_request)
    assert result == {"first": "Steve", "last": None}


def test_parse_required_arg(parser, web_request):
    web_request.json = {"foo": 42}
    result = parser.parse({"foo": fields.Field(required=True)}, web_request)
    assert result == {"foo": 42}


def test_parse_required_list(parser, web_request):
    web_request.json = {"bar": []}
    args = {"foo": fields.List(fields.Field(), required=True)}
    with pytest.raises(ValidationError) as excinfo:
        parser.parse(args, web_request)
    assert (
        excinfo.value.messages["json"]["foo"][0] == "Missing data for required field."
    )


# Regression test for https://github.com/marshmallow-code/webargs/issues/107
def test_parse_list_allow_none(parser, web_request):
    web_request.json = {"foo": None}
    args = {"foo": fields.List(fields.Field(allow_none=True), allow_none=True)}
    assert parser.parse(args, web_request) == {"foo": None}


def test_parse_list_dont_allow_none(parser, web_request):
    web_request.json = {"foo": None}
    args = {"foo": fields.List(fields.Field(), allow_none=False)}
    with pytest.raises(ValidationError) as excinfo:
        parser.parse(args, web_request)
    assert excinfo.value.messages["json"]["foo"][0] == "Field may not be null."


def test_parse_empty_list(parser, web_request):
    web_request.json = {"things": []}
    args = {"things": fields.List(fields.Field())}
    assert parser.parse(args, web_request) == {"things": []}


def test_parse_missing_list(parser, web_request):
    web_request.json = {}
    args = {"things": fields.List(fields.Field())}
    assert parser.parse(args, web_request) == {}


def test_default_location():
    assert Parser.DEFAULT_LOCATION == "json"


def test_missing_with_default(parser, web_request):
    web_request.json = {}
    args = {"val": fields.Field(missing="pizza")}
    result = parser.parse(args, web_request)
    assert result["val"] == "pizza"


def test_default_can_be_none(parser, web_request):
    web_request.json = {}
    args = {"val": fields.Field(missing=None, allow_none=True)}
    result = parser.parse(args, web_request)
    assert result["val"] is None


# Regression test for issue #11
def test_arg_with_default_and_location(parser, web_request):
    web_request.json = {}
    args = {
        "p": fields.Int(
            missing=1,
            validate=lambda p: p > 0,
            error="La page demandée n'existe pas",
            location="querystring",
        )
    }
    assert parser.parse(args, web_request) == {"p": 1}


def test_value_error_raised_if_parse_called_with_invalid_location(parser, web_request):
    field = fields.Field()
    with pytest.raises(ValueError, match="Invalid location argument: invalidlocation"):
        parser.parse({"foo": field}, web_request, location="invalidlocation")


@mock.patch("webargs.core.Parser.handle_error")
def test_handle_error_called_when_parsing_raises_error(handle_error, web_request):
    def always_fail(*args, **kwargs):
        raise ValidationError("error occurred")

    p = Parser()
    assert handle_error.call_count == 0
    p.parse({"foo": fields.Field()}, web_request, validate=always_fail)
    assert handle_error.call_count == 1
    p.parse({"foo": fields.Field()}, web_request, validate=always_fail)
    assert handle_error.call_count == 2


def test_handle_error_reraises_errors(web_request):
    p = Parser()
    with pytest.raises(ValidationError):
        p.handle_error(
            ValidationError("error raised"),
            web_request,
            Schema(),
            error_status_code=422,
            error_headers={},
        )


@mock.patch("webargs.core.Parser.load_headers")
def test_location_as_init_argument(load_headers, web_request):
    p = Parser(location="headers")
    load_headers.return_value = {}
    p.parse({"foo": fields.Field()}, web_request)
    assert load_headers.called


def test_custom_error_handler(web_request):
    class CustomError(Exception):
        pass

    def error_handler(error, req, schema, *, error_status_code, error_headers):
        assert isinstance(schema, Schema)
        raise CustomError(error)

    def failing_validate_func(args):
        raise ValidationError("parsing failed")

    class MySchema(Schema):
        foo = fields.Int()

    myschema = MySchema(**strict_kwargs)
    web_request.json = {"foo": "hello world"}

    p = Parser(error_handler=error_handler)
    with pytest.raises(CustomError):
        p.parse(myschema, web_request, validate=failing_validate_func)


def test_custom_error_handler_decorator(web_request):
    class CustomError(Exception):
        pass

    mock_schema = mock.Mock(spec=Schema)
    mock_schema.strict = True
    mock_schema.load.side_effect = ValidationError("parsing json failed")
    parser = Parser()

    @parser.error_handler
    def handle_error(error, req, schema, *, error_status_code, error_headers):
        assert isinstance(schema, Schema)
        raise CustomError(error)

    with pytest.raises(CustomError):
        parser.parse(mock_schema, web_request)


def test_custom_location_loader(web_request):
    web_request.data = {"foo": 42}

    parser = Parser()

    @parser.location_loader("data")
    def load_data(req, schema):
        return req.data

    result = parser.parse({"foo": fields.Int()}, web_request, location="data")
    assert result["foo"] == 42


def test_custom_location_loader_with_data_key(web_request):
    web_request.data = {"X-Foo": 42}
    parser = Parser()

    @parser.location_loader("data")
    def load_data(req, schema):
        return req.data

    data_key_kwarg = {
        "load_from" if (MARSHMALLOW_VERSION_INFO[0] < 3) else "data_key": "X-Foo"
    }
    result = parser.parse(
        {"x_foo": fields.Int(**data_key_kwarg)}, web_request, location="data"
    )
    assert result["x_foo"] == 42


def test_full_input_validation(parser, web_request):

    web_request.json = {"foo": 41, "bar": 42}

    args = {"foo": fields.Int(), "bar": fields.Int()}
    with pytest.raises(ValidationError):
        # Test that `validate` receives dictionary of args
        parser.parse(args, web_request, validate=lambda args: args["foo"] > args["bar"])


def test_full_input_validation_with_multiple_validators(web_request, parser):
    def validate1(args):
        if args["a"] > args["b"]:
            raise ValidationError("b must be > a")

    def validate2(args):
        if args["b"] > args["a"]:
            raise ValidationError("a must be > b")

    args = {"a": fields.Int(), "b": fields.Int()}
    web_request.json = {"a": 2, "b": 1}
    validators = [validate1, validate2]
    with pytest.raises(ValidationError, match="b must be > a"):
        parser.parse(args, web_request, validate=validators)

    web_request.json = {"a": 1, "b": 2}
    with pytest.raises(ValidationError, match="a must be > b"):
        parser.parse(args, web_request, validate=validators)


def test_required_with_custom_error(parser, web_request):
    web_request.json = {}
    args = {
        "foo": fields.Str(required=True, error_messages={"required": "We need foo"})
    }
    with pytest.raises(ValidationError) as excinfo:
        # Test that `validate` receives dictionary of args
        parser.parse(args, web_request)

    assert "We need foo" in excinfo.value.messages["json"]["foo"]
    if MARSHMALLOW_VERSION_INFO[0] < 3:
        assert "foo" in excinfo.value.field_names


def test_required_with_custom_error_and_validation_error(parser, web_request):
    web_request.json = {"foo": ""}
    args = {
        "foo": fields.Str(
            required="We need foo",
            validate=lambda s: len(s) > 1,
            error_messages={"validator_failed": "foo required length is 3"},
        )
    }
    with pytest.raises(ValidationError) as excinfo:
        # Test that `validate` receives dictionary of args
        parser.parse(args, web_request)

    assert "foo required length is 3" in excinfo.value.args[0]["foo"]
    if MARSHMALLOW_VERSION_INFO[0] < 3:
        assert "foo" in excinfo.value.field_names


def test_full_input_validator_receives_nonascii_input(web_request):
    def validate(val):
        return False

    text = "øœ∑∆∑"
    web_request.json = {"text": text}
    parser = MockRequestParser()
    args = {"text": fields.Str()}
    with pytest.raises(ValidationError) as excinfo:
        parser.parse(args, web_request, validate=validate)
    assert excinfo.value.messages == {"json": ["Invalid value."]}


def test_invalid_argument_for_validate(web_request, parser):
    with pytest.raises(ValueError) as excinfo:
        parser.parse({}, web_request, validate="notcallable")
    assert "not a callable or list of callables." in excinfo.value.args[0]


def create_bottle_multi_dict():
    d = BotMultiDict()
    d["foos"] = "a"
    d["foos"] = "b"
    return d


multidicts = [
    WerkMultiDict([("foos", "a"), ("foos", "b")]),
    create_bottle_multi_dict(),
    DjMultiDict({"foos": ["a", "b"]}),
]


@pytest.mark.parametrize("input_dict", multidicts)
def test_multidict_proxy(input_dict):
    class ListSchema(Schema):
        foos = fields.List(fields.Str())

    class StrSchema(Schema):
        foos = fields.Str()

    # this MultiDictProxy is aware that "foos" is a list field and will
    # therefore produce a list with __getitem__
    list_wrapped_multidict = MultiDictProxy(input_dict, ListSchema())

    # this MultiDictProxy is under the impression that "foos" is just a string
    # and it should return "a" or "b"
    # the decision between "a" and "b" in this case belongs to the framework
    str_wrapped_multidict = MultiDictProxy(input_dict, StrSchema())

    assert list_wrapped_multidict["foos"] == ["a", "b"]
    assert str_wrapped_multidict["foos"] in ("a", "b")


def test_parse_with_data_key(web_request):
    web_request.json = {"Content-Type": "application/json"}

    parser = MockRequestParser()
    data_key_kwargs = {
        "load_from" if (MARSHMALLOW_VERSION_INFO[0] < 3) else "data_key": "Content-Type"
    }
    args = {"content_type": fields.Field(**data_key_kwargs)}
    parsed = parser.parse(args, web_request)
    assert parsed == {"content_type": "application/json"}


# https://github.com/marshmallow-code/webargs/issues/118
@pytest.mark.skipif(
    MARSHMALLOW_VERSION_INFO[0] >= 3, reason="Behaviour changed in marshmallow 3"
)
# https://github.com/marshmallow-code/marshmallow/pull/714
def test_load_from_is_checked_after_given_key(web_request):
    web_request.json = {"content_type": "application/json"}

    parser = MockRequestParser()
    args = {"content_type": fields.Field(load_from="Content-Type")}
    parsed = parser.parse(args, web_request)
    assert parsed == {"content_type": "application/json"}


def test_parse_with_data_key_retains_field_name_in_error(web_request):
    web_request.json = {"Content-Type": 12345}

    parser = MockRequestParser()
    data_key_kwargs = {
        "load_from" if (MARSHMALLOW_VERSION_INFO[0] < 3) else "data_key": "Content-Type"
    }
    args = {"content_type": fields.Str(**data_key_kwargs)}
    with pytest.raises(ValidationError) as excinfo:
        parser.parse(args, web_request)
    assert "json" in excinfo.value.messages
    assert "Content-Type" in excinfo.value.messages["json"]
    assert excinfo.value.messages["json"]["Content-Type"] == ["Not a valid string."]


def test_parse_nested_with_data_key(web_request):
    parser = MockRequestParser()
    web_request.json = {"nested_arg": {"wrong": "OK"}}
    data_key_kwarg = {
        "load_from" if (MARSHMALLOW_VERSION_INFO[0] < 3) else "data_key": "wrong"
    }
    args = {"nested_arg": fields.Nested({"right": fields.Field(**data_key_kwarg)})}

    parsed = parser.parse(args, web_request)
    assert parsed == {"nested_arg": {"right": "OK"}}


def test_parse_nested_with_missing_key_and_data_key(web_request):
    parser = MockRequestParser()

    web_request.json = {"nested_arg": {}}
    data_key_kwargs = {
        "load_from" if (MARSHMALLOW_VERSION_INFO[0] < 3) else "data_key": "miss"
    }
    args = {
        "nested_arg": fields.Nested(
            {"found": fields.Field(missing=None, allow_none=True, **data_key_kwargs)}
        )
    }

    parsed = parser.parse(args, web_request)
    assert parsed == {"nested_arg": {"found": None}}


def test_parse_nested_with_default(web_request):
    parser = MockRequestParser()

    web_request.json = {"nested_arg": {}}
    args = {"nested_arg": fields.Nested({"miss": fields.Field(missing="<foo>")})}

    parsed = parser.parse(args, web_request)
    assert parsed == {"nested_arg": {"miss": "<foo>"}}


def test_nested_many(web_request, parser):
    web_request.json = {"pets": [{"name": "Pips"}, {"name": "Zula"}]}
    args = {"pets": fields.Nested({"name": fields.Str()}, required=True, many=True)}
    parsed = parser.parse(args, web_request)
    assert parsed == {"pets": [{"name": "Pips"}, {"name": "Zula"}]}
    web_request.json = {}
    with pytest.raises(ValidationError):
        parser.parse(args, web_request)


def test_use_args(web_request, parser):
    user_args = {"username": fields.Str(), "password": fields.Str()}
    web_request.json = {"username": "foo", "password": "bar"}

    @parser.use_args(user_args, web_request)
    def viewfunc(args):
        return args

    assert viewfunc() == {"username": "foo", "password": "bar"}


def test_use_args_stacked(web_request, parser):
    query_args = {"page": fields.Int()}
    json_args = {"username": fields.Str()}
    web_request.json = {"username": "foo"}
    web_request.query = {"page": 42}

    @parser.use_args(query_args, web_request, location="query")
    @parser.use_args(json_args, web_request)
    def viewfunc(query_parsed, json_parsed):
        return {"json": json_parsed, "query": query_parsed}

    assert viewfunc() == {"json": {"username": "foo"}, "query": {"page": 42}}


def test_use_kwargs_stacked(web_request, parser):
    query_args = {
        "page": fields.Int(error_messages={"invalid": "{input} not a valid integer"})
    }
    json_args = {"username": fields.Str()}
    web_request.json = {"username": "foo"}
    web_request.query = {"page": 42}

    @parser.use_kwargs(query_args, web_request, location="query")
    @parser.use_kwargs(json_args, web_request)
    def viewfunc(page, username):
        return {"json": {"username": username}, "query": {"page": page}}

    assert viewfunc() == {"json": {"username": "foo"}, "query": {"page": 42}}


@pytest.mark.parametrize("decorator_name", ["use_args", "use_kwargs"])
def test_decorators_dont_change_docstring(parser, decorator_name):
    decorator = getattr(parser, decorator_name)

    @decorator({"val": fields.Int()})
    def viewfunc(*args, **kwargs):
        """View docstring"""
        pass

    assert viewfunc.__doc__ == "View docstring"


def test_list_allowed_missing(web_request, parser):
    args = {"name": fields.List(fields.Str())}
    web_request.json = {}
    result = parser.parse(args, web_request)
    assert result == {}


def test_int_list_allowed_missing(web_request, parser):
    args = {"name": fields.List(fields.Int())}
    web_request.json = {}
    result = parser.parse(args, web_request)
    assert result == {}


def test_multiple_arg_required_with_int_conversion(web_request, parser):
    args = {"ids": fields.List(fields.Int(), required=True)}
    web_request.json = {}
    with pytest.raises(ValidationError) as excinfo:
        parser.parse(args, web_request)
    assert excinfo.value.messages == {
        "json": {"ids": ["Missing data for required field."]}
    }


def test_parse_with_callable(web_request, parser):

    web_request.json = {"foo": 42}

    class MySchema(Schema):
        foo = fields.Field()

        if MARSHMALLOW_VERSION_INFO[0] < 3:

            class Meta:
                strict = True

    def make_schema(req):
        assert req is web_request
        return MySchema(context={"request": req})

    result = parser.parse(make_schema, web_request)

    assert result == {"foo": 42}


def test_use_args_callable(web_request, parser):
    class HelloSchema(Schema):
        name = fields.Str()

        if MARSHMALLOW_VERSION_INFO[0] < 3:

            class Meta:
                strict = True

        @post_load
        def request_data(self, item, **kwargs):
            item["data"] = self.context["request"].data
            return item

    web_request.json = {"name": "foo"}
    web_request.data = "request-data"

    def make_schema(req):
        assert req is web_request
        return HelloSchema(context={"request": req})

    @parser.use_args(make_schema, web_request)
    def viewfunc(args):
        return args

    assert viewfunc() == {"name": "foo", "data": "request-data"}


class TestPassingSchema:
    class UserSchema(Schema):
        id = fields.Int(dump_only=True)
        email = fields.Email()
        password = fields.Str(load_only=True)
        if MARSHMALLOW_VERSION_INFO[0] < 3:

            class Meta:
                strict = True

    def test_passing_schema_to_parse(self, parser, web_request):
        web_request.json = {"email": "foo@bar.com", "password": "bar"}

        result = parser.parse(self.UserSchema(**strict_kwargs), web_request)

        assert result == {"email": "foo@bar.com", "password": "bar"}

    def test_use_args_can_be_passed_a_schema(self, web_request, parser):

        web_request.json = {"email": "foo@bar.com", "password": "bar"}

        @parser.use_args(self.UserSchema(**strict_kwargs), web_request)
        def viewfunc(args):
            return args

        assert viewfunc() == {"email": "foo@bar.com", "password": "bar"}

    def test_passing_schema_factory_to_parse(self, parser, web_request):
        web_request.json = {"email": "foo@bar.com", "password": "bar"}

        def factory(req):
            assert req is web_request
            return self.UserSchema(context={"request": req}, **strict_kwargs)

        result = parser.parse(factory, web_request)

        assert result == {"email": "foo@bar.com", "password": "bar"}

    def test_use_args_can_be_passed_a_schema_factory(self, web_request, parser):
        web_request.json = {"email": "foo@bar.com", "password": "bar"}

        def factory(req):
            assert req is web_request
            return self.UserSchema(context={"request": req}, **strict_kwargs)

        @parser.use_args(factory, web_request)
        def viewfunc(args):
            return args

        assert viewfunc() == {"email": "foo@bar.com", "password": "bar"}

    def test_use_kwargs_can_be_passed_a_schema(self, web_request, parser):

        web_request.json = {"email": "foo@bar.com", "password": "bar"}

        @parser.use_kwargs(self.UserSchema(**strict_kwargs), web_request)
        def viewfunc(email, password):
            return {"email": email, "password": password}

        assert viewfunc() == {"email": "foo@bar.com", "password": "bar"}

    def test_use_kwargs_can_be_passed_a_schema_factory(self, web_request, parser):
        web_request.json = {"email": "foo@bar.com", "password": "bar"}

        def factory(req):
            assert req is web_request
            return self.UserSchema(context={"request": req}, **strict_kwargs)

        @parser.use_kwargs(factory, web_request)
        def viewfunc(email, password):
            return {"email": email, "password": password}

        assert viewfunc() == {"email": "foo@bar.com", "password": "bar"}

    @pytest.mark.skipif(
        MARSHMALLOW_VERSION_INFO[0] >= 3,
        reason='"strict" parameter is removed in marshmallow 3',
    )
    def test_warning_raised_if_schema_is_not_in_strict_mode(self, web_request, parser):

        with pytest.warns(UserWarning) as record:
            parser.parse(self.UserSchema(strict=False), web_request)
        warning = record[0]
        assert "strict=True" in str(warning.message)

    def test_use_kwargs_stacked(self, web_request, parser):
        if MARSHMALLOW_VERSION_INFO[0] >= 3:
            from marshmallow import EXCLUDE

            class PageSchema(Schema):
                page = fields.Int()

            pageschema = PageSchema(unknown=EXCLUDE)
            userschema = self.UserSchema(unknown=EXCLUDE)
        else:
            pageschema = {"page": fields.Int()}
            userschema = self.UserSchema(**strict_kwargs)

        web_request.json = {"email": "foo@bar.com", "password": "bar", "page": 42}

        @parser.use_kwargs(pageschema, web_request)
        @parser.use_kwargs(userschema, web_request)
        def viewfunc(email, password, page):
            return {"email": email, "password": password, "page": page}

        assert viewfunc() == {"email": "foo@bar.com", "password": "bar", "page": 42}

    # Regression test for https://github.com/marshmallow-code/webargs/issues/146
    def test_parse_does_not_add_missing_values_to_schema_validator(
        self, web_request, parser
    ):
        class UserSchema(Schema):
            name = fields.Str()
            location = fields.Field(required=False)
            if MARSHMALLOW_VERSION_INFO[0] < 3:

                class Meta:
                    strict = True

            @validates_schema(pass_original=True)
            def validate_schema(self, data, original_data, **kwargs):
                assert "location" not in original_data
                return True

        web_request.json = {"name": "Eric Cartman"}
        res = parser.parse(UserSchema, web_request)
        assert res == {"name": "Eric Cartman"}


def test_use_args_with_custom_location_in_parser(web_request, parser):
    custom_args = {"foo": fields.Str()}
    web_request.json = {}
    parser.location = "custom"

    @parser.location_loader("custom")
    def load_custom(schema, req):
        return {"foo": "bar"}

    @parser.use_args(custom_args, web_request)
    def viewfunc(args):
        return args

    assert viewfunc() == {"foo": "bar"}


def test_use_kwargs(web_request, parser):
    user_args = {"username": fields.Str(), "password": fields.Str()}
    web_request.json = {"username": "foo", "password": "bar"}

    @parser.use_kwargs(user_args, web_request)
    def viewfunc(username, password):
        return {"username": username, "password": password}

    assert viewfunc() == {"username": "foo", "password": "bar"}


def test_use_kwargs_with_arg_missing(web_request, parser):
    user_args = {"username": fields.Str(required=True), "password": fields.Str()}
    web_request.json = {"username": "foo"}

    @parser.use_kwargs(user_args, web_request)
    def viewfunc(username, **kwargs):
        assert "password" not in kwargs
        return {"username": username}

    assert viewfunc() == {"username": "foo"}


def test_delimited_list_default_delimiter(web_request, parser):
    web_request.json = {"ids": "1,2,3"}
    schema_cls = dict2schema({"ids": fields.DelimitedList(fields.Int())})
    schema = schema_cls()

    parsed = parser.parse(schema, web_request)
    assert parsed["ids"] == [1, 2, 3]

    dumped = schema.dump(parsed)
    data = dumped.data if MARSHMALLOW_VERSION_INFO[0] < 3 else dumped
    assert data["ids"] == "1,2,3"


def test_delimited_list_as_string_v2(web_request, parser):
    web_request.json = {"dates": "2018-11-01,2018-11-02"}
    schema_cls = dict2schema(
        {"dates": fields.DelimitedList(fields.DateTime(format="%Y-%m-%d"))}
    )
    schema = schema_cls()

    parsed = parser.parse(schema, web_request)
    assert parsed["dates"] == [
        datetime.datetime(2018, 11, 1),
        datetime.datetime(2018, 11, 2),
    ]

    dumped = schema.dump(parsed)
    data = dumped.data if MARSHMALLOW_VERSION_INFO[0] < 3 else dumped
    assert data["dates"] == "2018-11-01,2018-11-02"


def test_delimited_list_custom_delimiter(web_request, parser):
    web_request.json = {"ids": "1|2|3"}
    schema_cls = dict2schema({"ids": fields.DelimitedList(fields.Int(), delimiter="|")})
    schema = schema_cls()

    parsed = parser.parse(schema, web_request)
    assert parsed["ids"] == [1, 2, 3]


def test_delimited_list_load_list_errors(web_request, parser):
    web_request.json = {"ids": [1, 2, 3]}
    schema_cls = dict2schema({"ids": fields.DelimitedList(fields.Int())})
    schema = schema_cls()

    with pytest.raises(ValidationError) as excinfo:
        parser.parse(schema, web_request)
    exc = excinfo.value
    assert isinstance(exc, ValidationError)
    errors = exc.args[0]
    assert errors["ids"] == ["Not a valid delimited list."]


# Regresion test for https://github.com/marshmallow-code/webargs/issues/149
def test_delimited_list_passed_invalid_type(web_request, parser):
    web_request.json = {"ids": 1}
    schema_cls = dict2schema({"ids": fields.DelimitedList(fields.Int())})
    schema = schema_cls()

    with pytest.raises(ValidationError) as excinfo:
        parser.parse(schema, web_request)
    assert excinfo.value.messages == {"json": {"ids": ["Not a valid delimited list."]}}


def test_missing_list_argument_not_in_parsed_result(web_request, parser):
    # arg missing in request
    web_request.json = {}
    args = {"ids": fields.List(fields.Int())}

    result = parser.parse(args, web_request)
    assert "ids" not in result


def test_type_conversion_with_multiple_required(web_request, parser):
    web_request.json = {}
    args = {"ids": fields.List(fields.Int(), required=True)}
    msg = "Missing data for required field."
    with pytest.raises(ValidationError, match=msg):
        parser.parse(args, web_request)


def test_validation_errors_in_validator_are_passed_to_handle_error(parser, web_request):
    def validate(value):
        raise ValidationError("Something went wrong.")

    args = {"name": fields.Field(validate=validate, location="json")}
    web_request.json = {"name": "invalid"}
    with pytest.raises(ValidationError) as excinfo:
        parser.parse(args, web_request)
    exc = excinfo.value
    assert isinstance(exc, ValidationError)
    errors = exc.args[0]
    assert errors["name"] == ["Something went wrong."]


def test_parse_basic(web_request, parser):
    web_request.json = {"foo": "42"}
    args = {"foo": fields.Int()}
    result = parser.parse(args, web_request)
    assert result == {"foo": 42}


def test_parse_raises_validation_error_if_data_invalid(web_request, parser):
    args = {"email": fields.Email()}
    web_request.json = {"email": "invalid"}
    with pytest.raises(ValidationError):
        parser.parse(args, web_request)


def test_dict2schema():
    data_key_kwargs = {
        "load_from" if (MARSHMALLOW_VERSION_INFO[0] < 3) else "data_key": "content-type"
    }
    argmap = {
        "id": fields.Int(required=True),
        "title": fields.Str(),
        "description": fields.Str(),
        "content_type": fields.Str(**data_key_kwargs),
    }

    schema_cls = dict2schema(argmap)
    assert issubclass(schema_cls, Schema)

    schema = schema_cls()

    for each in ["id", "title", "description", "content_type"]:
        assert each in schema.fields
    assert schema.fields["id"].required
    if MARSHMALLOW_VERSION_INFO[0] < 3:
        assert schema.opts.strict is True


# Regression test for https://github.com/marshmallow-code/webargs/issues/101
def test_dict2schema_doesnt_add_to_class_registry():
    old_n_entries = len(
        list(
            itertools.chain(
                [classes for _, classes in class_registry._registry.items()]
            )
        )
    )
    argmap = {"id": fields.Field()}
    dict2schema(argmap)
    dict2schema(argmap)
    new_n_entries = len(
        list(
            itertools.chain(
                [classes for _, classes in class_registry._registry.items()]
            )
        )
    )
    assert new_n_entries == old_n_entries


def test_dict2schema_with_nesting():
    argmap = {"nest": fields.Nested({"foo": fields.Field()})}
    schema_cls = dict2schema(argmap)
    assert issubclass(schema_cls, Schema)
    schema = schema_cls()
    assert "nest" in schema.fields
    assert type(schema.fields["nest"]) is fields.Nested
    assert "foo" in schema.fields["nest"].schema.fields


def test_is_json():
    assert is_json(None) is False
    assert is_json("application/json") is True
    assert is_json("application/xml") is False
    assert is_json("application/vnd.api+json") is True


def test_get_mimetype():
    assert get_mimetype("application/json") == "application/json"
    assert get_mimetype("application/json;charset=utf8") == "application/json"
    assert get_mimetype(None) is None


class MockRequestParserWithErrorHandler(MockRequestParser):
    def handle_error(self, error, req, schema, *, error_status_code, error_headers):
        assert isinstance(error, ValidationError)
        assert isinstance(schema, Schema)
        raise MockHTTPError(error_status_code, error_headers)


def test_parse_with_error_status_code_and_headers(web_request):
    parser = MockRequestParserWithErrorHandler()
    web_request.json = {"foo": 42}
    args = {"foo": fields.Field(validate=lambda x: False)}
    with pytest.raises(MockHTTPError) as excinfo:
        parser.parse(
            args, web_request, error_status_code=418, error_headers={"X-Foo": "bar"}
        )
    error = excinfo.value
    assert error.status_code == 418
    assert error.headers == {"X-Foo": "bar"}


@mock.patch("webargs.core.Parser.load_json")
def test_custom_schema_class(load_json, web_request):
    class CustomSchema(Schema):
        @pre_load
        def pre_load(self, data, **kwargs):
            data["value"] += " world"
            return data

    load_json.return_value = {"value": "hello"}
    argmap = {"value": fields.Str()}
    p = Parser(schema_class=CustomSchema)
    ret = p.parse(argmap, web_request)
    assert ret == {"value": "hello world"}


@mock.patch("webargs.core.Parser.load_json")
def test_custom_default_schema_class(load_json, web_request):
    class CustomSchema(Schema):
        @pre_load
        def pre_load(self, data, **kwargs):
            data["value"] += " world"
            return data

    class CustomParser(Parser):
        DEFAULT_SCHEMA_CLASS = CustomSchema

    load_json.return_value = {"value": "hello"}
    argmap = {"value": fields.Str()}
    p = CustomParser()
    ret = p.parse(argmap, web_request)
    assert ret == {"value": "hello world"}
