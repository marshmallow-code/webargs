# -*- coding: utf-8 -*-
import mock
import sys

import pytest
from marshmallow import Schema, post_load
from werkzeug.datastructures import MultiDict as WerkMultiDict

PY26 = sys.version_info[0] == 2 and int(sys.version_info[1]) < 7
if not PY26:  # django does not support python 2.6
    from django.utils.datastructures import MultiValueDict as DjMultiDict
from bottle import MultiDict as BotMultiDict

from webargs import (
    fields,
    missing,
    ValidationError,
)
from webargs.core import Parser, get_value, argmap2schema, is_json, get_mimetype


class MockRequestParser(Parser):
    """A minimal parser implementation that parses mock requests."""

    def parse_json(self, web_request, name, arg):
        return get_value(web_request.json, name, arg)

    def parse_cookies(self, web_request, name, arg):
        return get_value(web_request.cookies, name, arg)


@pytest.fixture
def web_request():
    return mock.Mock()

@pytest.fixture
def parser():
    return MockRequestParser()

# Parser tests

@mock.patch('webargs.core.Parser.parse_json')
def test_parse_json_called_by_parse_arg(parse_json, web_request):
    field = fields.Field()
    p = Parser()
    p.parse_arg('foo', field, web_request)
    parse_json.assert_called_with(web_request, 'foo', field)

@mock.patch('webargs.core.Parser.parse_querystring')
def test_parse_querystring_called_by_parse_arg(parse_querystring, web_request):
    field = fields.Field()
    p = Parser()
    p.parse_arg('foo', field, web_request)
    assert parse_querystring.called_once()

@mock.patch('webargs.core.Parser.parse_form')
def test_parse_form_called_by_parse_arg(parse_form, web_request):
    field = fields.Field()
    p = Parser()
    p.parse_arg('foo', field, web_request)
    assert parse_form.called_once()

@mock.patch('webargs.core.Parser.parse_json')
def test_parse_json_not_called_when_json_not_a_location(parse_json, web_request):
    field = fields.Field()
    p = Parser()
    p.parse_arg('foo', field, web_request, locations=('form', 'querystring'))
    assert parse_json.call_count == 0

@mock.patch('webargs.core.Parser.parse_headers')
def test_parse_headers_called_when_headers_is_a_location(parse_headers, web_request):
    field = fields.Field()
    p = Parser()
    p.parse_arg('foo', field, web_request)
    assert parse_headers.call_count == 0
    p.parse_arg('foo', field, web_request, locations=('headers',))
    parse_headers.assert_called()

@mock.patch('webargs.core.Parser.parse_cookies')
def test_parse_cookies_called_when_cookies_is_a_location(parse_cookies, web_request):
    field = fields.Field()
    p = Parser()
    p.parse_arg('foo', field, web_request)
    assert parse_cookies.call_count == 0
    p.parse_arg('foo', field, web_request, locations=('cookies',))
    parse_cookies.assert_called()

@mock.patch('webargs.core.Parser.parse_json')
def test_parse(parse_json, web_request):
    parse_json.return_value = 42
    argmap = {
        'username': fields.Field(),
        'password': fields.Field(),
    }
    p = Parser()
    ret = p.parse(argmap, web_request)
    assert {'username': 42, 'password': 42} == ret

def test_parse_required_arg_raises_validation_error(parser, web_request):
    web_request.json = {}
    args = {'foo': fields.Field(required=True)}
    with pytest.raises(ValidationError) as excinfo:
        parser.parse(args, web_request)
    assert 'Missing data for required field.' in str(excinfo)

@mock.patch('webargs.core.Parser.parse_json')
def test_parse_required_arg(parse_json, web_request):
    arg = fields.Field(required=True)
    parse_json.return_value = 42
    p = Parser()
    result = p.parse_arg('foo', arg, web_request, locations=('json', ))
    assert result == 42

def test_parse_required_list(parser, web_request):
    web_request.json = {'bar': []}
    args = {'foo': fields.List(fields.Field(), required=True)}
    with pytest.raises(ValidationError) as excinfo:
        parser.parse(args, web_request)
    assert excinfo.value.messages['foo'][0] == 'Missing data for required field.'

def test_parse_empty_list(parser, web_request):
    web_request.json = {'things': []}
    args = {'things': fields.List(fields.Field())}
    assert parser.parse(args, web_request) == {'things': []}

