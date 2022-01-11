import collections
import datetime
import typing
from unittest import mock

import pytest
from marshmallow import (
    Schema,
    post_load,
    pre_load,
    validates_schema,
    EXCLUDE,
    INCLUDE,
    RAISE,
)
from werkzeug.datastructures import MultiDict as WerkMultiDict
from django.utils.datastructures import MultiValueDict as DjMultiDict
from bottle import MultiDict as BotMultiDict

from webargs import fields, ValidationError
from webargs.core import (
    Parser,
    is_json,
    get_mimetype,
)
from webargs.multidictproxy import MultiDictProxy


class MockHTTPError(Exception):
    def __init__(self, status_code, headers):
        self.status_code = status_code
        self.headers = headers
        super().__init__(self, "HTTP Error occurred")


class MockRequestParser(Parser):
    """A minimal parser implementation that parses mock requests."""

    def load_querystring(self, req, schema):
        return self._makeproxy(req.query, schema)

    def load_form(self, req, schema):
        return MultiDictProxy(req.form, schema)

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
    schema = Schema.from_dict({"foo": fields.Field()})()
    load_json.return_value = {"foo": 1}
    p = Parser()
    p.parse(schema, web_request)
    load_json.assert_called_with(web_request, schema)


@pytest.mark.parametrize(
    "location", ["querystring", "form", "headers", "cookies", "files"]
)
def test_load_nondefault_called_by_parse_with_location(location, web_request):
    with mock.patch(
        f"webargs.core.Parser.load_{location}"
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


@pytest.mark.parametrize(
    "set_location",
    [
        "schema_instance",
        "parse_call",
        "parser_default",
        "parser_class_default",
    ],
)
def test_parse_with_unknown_behavior_specified(parser, web_request, set_location):
    web_request.json = {"username": 42, "password": 42, "fjords": 42}

    class CustomSchema(Schema):
        username = fields.Field()
        password = fields.Field()

    def parse_with_desired_behavior(value):
        if set_location == "schema_instance":
            if value is not None:
                # pass 'unknown=None' to parse() in order to indicate that the
                # schema setting should be respected
                return parser.parse(
                    CustomSchema(unknown=value), web_request, unknown=None
                )
            else:
                return parser.parse(CustomSchema(), web_request)
        elif set_location == "parse_call":
            return parser.parse(CustomSchema(), web_request, unknown=value)
        elif set_location == "parser_default":
            parser.unknown = value
            return parser.parse(CustomSchema(), web_request)
        elif set_location == "parser_class_default":

            class CustomParser(MockRequestParser):
                DEFAULT_UNKNOWN_BY_LOCATION = {"json": value}

            return CustomParser().parse(CustomSchema(), web_request)
        else:
            raise NotImplementedError

    # with no unknown setting or unknown=RAISE, it blows up
    with pytest.raises(ValidationError, match="Unknown field."):
        parse_with_desired_behavior(None)
    with pytest.raises(ValidationError, match="Unknown field."):
        parse_with_desired_behavior(RAISE)

    # with unknown=EXCLUDE the data is omitted
    ret = parse_with_desired_behavior(EXCLUDE)
    assert {"username": 42, "password": 42} == ret
    # with unknown=INCLUDE it is added even though it isn't part of the schema
    ret = parse_with_desired_behavior(INCLUDE)
    assert {"username": 42, "password": 42, "fjords": 42} == ret


def test_parse_with_explicit_unknown_overrides_schema(parser, web_request):
    web_request.json = {"username": 42, "password": 42, "fjords": 42}

    class CustomSchema(Schema):
        username = fields.Field()
        password = fields.Field()

    # setting RAISE in the parse call overrides schema setting
    with pytest.raises(ValidationError, match="Unknown field."):
        parser.parse(CustomSchema(unknown=EXCLUDE), web_request, unknown=RAISE)
    with pytest.raises(ValidationError, match="Unknown field."):
        parser.parse(CustomSchema(unknown=INCLUDE), web_request, unknown=RAISE)

    # and the reverse -- setting EXCLUDE or INCLUDE in the parse call overrides
    # a schema with RAISE already set
    ret = parser.parse(CustomSchema(unknown=RAISE), web_request, unknown=EXCLUDE)
    assert {"username": 42, "password": 42} == ret
    ret = parser.parse(CustomSchema(unknown=RAISE), web_request, unknown=INCLUDE)
    assert {"username": 42, "password": 42, "fjords": 42} == ret


@pytest.mark.parametrize("clear_method", ["custom_class", "instance_setting", "both"])
def test_parse_with_default_unknown_cleared_uses_schema_value(
    parser, web_request, clear_method
):
    web_request.json = {"username": 42, "password": 42, "fjords": 42}

    class CustomSchema(Schema):
        username = fields.Field()
        password = fields.Field()

    if clear_method == "custom_class":

        class CustomParser(MockRequestParser):
            DEFAULT_UNKNOWN_BY_LOCATION = {}

        parser = CustomParser()
    elif clear_method == "instance_setting":
        parser = MockRequestParser(unknown=None)
    elif clear_method == "both":
        # setting things in multiple ways should not result in errors
        class CustomParser(MockRequestParser):
            DEFAULT_UNKNOWN_BY_LOCATION = {}

        parser = CustomParser(unknown=None)
    else:
        raise NotImplementedError

    with pytest.raises(ValidationError, match="Unknown field."):
        parser.parse(CustomSchema(), web_request)
    with pytest.raises(ValidationError, match="Unknown field."):
        parser.parse(CustomSchema(unknown=RAISE), web_request)

    ret = parser.parse(CustomSchema(unknown=EXCLUDE), web_request)
    assert {"username": 42, "password": 42} == ret
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
    # handle_error must raise an error to be valid
    handle_error.side_effect = ValidationError("parsing failed")

    def always_fail(*args, **kwargs):
        raise ValidationError("error occurred")

    p = Parser()
    assert handle_error.call_count == 0
    with pytest.raises(ValidationError):
        p.parse({"foo": fields.Field()}, web_request, validate=always_fail)
    assert handle_error.call_count == 1
    with pytest.raises(ValidationError):
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

    myschema = MySchema()
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


def test_custom_error_handler_must_reraise(web_request):
    class CustomError(Exception):
        pass

    mock_schema = mock.Mock(spec=Schema)
    mock_schema.strict = True
    mock_schema.load.side_effect = ValidationError("parsing json failed")
    parser = Parser()

    @parser.error_handler
    def handle_error(error, req, schema, *, error_status_code, error_headers):
        pass

    # because the handler above does not raise a new error, the parser should
    # raise a ValueError -- indicating a programming error
    with pytest.raises(ValueError):
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

    result = parser.parse(
        {"x_foo": fields.Int(data_key="X-Foo")}, web_request, location="data"
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
    args = {"content_type": fields.Field(data_key="Content-Type")}
    parsed = parser.parse(args, web_request)
    assert parsed == {"content_type": "application/json"}


def test_parse_with_data_key_retains_field_name_in_error(web_request):
    web_request.json = {"Content-Type": 12345}

    parser = MockRequestParser()
    args = {"content_type": fields.Str(data_key="Content-Type")}
    with pytest.raises(ValidationError) as excinfo:
        parser.parse(args, web_request)
    assert "json" in excinfo.value.messages
    assert "Content-Type" in excinfo.value.messages["json"]
    assert excinfo.value.messages["json"]["Content-Type"] == ["Not a valid string."]


def test_parse_nested_with_data_key(web_request):
    parser = MockRequestParser()
    web_request.json = {"nested_arg": {"wrong": "OK"}}
    args = {"nested_arg": fields.Nested({"right": fields.Field(data_key="wrong")})}

    parsed = parser.parse(args, web_request)
    assert parsed == {"nested_arg": {"right": "OK"}}


def test_parse_nested_with_missing_key_and_data_key(web_request):
    parser = MockRequestParser()

    web_request.json = {"nested_arg": {}}
    args = {
        "nested_arg": fields.Nested(
            {"found": fields.Field(missing=None, allow_none=True, data_key="miss")}
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

    def make_schema(req):
        assert req is web_request
        return MySchema(context={"request": req})

    result = parser.parse(make_schema, web_request)

    assert result == {"foo": 42}


def test_use_args_callable(web_request, parser):
    class HelloSchema(Schema):
        name = fields.Str()

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

    def test_passing_schema_to_parse(self, parser, web_request):
        web_request.json = {"email": "foo@bar.com", "password": "bar"}

        result = parser.parse(self.UserSchema(), web_request)

        assert result == {"email": "foo@bar.com", "password": "bar"}

    def test_use_args_can_be_passed_a_schema(self, web_request, parser):

        web_request.json = {"email": "foo@bar.com", "password": "bar"}

        @parser.use_args(self.UserSchema(), web_request)
        def viewfunc(args):
            return args

        assert viewfunc() == {"email": "foo@bar.com", "password": "bar"}

    def test_passing_schema_factory_to_parse(self, parser, web_request):
        web_request.json = {"email": "foo@bar.com", "password": "bar"}

        def factory(req):
            assert req is web_request
            return self.UserSchema(context={"request": req})

        result = parser.parse(factory, web_request)

        assert result == {"email": "foo@bar.com", "password": "bar"}

    def test_use_args_can_be_passed_a_schema_factory(self, web_request, parser):
        web_request.json = {"email": "foo@bar.com", "password": "bar"}

        def factory(req):
            assert req is web_request
            return self.UserSchema(context={"request": req})

        @parser.use_args(factory, web_request)
        def viewfunc(args):
            return args

        assert viewfunc() == {"email": "foo@bar.com", "password": "bar"}

    def test_use_kwargs_can_be_passed_a_schema(self, web_request, parser):

        web_request.json = {"email": "foo@bar.com", "password": "bar"}

        @parser.use_kwargs(self.UserSchema(), web_request)
        def viewfunc(email, password):
            return {"email": email, "password": password}

        assert viewfunc() == {"email": "foo@bar.com", "password": "bar"}

    def test_use_kwargs_can_be_passed_a_schema_factory(self, web_request, parser):
        web_request.json = {"email": "foo@bar.com", "password": "bar"}

        def factory(req):
            assert req is web_request
            return self.UserSchema(context={"request": req})

        @parser.use_kwargs(factory, web_request)
        def viewfunc(email, password):
            return {"email": email, "password": password}

        assert viewfunc() == {"email": "foo@bar.com", "password": "bar"}

    def test_use_kwargs_stacked(self, web_request, parser):
        web_request.json = {"email": "foo@bar.com", "password": "bar", "page": 42}

        @parser.use_kwargs({"page": fields.Int()}, web_request, unknown=EXCLUDE)
        @parser.use_kwargs(self.UserSchema(), web_request, unknown=EXCLUDE)
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


def test_delimited_list_empty_string(web_request, parser):
    web_request.json = {"dates": ""}
    schema_cls = Schema.from_dict({"dates": fields.DelimitedList(fields.Str())})
    schema = schema_cls()

    parsed = parser.parse(schema, web_request)
    assert parsed["dates"] == []

    data = schema.dump(parsed)
    assert data["dates"] == ""


def test_delimited_list_default_delimiter(web_request, parser):
    web_request.json = {"ids": "1,2,3"}
    schema_cls = Schema.from_dict({"ids": fields.DelimitedList(fields.Int())})
    schema = schema_cls()

    parsed = parser.parse(schema, web_request)
    assert parsed["ids"] == [1, 2, 3]

    data = schema.dump(parsed)
    assert data["ids"] == "1,2,3"


def test_delimited_tuple_default_delimiter(web_request, parser):
    """
    Test load and dump from DelimitedTuple, including the use of a datetime
    type (similar to a DelimitedList test below) which confirms that we aren't
    relying on __str__, but are properly de/serializing the included fields
    """
    web_request.json = {"ids": "1,2,2020-05-04"}
    schema_cls = Schema.from_dict(
        {
            "ids": fields.DelimitedTuple(
                (fields.Int, fields.Int, fields.DateTime(format="%Y-%m-%d"))
            )
        }
    )
    schema = schema_cls()

    parsed = parser.parse(schema, web_request)
    assert parsed["ids"] == (1, 2, datetime.datetime(2020, 5, 4))

    data = schema.dump(parsed)
    assert data["ids"] == "1,2,2020-05-04"


def test_delimited_tuple_incorrect_arity(web_request, parser):
    web_request.json = {"ids": "1,2"}
    schema_cls = Schema.from_dict(
        {"ids": fields.DelimitedTuple((fields.Int, fields.Int, fields.Int))}
    )
    schema = schema_cls()

    with pytest.raises(ValidationError):
        parser.parse(schema, web_request)


def test_delimited_list_with_datetime(web_request, parser):
    """
    Test that DelimitedList(DateTime(format=...)) correctly parses and dumps
    dates to and from strings -- indicates that we're doing proper
    serialization of values in dump() and not just relying on __str__ producing
    correct results
    """
    web_request.json = {"dates": "2018-11-01,2018-11-02"}
    schema_cls = Schema.from_dict(
        {"dates": fields.DelimitedList(fields.DateTime(format="%Y-%m-%d"))}
    )
    schema = schema_cls()

    parsed = parser.parse(schema, web_request)
    assert parsed["dates"] == [
        datetime.datetime(2018, 11, 1),
        datetime.datetime(2018, 11, 2),
    ]

    data = schema.dump(parsed)
    assert data["dates"] == "2018-11-01,2018-11-02"


def test_delimited_list_custom_delimiter(web_request, parser):
    web_request.json = {"ids": "1|2|3"}
    schema_cls = Schema.from_dict(
        {"ids": fields.DelimitedList(fields.Int(), delimiter="|")}
    )
    schema = schema_cls()

    parsed = parser.parse(schema, web_request)
    assert parsed["ids"] == [1, 2, 3]

    data = schema.dump(parsed)
    assert data["ids"] == "1|2|3"


def test_delimited_tuple_custom_delimiter(web_request, parser):
    web_request.json = {"ids": "1|2"}
    schema_cls = Schema.from_dict(
        {"ids": fields.DelimitedTuple((fields.Int, fields.Int), delimiter="|")}
    )
    schema = schema_cls()

    parsed = parser.parse(schema, web_request)
    assert parsed["ids"] == (1, 2)

    data = schema.dump(parsed)
    assert data["ids"] == "1|2"


def test_delimited_list_load_list_errors(web_request, parser):
    web_request.json = {"ids": [1, 2, 3]}
    schema_cls = Schema.from_dict({"ids": fields.DelimitedList(fields.Int())})
    schema = schema_cls()

    with pytest.raises(ValidationError) as excinfo:
        parser.parse(schema, web_request)
    exc = excinfo.value
    assert isinstance(exc, ValidationError)
    errors = exc.args[0]
    assert errors["ids"] == ["Not a valid delimited list."]


def test_delimited_tuple_load_list_errors(web_request, parser):
    web_request.json = {"ids": [1, 2]}
    schema_cls = Schema.from_dict(
        {"ids": fields.DelimitedTuple((fields.Int, fields.Int))}
    )
    schema = schema_cls()

    with pytest.raises(ValidationError) as excinfo:
        parser.parse(schema, web_request)
    exc = excinfo.value
    assert isinstance(exc, ValidationError)
    errors = exc.args[0]
    assert errors["ids"] == ["Not a valid delimited tuple."]


# Regresion test for https://github.com/marshmallow-code/webargs/issues/149
def test_delimited_list_passed_invalid_type(web_request, parser):
    web_request.json = {"ids": 1}
    schema_cls = Schema.from_dict({"ids": fields.DelimitedList(fields.Int())})
    schema = schema_cls()

    with pytest.raises(ValidationError) as excinfo:
        parser.parse(schema, web_request)
    assert excinfo.value.messages == {"json": {"ids": ["Not a valid delimited list."]}}


def test_delimited_tuple_passed_invalid_type(web_request, parser):
    web_request.json = {"ids": 1}
    schema_cls = Schema.from_dict({"ids": fields.DelimitedTuple((fields.Int,))})
    schema = schema_cls()

    with pytest.raises(ValidationError) as excinfo:
        parser.parse(schema, web_request)
    assert excinfo.value.messages == {"json": {"ids": ["Not a valid delimited tuple."]}}


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


@pytest.mark.parametrize("input_dict", multidicts)
@pytest.mark.parametrize(
    "setting",
    [
        "is_multiple_true",
        "is_multiple_false",
        "is_multiple_notset",
        "list_field",
        "tuple_field",
        "added_to_known",
    ],
)
def test_is_multiple_detection(web_request, parser, input_dict, setting):
    # this custom class "multiplexes" in that it can be given a single value or
    # list of values -- a single value is treated as a string, and a list of
    # values is treated as a list of strings
    class CustomMultiplexingField(fields.String):
        def _deserialize(self, value, attr, data, **kwargs):
            if isinstance(value, str):
                return super()._deserialize(value, attr, data, **kwargs)
            return [
                self._deserialize(v, attr, data, **kwargs)
                for v in value
                if isinstance(v, str)
            ]

        def _serialize(self, value, attr, **kwargs):
            if isinstance(value, str):
                return super()._serialize(value, attr, **kwargs)
            return [
                self._serialize(v, attr, **kwargs) for v in value if isinstance(v, str)
            ]

    class CustomMultipleField(CustomMultiplexingField):
        is_multiple = True

    class CustomNonMultipleField(CustomMultiplexingField):
        is_multiple = False

    # the request's query params are the input multidict
    web_request.query = input_dict

    # case 1: is_multiple=True
    if setting == "is_multiple_true":
        # the multidict should unpack to a list of strings
        #
        # order is not necessarily guaranteed by the multidict implementations, but
        # both values must be present
        args = {"foos": CustomMultipleField()}
        result = parser.parse(args, web_request, location="query")
        assert result["foos"] in (["a", "b"], ["b", "a"])
    # case 2: is_multiple=False
    elif setting == "is_multiple_false":
        # the multidict should unpack to a string
        #
        # either value may be returned, depending on the multidict implementation,
        # but not both
        args = {"foos": CustomNonMultipleField()}
        result = parser.parse(args, web_request, location="query")
        assert result["foos"] in ("a", "b")
    # case 3: is_multiple is not set
    elif setting == "is_multiple_notset":
        # this should be the same as is_multiple=False
        args = {"foos": CustomMultiplexingField()}
        result = parser.parse(args, web_request, location="query")
        assert result["foos"] in ("a", "b")
    # case 4: the field is a List (special case)
    elif setting == "list_field":
        # this should behave like the is_multiple=True case
        args = {"foos": fields.List(fields.Str())}
        result = parser.parse(args, web_request, location="query")
        assert result["foos"] in (["a", "b"], ["b", "a"])
    # case 5: the field is a Tuple (special case)
    elif setting == "tuple_field":
        # this should behave like the is_multiple=True case and produce a tuple
        args = {"foos": fields.Tuple((fields.Str, fields.Str))}
        result = parser.parse(args, web_request, location="query")
        assert result["foos"] in (("a", "b"), ("b", "a"))
    # case 6: the field is custom, but added to the known fields of the parser
    elif setting == "added_to_known":
        # if it's included in the known multifields and is_multiple is not set, behave
        # like is_multiple=True
        parser.KNOWN_MULTI_FIELDS.append(CustomMultiplexingField)
        args = {"foos": CustomMultiplexingField()}
        result = parser.parse(args, web_request, location="query")
        assert result["foos"] in (["a", "b"], ["b", "a"])
    else:
        raise NotImplementedError


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


def test_nested_field_from_dict():
    # webargs.fields.Nested implements dict handling
    argmap = {"nest": fields.Nested({"foo": fields.Field()})}
    schema_cls = Schema.from_dict(argmap)
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


def test_parser_pre_load(web_request):
    class CustomParser(MockRequestParser):
        # pre-load hook to strip whitespace from query params
        def pre_load(self, data, *, schema, req, location):
            if location == "query":
                return {k: v.strip() for k, v in data.items()}
            return data

    parser = CustomParser()

    # mock data for both query and json
    web_request.query = web_request.json = {"value": " hello "}
    argmap = {"value": fields.Str()}

    # data gets through for 'json' just fine
    ret = parser.parse(argmap, web_request)
    assert ret == {"value": " hello "}

    # but for 'query', the pre_load hook changes things
    ret = parser.parse(argmap, web_request, location="query")
    assert ret == {"value": "hello"}


# this test is meant to be a run of the WhitspaceStrippingFlaskParser we give
# in the docs/advanced.rst examples for how to use pre_load
# this helps ensure that the example code is correct
# rather than a FlaskParser, we're working with the mock parser, but it's
# otherwise the same
def test_whitespace_stripping_parser_example(web_request):
    def _strip_whitespace(value):
        if isinstance(value, str):
            value = value.strip()
        elif isinstance(value, typing.Mapping):
            return {k: _strip_whitespace(value[k]) for k in value}
        elif isinstance(value, (list, tuple)):
            return type(value)(map(_strip_whitespace, value))
        return value

    class WhitspaceStrippingParser(MockRequestParser):
        def pre_load(self, location_data, *, schema, req, location):
            if location in ("query", "form"):
                ret = _strip_whitespace(location_data)
                return ret
            return location_data

    parser = WhitspaceStrippingParser()

    # mock data for query, form, and json
    web_request.form = web_request.query = web_request.json = {"value": " hello "}
    argmap = {"value": fields.Str()}

    # data gets through for 'json' just fine
    ret = parser.parse(argmap, web_request)
    assert ret == {"value": " hello "}

    # but for 'query' and 'form', the pre_load hook changes things
    for loc in ("query", "form"):
        ret = parser.parse(argmap, web_request, location=loc)
        assert ret == {"value": "hello"}

    # check that it applies in the case where the field is a list type
    # applied to an argument (logic for `tuple` is effectively the same)
    web_request.form = web_request.query = web_request.json = {
        "ids": [" 1", "3", " 4"],
        "values": [" foo  ", " bar"],
    }
    schema = Schema.from_dict(
        {"ids": fields.List(fields.Int), "values": fields.List(fields.Str)}
    )
    for loc in ("query", "form"):
        ret = parser.parse(schema, web_request, location=loc)
        assert ret == {"ids": [1, 3, 4], "values": ["foo", "bar"]}

    # json loading should also work even though the pre_load hook above
    # doesn't strip whitespace from JSON data
    #   - values=[" foo  ", ...]  will have whitespace preserved
    #   - ids=[" 1", ...]  will still parse okay because "  1" is valid for fields.Int
    ret = parser.parse(schema, web_request, location="json")
    assert ret == {"ids": [1, 3, 4], "values": [" foo  ", " bar"]}


def test_parse_rejects_non_dict_argmap_mapping(parser, web_request):
    web_request.json = {"username": 42, "password": 42}
    argmap = collections.UserDict(
        {"username": fields.Field(), "password": fields.Field()}
    )

    # UserDict is dict-like in all meaningful ways, but not a subclass of `dict`
    # it will therefore be rejected with a TypeError when used
    with pytest.raises(TypeError):
        parser.parse(argmap, web_request)