def test_parse_missing_list(parser, web_request):
    web_request.json = {}
    args = {'things': fields.List(fields.Field())}
    assert parser.parse(args, web_request) == {}

def test_default_locations():
    assert set(Parser.DEFAULT_LOCATIONS) == set(['json', 'querystring', 'form'])


def test_missing_with_default(parser, web_request):
    web_request.json = {}
    args = {'val': fields.Field(missing='pizza')}
    result = parser.parse(args, web_request, locations=('json', ))
    assert result['val'] == 'pizza'


def test_default_can_be_none(parser, web_request):
    web_request.json = {}
    args = {'val': fields.Field(missing=None, allow_none=True)}
    result = parser.parse(args, web_request, locations=('json', ))
    assert result['val'] is None


def test_value_error_raised_if_parse_arg_called_with_invalid_location(web_request):
    field = fields.Field()
    p = Parser()
    with pytest.raises(ValueError) as excinfo:
        p.parse_arg('foo', field, web_request, locations=('invalidlocation', 'headers'))
    assert 'Invalid locations arguments: {0}'.format(['invalidlocation']) in str(excinfo)

def test_value_error_raised_if_invalid_location_on_field(web_request, parser):
    with pytest.raises(ValueError) as excinfo:
        parser.parse({'foo': fields.Field(location='invalidlocation')}, web_request)
    assert 'Invalid locations arguments: {0}'.format(['invalidlocation']) in str(excinfo)

@mock.patch('webargs.core.Parser.handle_error')
@mock.patch('webargs.core.Parser.parse_json')
def test_handle_error_called_when_parsing_raises_error(parse_json, handle_error, web_request):
    val_err = ValidationError('error occurred')
    parse_json.side_effect = val_err
    p = Parser()
    p.parse({'foo': fields.Field()}, web_request, locations=('json',))
    handle_error.assert_called
    parse_json.side_effect = ValidationError('another exception')
    p.parse({'foo': fields.Field()}, web_request, locations=('json',))
    assert handle_error.call_count == 2

def test_handle_error_reraises_errors():
    p = Parser()
    with pytest.raises(ValidationError):
        p.handle_error(ValidationError('error raised'))

@mock.patch('webargs.core.Parser.parse_headers')
def test_locations_as_init_arguments(parse_headers, web_request):
    p = Parser(locations=('headers',))
    p.parse({'foo': fields.Field()}, web_request)
    assert parse_headers.called

@mock.patch('webargs.core.Parser.parse_files')
def test_parse_files(parse_files, web_request):
    p = Parser()
    p.parse({'foo': fields.Field()}, web_request, locations=('files',))
    assert parse_files.called

@mock.patch('webargs.core.Parser.parse_json')
def test_custom_error_handler(parse_json, web_request):
    class CustomError(Exception):
        pass

    def error_handler(error):
        raise CustomError(error)
    parse_json.side_effect = ValidationError('parse_json failed')
    p = Parser(error_handler=error_handler)
    with pytest.raises(CustomError):
        p.parse({'foo': fields.Field()}, web_request)


@mock.patch('webargs.core.Parser.parse_json')
def test_custom_error_handler_decorator(parse_json, web_request):
    class CustomError(Exception):
        pass
    parse_json.side_effect = ValidationError('parse_json failed')

    parser = Parser()

    @parser.error_handler
    def handle_error(error):
        raise CustomError(error)

    with pytest.raises(CustomError):
        parser.parse({'foo': fields.Field()}, web_request)


def test_custom_location_handler(web_request):
    web_request.data = {'foo': 42}

    parser = Parser()

    @parser.location_handler('data')
    def parse_data(req, name, arg):
        return req.data.get(name)

    result = parser.parse({'foo': fields.Int()}, web_request, locations=('data', ))
    assert result['foo'] == 42

def test_custom_location_handler_with_load_from(web_request):
    web_request.data = {'X-Foo': 42}
    parser = Parser()

    @parser.location_handler('data')
    def parse_data(req, name, arg):
        assert name == 'X-Foo'
        return req.data.get(name)

    result = parser.parse({'x_foo': fields.Int(load_from='X-Foo')},
        web_request, locations=('data', ))
    assert result['x_foo'] == 42

def test_full_input_validation(web_request):

    web_request.json = {'foo': 41, 'bar': 42}

    parser = MockRequestParser()
    args = {'foo': fields.Int(), 'bar': fields.Int()}
    with pytest.raises(ValidationError):
        # Test that `validate` receives dictionary of args
        parser.parse(args, web_request, locations=('json', ),
                     validate=lambda args: args['foo'] > args['bar'])

def test_full_input_validation_with_multiple_validators(web_request, parser):
    def validate1(args):
        if args['a'] > args['b']:
            raise ValidationError('b must be > a')

    def validate2(args):
        if args['b'] > args['a']:
            raise ValidationError('a must be > b')

    args = {'a': fields.Int(), 'b': fields.Int()}
    web_request.json = {'a': 2, 'b': 1}
    validators = [validate1, validate2]
    with pytest.raises(ValidationError) as excinfo:
        parser.parse(args, web_request, locations=('json', ),
                validate=validators)
    assert 'b must be > a' in str(excinfo)

    web_request.json = {'a': 1, 'b': 2}
    with pytest.raises(ValidationError) as excinfo:
        parser.parse(args, web_request, locations=('json', ),
                validate=validators)
    assert 'a must be > b' in str(excinfo)

def test_required_with_custom_error(web_request):
    web_request.json = {}
    parser = MockRequestParser()
    args = {'foo': fields.Str(
        required=True,
        error_messages={'required': 'We need foo'})
    }
    with pytest.raises(ValidationError) as excinfo:
        # Test that `validate` receives dictionary of args
        parser.parse(args, web_request, locations=('json', ))

    assert 'We need foo' in excinfo.value.messages['foo']
    assert 'foo' in excinfo.value.field_names

def test_required_with_custom_error_and_validation_error(web_request):
    web_request.json = {'foo': ''}
    parser = MockRequestParser()
    args = {'foo': fields.Str(required='We need foo', validate=lambda s: len(s) > 1,
        error_messages={'validator_failed': 'foo required length is 3'})}
    with pytest.raises(ValidationError) as excinfo:
        # Test that `validate` receives dictionary of args
        parser.parse(args, web_request, locations=('json', ))

    assert 'foo required length is 3' in excinfo.value.args[0]['foo']
    assert 'foo' in excinfo.value.field_names

def test_full_input_validator_receives_nonascii_input(web_request):
    def validate(val):
        return False
    text = u'øœ∑∆∑'
    web_request.json = {'text': text}
    parser = MockRequestParser()
    args = {'text': fields.Str()}
    with pytest.raises(ValidationError) as excinfo:
        parser.parse(args, web_request, locations=('json', ), validate=validate)
    assert excinfo.value.messages == ['Invalid value.']

def test_invalid_argument_for_validate(web_request, parser):
    with pytest.raises(ValueError) as excinfo:
        parser.parse({}, web_request, validate='notcallable')
    assert 'not a callable or list of callables.' in excinfo.value.args[0]

def test_get_value_basic():
    assert get_value({'foo': 42}, 'foo', False) == 42
    assert get_value({'foo': 42}, 'bar', False) is missing
    assert get_value({'foos': ['a', 'b']}, 'foos', True) == ['a', 'b']
    # https://github.com/sloria/webargs/pull/30
    assert get_value({'foos': ['a', 'b']}, 'bar', True) is missing


def create_bottle_multi_dict():
    d = BotMultiDict()
    d['foos'] = 'a'
    d['foos'] = 'b'
    return d

multidicts = [
    WerkMultiDict([('foos', 'a'), ('foos', 'b')]),
    create_bottle_multi_dict(),
]
if not PY26:
    multidicts.append(DjMultiDict({'foos': ['a', 'b']}))
@pytest.mark.parametrize('input_dict', multidicts)
def test_get_value_multidict(input_dict):
    field = fields.List(fields.Str())
    assert get_value(input_dict, 'foos', field) == ['a', 'b']

def test_parse_with_load_from(web_request):
    web_request.json = {'Content-Type': 'application/json'}

    parser = MockRequestParser()
    args = {'content_type': fields.Field(load_from='Content-Type')}
    parsed = parser.parse(args, web_request, locations=('json',))
    assert parsed == {'content_type': 'application/json'}


def test_parse_with_force_all(web_request, parser):
    web_request.json = {'foo': 42}

    args = {'foo': fields.Int(), 'bar': fields.Int(required=False)}

    parsed = parser.parse(args, web_request, force_all=True)
    assert parsed['foo'] == 42
    assert parsed['bar'] is missing

def test_parse_nested_with_load_from(web_request):
    parser = MockRequestParser()
    web_request.json = {
        'nested_arg': {'wrong': 'OK'}
    }
    args = {
        'nested_arg': fields.Nested({'right': fields.Field(load_from='wrong')})
    }

    parsed = parser.parse(args, web_request, locations=('json',))
    assert parsed == {
        'nested_arg': {'right': 'OK'}
    }

def test_parse_nested_with_missing_key_and_load_from(web_request):
    parser = MockRequestParser()

    web_request.json = {
        'nested_arg': {
            'payload': 'OK'
        }
    }
    args = {
        'nested_arg': fields.Nested({
            'found': fields.Field(missing=None, allow_none=True, load_from='miss')
        })
    }

    parsed = parser.parse(args, web_request, locations=('json',))
    assert parsed == {
        'nested_arg': {
            'found': None
        }
    }

def test_parse_nested_with_default(web_request):
    parser = MockRequestParser()

    web_request.json = {'nested_arg': {}}
    args = {
        'nested_arg': fields.Nested({
            'miss': fields.Field(missing='<foo>')
        })
    }

    parsed = parser.parse(args, web_request, locations=('json',))
    assert parsed == {
        'nested_arg': {'miss': '<foo>'}
    }

def test_nested_many(web_request, parser):
    web_request.json = {
        'pets': [
            {'name': 'Pips'},
            {'name': 'Zula'}
        ]
    }
    args = {
        'pets': fields.Nested({'name': fields.Str()}, required=True, many=True)
    }
    parsed = parser.parse(args, web_request)
    assert parsed == {
        'pets': [
            {'name': 'Pips'},
            {'name': 'Zula'}
        ]
    }
    web_request.json = {}
    with pytest.raises(ValidationError):
        parser.parse(args, web_request)

def test_use_args(web_request, parser):
    user_args = {
        'username': fields.Str(),
        'password': fields.Str(),
    }
    web_request.json = {'username': 'foo', 'password': 'bar'}

    @parser.use_args(user_args, web_request)
    def viewfunc(args):
        return args
    assert viewfunc() == {'username': 'foo', 'password': 'bar'}


def test_parse_with_callable(web_request, parser):

    web_request.json = {'foo': 42}

    class MySchema(Schema):
        foo = fields.Field()

    def make_schema(req):
        assert req is web_request
        return MySchema(context={'request': req})

    result = parser.parse(make_schema, web_request)

    assert result == {'foo': 42}


def test_use_args_callable(web_request, parser):
    class HelloSchema(Schema):
        name = fields.Str()

        class Meta(object):
            strict = True

        @post_load
        def request_data(self, item):
            item['data'] = self.context['request'].data
            return item

    web_request.json = {'name': 'foo'}
    web_request.data = 'request-data'

    def make_schema(req):
        assert req is web_request
        return HelloSchema(context={'request': req})

    @parser.use_args(
        make_schema,
        web_request,
    )
    def viewfunc(args):
        return args
    assert viewfunc() == {'name': 'foo', 'data': 'request-data'}


class TestPassingSchema:
    class UserSchema(Schema):
        id = fields.Int(dump_only=True)
        email = fields.Email()
        password = fields.Str(load_only=True)

    def test_passing_schema_to_parse(self, parser, web_request):
        web_request.json = {'id': 12, 'email': 'foo@bar.com', 'password': 'bar'}

        result = parser.parse(self.UserSchema(strict=True), web_request)

        assert result == {'email': 'foo@bar.com', 'password': 'bar'}

    def test_use_args_can_be_passed_a_schema(self, web_request, parser):

        web_request.json = {'id': 12, 'email': 'foo@bar.com', 'password': 'bar'}

        @parser.use_args(self.UserSchema(strict=True), web_request)
        def viewfunc(args):
            return args
        assert viewfunc() == {'email': 'foo@bar.com', 'password': 'bar'}

    def test_use_kwargs_can_be_passed_a_schema(self, web_request, parser):

        web_request.json = {'id': 12, 'email': 'foo@bar.com', 'password': 'bar'}

        @parser.use_kwargs(self.UserSchema(strict=True), web_request)
        def viewfunc(email, password):
            return {'email': email, 'password': password}
        assert viewfunc() == {'email': 'foo@bar.com', 'password': 'bar'}

    # Must skip on older versions of python due to
    # https://github.com/pytest-dev/pytest/issues/840
    @pytest.mark.skipif(sys.version_info < (3, 4),
                        reason="Skipping due to a bug in pytest's warning recording")
    def test_warning_raised_if_schema_is_not_in_strict_mode(
        self, web_request, parser
    ):

        with pytest.warns(UserWarning) as record:
            parser.parse(self.UserSchema(strict=False), web_request)
        warning = record[0]
        assert 'strict=True' in str(warning.message)

    def test_use_kwargs_stacked(self, web_request, parser):
        web_request.json = {
            'id': 12, 'email': 'foo@bar.com', 'password': 'bar',
            'page': 42,
        }

        @parser.use_kwargs({'page': fields.Int()}, web_request)
        @parser.use_kwargs(self.UserSchema(strict=True), web_request)
        def viewfunc(email, password, page):
            return {'email': email, 'password': password, 'page': page}
        assert viewfunc() == {'email': 'foo@bar.com', 'password': 'bar', 'page': 42}

    def test_error_handler_is_called_when_regardless_of_schema_strict_setting(self,
            web_request, parser):

        class UserSchema(Schema):
            email = fields.Email()

        web_request.json = {'email': 'invalid'}

        class CustomError(Exception):
            pass

        @parser.error_handler
        def handle_error(error):
            raise CustomError(error.messages)

        @parser.use_args(UserSchema(strict=True), web_request)
        def viewfunc(args):
            return args

        @parser.use_args(UserSchema(), web_request)
        def viewfunc2(args):
            return args

        with pytest.raises(CustomError) as excinfo:
            viewfunc()
        assert excinfo.value.args[0] == {'email': ['Not a valid email address.']}

        with pytest.raises(CustomError) as excinfo:
            viewfunc()
        assert excinfo.value.args[0] == {'email': ['Not a valid email address.']}


def test_use_args_with_custom_locations_in_parser(web_request, parser):
    custom_args = {
        'foo': fields.Str(),
    }
    web_request.json = {}
    parser.locations = ('custom',)

    @parser.location_handler('custom')
    def parse_custom(req, name, arg):
        return "bar"

    @parser.use_args(custom_args, web_request)
    def viewfunc(args):
        return args
    assert viewfunc() == {'foo': "bar"}

def test_use_kwargs(web_request, parser):
    user_args = {
        'username': fields.Str(),
        'password': fields.Str(),
    }
    web_request.json = {'username': 'foo', 'password': 'bar'}

    @parser.use_kwargs(user_args, web_request)
    def viewfunc(username, password):
        return {'username': username, 'password': password}
    assert viewfunc() == {'username': 'foo', 'password': 'bar'}


def test_use_kwargs_with_arg_missing(web_request, parser):
    user_args = {
        'username': fields.Str(),
        'password': fields.Str(),
    }
    web_request.json = {'username': 'foo'}

    @parser.use_kwargs(user_args, web_request)
    def viewfunc(username, password):
        return {'username': username, 'password': password}
    assert viewfunc() == {'username': 'foo', 'password': missing}

def test_delimited_list_default_delimiter(web_request, parser):
    web_request.json = {'ids': '1,2,3'}
    schema_cls = argmap2schema({'ids': fields.DelimitedList(fields.Int())})
    schema = schema_cls()

    parsed = parser.parse(schema, web_request)
    assert parsed['ids'] == [1, 2, 3]

    dumped = schema.dump(parsed).data
    assert dumped['ids'] == [1, 2, 3]

def test_delimited_list_as_string(web_request, parser):
    web_request.json = {'ids': '1,2,3'}
    schema_cls = argmap2schema({'ids': fields.DelimitedList(fields.Int(), as_string=True)})
    schema = schema_cls()

    parsed = parser.parse(schema, web_request)
    assert parsed['ids'] == [1, 2, 3]

    dumped = schema.dump(parsed).data
    assert dumped['ids'] == '1,2,3'

def test_delimited_list_custom_delimiter(web_request, parser):
    web_request.json = {'ids': '1|2|3'}
    schema_cls = argmap2schema({'ids': fields.DelimitedList(fields.Int(), delimiter='|')})
    schema = schema_cls()

    parsed = parser.parse(schema, web_request)
    assert parsed['ids'] == [1, 2, 3]

def test_delimited_list_load_list(web_request, parser):
    web_request.json = {'ids': [1, 2, 3]}
    schema_cls = argmap2schema({'ids': fields.DelimitedList(fields.Int())})
    schema = schema_cls()

    parsed = parser.parse(schema, web_request)
    assert parsed['ids'] == [1, 2, 3]

def test_missing_list_argument_not_in_parsed_result(web_request, parser):
    # arg missing in request
    web_request.json = {}
    args = {'ids': fields.List(fields.Int())}

    result = parser.parse(args, web_request)
    assert 'ids' not in result

def test_type_conversion_with_multiple_required(web_request, parser):
    web_request.json = {}
    args = {'ids': fields.List(fields.Int(), required=True)}
    with pytest.raises(ValidationError) as excinfo:
        parser.parse(args, web_request)
    assert 'Missing data for required field.' in str(excinfo)


def test_arg_location_param(web_request, parser):
    web_request.json = {'foo': 24}
    web_request.cookies = {'foo': 42}
    args = {'foo': fields.Field(location='cookies')}

    parsed = parser.parse(args, web_request)

    assert parsed['foo'] == 42

def test_validation_errors_in_validator_are_passed_to_handle_error(parser, web_request):
    def validate(value):
        raise ValidationError('Something went wrong.')
    args = {
        'name': fields.Field(validate=validate, location='json')
    }
    web_request.json = {'name': 'invalid'}
    with pytest.raises(ValidationError) as excinfo:
        parser.parse(args, web_request)
    exc = excinfo.value
    assert isinstance(exc, ValidationError)
    errors = exc.args[0]
    assert errors['name'] == ['Something went wrong.']


class TestValidationError:

    def test_can_store_status_code(self):
        err = ValidationError('foo', status_code=401)
        assert err.status_code == 401

    def test_can_store_headers(self):
        err = ValidationError('foo', headers={'X-Food-Header': 'pizza'})
        assert err.headers == {'X-Food-Header': 'pizza'}

    def test_str(self):
        err = ValidationError('foo', status_code=403)
        assert str(err) == 'foo'

    def test_repr(self):
        err = ValidationError('foo', status_code=403)
        assert repr(err) == ('ValidationError({0!r}, '
                'status_code=403, headers=None)'.format('foo'))

def test_parse_basic(web_request, parser):
    web_request.json = {'foo': '42'}
    args = {
        'foo': fields.Int()
    }
    result = parser.parse(args, web_request)
    assert result == {'foo': 42}


def test_parse_raises_validation_error_if_data_invalid(web_request, parser):
    args = {
        'email': fields.Email(),
    }
    web_request.json = {'email': 'invalid'}
    with pytest.raises(ValidationError):
        parser.parse(args, web_request)


def test_argmap2schema():
    argmap = {
        'id': fields.Int(required=True),
        'title': fields.Str(),
        'description': fields.Str(),
        'content_type': fields.Str(load_from='content-type')
    }

    schema_cls = argmap2schema(argmap)
    assert issubclass(schema_cls, Schema)

    schema = schema_cls()

    for each in ['id', 'title', 'description', 'content_type']:
        assert each in schema.fields
    assert schema.fields['id'].required
    assert schema.opts.strict is True


def test_argmap2schema_with_nesting():
    argmap = {
        'nest': fields.Nested({
            'foo': fields.Field()
        })
    }
    schema_cls = argmap2schema(argmap)
    assert issubclass(schema_cls, Schema)
    schema = schema_cls()
    assert 'nest' in schema.fields
    assert type(schema.fields['nest']) is fields.Nested
    assert 'foo' in schema.fields['nest'].schema.fields


def test_is_json():
    assert is_json(None) is False
    assert is_json('application/json') is True
    assert is_json('application/xml') is False
    assert is_json('application/vnd.api+json') is True

def test_get_mimetype():
    assert get_mimetype('application/json') == 'application/json'
    assert get_mimetype('application/json;charset=utf8') == 'application/json'
    assert get_mimetype(None) is None
