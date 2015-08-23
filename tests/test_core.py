# -*- coding: utf-8 -*-
import json
import mock
import sys

import pytest
from werkzeug.datastructures import MultiDict as WerkMultiDict

PY26 = sys.version_info[0] == 2 and int(sys.version_info[1]) < 7
if not PY26:  # django does not support python 2.6
    from django.utils.datastructures import MultiValueDict as DjMultiDict
from bottle import MultiDict as BotMultiDict

from webargs.core import (
    Parser,
    Arg,
    ValidationError,
    RequiredArgMissingError,
    Missing,
    get_value,
    PY2,
    text_type,
    long_type,
    __type_map__,
    __non_nullable_types__
)

from uuid import UUID

if not PY2:
    unicode = str


class MockRequestParser(Parser):
    """A minimal parser implementation that parses mock requests."""

    def parse_json(self, web_request, name, arg):
        return get_value(web_request.json, name, arg.multiple)

    def parse_cookies(self, web_request, name, arg):
        return get_value(web_request.cookies, name, arg.multiple)


@pytest.fixture
def web_request():
    return mock.Mock()

@pytest.fixture
def parser():
    return MockRequestParser()


class TestArg:

    def test_bad_validate_param(self):
        with pytest.raises(ValueError):
            Arg(validate='bad')

    def test_validated(self):
        arg = Arg(validate=lambda x: x == 42)
        assert arg.validated('foo', 42) == 42
        with pytest.raises(ValidationError):
            arg.validated('foo', 32)

    def test_validated_stores_the_arg_name(self):
        arg = Arg(validate=lambda t: False)
        with pytest.raises(ValidationError) as excinfo:
            arg.validated('our_arg_name', True)
        assert 'our_arg_name' == excinfo.value.arg_name

    def test_validated_with_nonascii_input(self):
        arg = Arg(validate=lambda t: False)
        text = u'øˆ∆´ƒº'
        with pytest.raises(ValidationError) as excinfo:
            arg.validated('foo', text)
        assert text in unicode(excinfo)

    def test_validated_with_conversion(self):
        arg = Arg(validate=lambda x: x == 42, type_=int)
        assert arg.validated('foo', '42') == 42

    def test_validated_with_bad_type(self):
        arg = Arg(type_=int)
        assert arg.validated('foo', 42) == 42
        with pytest.raises(ValidationError) as excinfo:
            arg.validated('foo', 'nonint')
        assert 'Expected type "integer" for foo, got "string"' in str(excinfo)

    @pytest.mark.parametrize('arg_type', __non_nullable_types__)
    def test_validated_non_nullable_types(self, arg_type):
        arg = Arg(type_=arg_type)
        with pytest.raises(ValidationError) as excinfo:
            arg.validated('foo', None)
        assert 'Expected type "{0}" for foo, got "null"'.format(
            __type_map__[arg_type]
        ) in str(excinfo)

    def test_validated_null(self):
        arg = Arg(type_=dict)
        assert arg.validated('foo', {}) == {}
        with pytest.raises(ValidationError) as excinfo:
            arg.validated('foo', None)
        assert 'Expected type "object" for foo, got "null"' in str(excinfo)

    def test_validated_null_noop(self):
        arg = Arg()
        assert arg.validated('foo', {}) == {}
        assert arg.validated('foo', None) is None

    def test_validated_text_type(self):
        arg = Arg(type_=text_type)
        assert arg.validated('foo', 42) == '42'

    def test_validated_long_type(self):
        arg = Arg(type_=long_type)
        assert arg.validated('foo', 42) == 42

    def test_validated_string_conversion_null(self):
        arg = Arg(type_=str)
        assert arg.validated('foo', None) is None

    def test_validated_unknown_type(self):
        arg = Arg(type_=UUID)
        assert (arg.validated('foo', '12345678123456781234567812345678') ==
                UUID('12345678-1234-5678-1234-567812345678'))
        with pytest.raises(ValidationError) as excinfo:
            arg.validated('foo', '123xyz')   # An invalid UUID
        assert 'Expected type "UUID" for foo, got "string"' in str(excinfo)

    def test_custom_error(self):
        arg = Arg(type_=int, error='not an int!')
        with pytest.raises(ValidationError) as excinfo:
            arg.validated('foo', 'badinput')
        assert 'not an int!' in str(excinfo)

    def test_default_valdation_msg(self):
        arg = Arg(validate=lambda x: x == 42)
        with pytest.raises(ValidationError) as excinfo:
            arg.validated('foo', 1)
        assert 'Validator <lambda>(1) is not True' in str(excinfo)

    def test_conversion_to_str(self):
        arg = Arg(str)
        assert arg.validated('foo', 42) == '42'

    def test_use_param(self):
        arg = Arg(use=lambda x: x.upper())
        assert arg.validated('foo', 'foo') == 'FOO'

    def test_use_can_be_list_of_callables(self):
        arg = Arg(use=[lambda x: x.upper(), lambda x: x.strip()])
        assert arg.validated('foo', '  foo  ') == 'FOO'

    def test_convert_and_use_params(self):
        arg = Arg(float, use=lambda val: val + 1)
        assert arg.validated('foo', 41) == 42.0

    def test_error_raised_if_use_is_uncallable(self):
        with pytest.raises(ValueError) as excinfo:
            Arg(use='bad')
        assert '{0!r} is not a callable or list of callables'.format('bad') in str(excinfo)

    def test_use_is_called_before_validate(self):
        arg = Arg(use=lambda x: x + 1, validate=lambda x: x == 41)
        with pytest.raises(ValidationError):
            arg.validated('foo', 41)

    def test_use_can_be_none(self):
        arg = Arg(use=None)
        assert arg.validated('foo', 41) == 41

    def test_validate_can_be_none(self):
        arg = Arg(validate=None)
        assert arg.validated('foo', 41) == 41

    def test_multiple_with_type_arg(self):
        arg = Arg(int, multiple=True)
        assert arg.validated('foo', ['1', 2, 3.0]) == [1, 2, 3]

    def test_multiple_with_use_arg(self):
        arg = Arg(multiple=True, use=lambda x: x.upper())
        assert arg.validated('foo', ['foo', 'bar']) == ['FOO', 'BAR']

    def test_repr(self):
        arg = Arg(str, default='foo', required=True)
        r = repr(arg)
        assert 'str' in r
        assert '<webargs.core.Arg' in r
        assert 'foo' in r
        assert 'required=True' in r


class TestArgNesting:

    def test_nested_argdict_has_type_dict(self):
        arg = Arg({
            'foo': Arg()
        })
        assert arg.type == dict

        with pytest.raises(ValidationError) as excinfo:
            arg.validated('myarg', 'notadict')

        assert 'Expected type "object" for myarg, got "string"' in str(excinfo)

    def test_nested_argdict_can_be_a_dict_subclass(self):
        arg = Arg(WerkMultiDict([('foo', 'bar')]))
        assert arg.type == WerkMultiDict

    def test_has_nesting(self):
        arg = Arg({'foo': Arg()})
        assert arg._has_nesting is True

    def test_nested_validation(self):
        arg = Arg({
            'foo': Arg(validate=lambda v: v <= 42)
        })

        assert arg.validated('myarg', {'foo': 42}) == {'foo': 42}
        with pytest.raises(ValidationError) as excinfo:
            arg.validated('', {'foo': 43})
        assert 'Validator <lambda>(43) is not True' in str(excinfo)

    def test_deep_nesting_validation(self):
        arg = Arg({
            'foo': Arg({
                'bar': Arg(validate=lambda v: v <= 42)
            })
        })

        valid = {'foo': {'bar': 42}}
        assert arg.validated('myarg', valid) == valid

    def test_outer_use(self):
        arg = Arg({
            'foo': Arg()
        }, use=json.loads)

        # has extra args
        in_data = json.dumps({'foo': 42, 'bar': 24})
        assert arg.validated('', in_data) == {'foo': 42}

    def test_nested_use(self):
        arg = Arg({
            'foo': Arg(use=lambda v: v.upper()),
            'bar': Arg(use=lambda v: v.lower())
        })
        in_data = {'foo': 'hErP', 'bar': 'dErP'}
        assert arg.validated('', in_data) == {'foo': 'HERP', 'bar': 'derp'}

    def test_nested_required(self):
        arg = Arg({
            'foo': Arg(required=True),
            'bar': Arg(required=False),
        })
        with pytest.raises(RequiredArgMissingError) as excinfo:
            arg.validated('', {})
        assert 'Required parameter "foo" not found.' in str(excinfo)

    def test_nested_required_unicode_error_message_override(self):
        arg = Arg({
            'foo': Arg(required=u'We need foo')
        })
        with pytest.raises(RequiredArgMissingError) as excinfo:
            arg.validated('', {})
        assert 'We need foo' in excinfo.value.message
        assert 'foo' in excinfo.value.arg_name

    def test_nested_multiple(self):
        arg = Arg({
            'foo': Arg(required=True),
            'bar': Arg(required=True),
        }, multiple=True)

        in_data = [{'foo': 42, 'bar': 24}, {'foo': 12, 'bar': 21}]
        assert arg.validated('', in_data) == in_data
        bad_data = [{'foo': 42, 'bar': 24}, {'bar': 21}]

        with pytest.raises(ValidationError) as excinfo:
            arg.validated('', bad_data)
        assert 'Required' in str(excinfo)

    def test_extra_arguments_are_excluded(self):
        arg = Arg({
            'foo': Arg(),
        })

        in_data = {'foo': 42, 'bar': 24}

        assert arg.validated('', in_data) == {'foo': 42}

# Parser tests

@mock.patch('webargs.core.Parser.parse_json')
def test_parse_json_called_by_parse_arg(parse_json, web_request):
    arg = Arg()
    p = Parser()
    p.parse_arg('foo', arg, web_request)
    parse_json.assert_called_with(web_request, 'foo', arg)

@mock.patch('webargs.core.Parser.parse_querystring')
def test_parse_querystring_called_by_parse_arg(parse_querystring, web_request):
    arg = Arg()
    p = Parser()
    p.parse_arg('foo', arg, web_request)
    assert parse_querystring.called

@mock.patch('webargs.core.Parser.parse_form')
def test_parse_form_called_by_parse_arg(parse_form, web_request):
    arg = Arg()
    p = Parser()
    p.parse_arg('foo', arg, web_request)
    assert parse_form.called

@mock.patch('webargs.core.Parser.parse_json')
def test_parse_json_not_called_when_json_not_a_location(parse_json, web_request):
    arg = Arg()
    p = Parser()
    p.parse_arg('foo', arg, web_request, locations=('form', 'querystring'))
    assert parse_json.call_count == 0

@mock.patch('webargs.core.Parser.parse_headers')
def test_parse_headers_called_when_headers_is_a_location(parse_headers, web_request):
    arg = Arg()
    p = Parser()
    p.parse_arg('foo', arg, web_request)
    assert parse_headers.call_count == 0
    p.parse_arg('foo', arg, web_request, locations=('headers',))
    parse_headers.assert_called

@mock.patch('webargs.core.Parser.parse_cookies')
def test_parse_cookies_called_when_cookies_is_a_location(parse_cookies, web_request):
    arg = Arg()
    p = Parser()
    p.parse_arg('foo', arg, web_request)
    assert parse_cookies.call_count == 0
    p.parse_arg('foo', arg, web_request, locations=('cookies',))
    parse_cookies.assert_called

@mock.patch('webargs.core.Parser.fallback')
def test_fallback_used_if_all_other_functions_return_none(fallback, web_request):
    arg = Arg()
    p = Parser()
    p.parse({'foo': arg}, web_request)
    fallback.assert_called

@mock.patch('webargs.core.Parser.parse_json')
def test_parse(parse_json, web_request):
    parse_json.return_value = 42
    argmap = {
        'username': Arg(),
        'password': Arg()
    }
    p = Parser()
    ret = p.parse(argmap, web_request)
    assert {'username': 42, 'password': 42} == ret

@mock.patch('webargs.core.Parser.parse_json')
def test_parse_required_arg_raises_validation_error(parse_json, web_request):
    arg = Arg(required=True)
    p = Parser()
    parse_json.return_value = Missing
    with pytest.raises(RequiredArgMissingError) as excinfo:
        p.parse_arg('foo', arg, web_request)
    assert 'Required parameter "foo" not found.' in str(excinfo)

@mock.patch('webargs.core.Parser.parse_json')
def test_parse_required_arg(parse_json, web_request):
    arg = Arg(required=True)
    parse_json.return_value = 42
    p = Parser()
    result = p.parse_arg('foo', arg, web_request, locations=('json', ))
    assert result == 42

@mock.patch('webargs.core.Parser.parse_form')
def test_parse_required_multiple_arg(parse_form, web_request):
    parse_form.return_value = []
    arg = Arg(multiple=True, required=True)
    p = Parser()
    with pytest.raises(RequiredArgMissingError):
        p.parse_arg('foo', arg, web_request)

    parse_form.return_value = None
    with pytest.raises(RequiredArgMissingError):
        p.parse_arg('foo', arg, web_request)

def test_default_locations():
    assert set(Parser.DEFAULT_LOCATIONS) == set(['json', 'querystring', 'form'])


def test_default(parser, web_request):
    web_request.json = {}
    args = {'val': Arg(default='pizza')}
    result = parser.parse(args, web_request, locations=('json', ))
    assert result['val'] == 'pizza'


def test_default_can_be_none(parser, web_request):
    web_request.json = {}
    args = {'val': Arg(default=None)}
    result = parser.parse(args, web_request, locations=('json', ))
    assert result['val'] is None


def test_callable_default(parser, web_request):
    web_request.json = {}
    args = {'val': Arg(default=lambda: 'pizza')}
    result = parser.parse(args, web_request, locations=('json', ))
    assert result['val'] == 'pizza'

def test_value_error_raised_if_invalid_location(web_request):
    arg = Arg()
    p = Parser()
    with pytest.raises(ValueError) as excinfo:
        p.parse_arg('foo', arg, web_request, locations=('invalidlocation', 'headers'))
    assert 'Invalid locations arguments: {0}'.format(['invalidlocation']) in str(excinfo)

def test_none_as_missing_sets_default(parser, web_request):
    web_request.json = {"name": None}
    args = {"name": Arg(none_as_missing=True, default="Bob")}
    result = parser.parse(args, web_request, locations=('json',))
    assert result["name"] == "Bob"

def test_none_as_missing_and_allow_missing(web_request, parser):
    web_request.json = {"name": None}
    args = {"name": Arg(none_as_missing=True, allow_missing=True)}
    result = parser.parse(args, web_request, locations=("json",))
    assert "name" not in result

def test_none_as_missing_and_required(web_request, parser):
    web_request.json = {"foo": None}
    arg = Arg(required=True, none_as_missing=True)
    with pytest.raises(RequiredArgMissingError) as excinfo:
        parser.parse_arg('foo', arg, web_request)
    assert 'Required parameter "foo" not found.' in str(excinfo)


@mock.patch('webargs.core.Parser.parse_json')
def test_conversion(parse_json, web_request):
    parse_json.return_value = 42
    arg = Arg(str)
    assert Parser().parse_arg('foo', arg, web_request, locations=('json',)) == '42'

@mock.patch('webargs.core.Parser.handle_error')
@mock.patch('webargs.core.Parser.parse_json')
def test_handle_error_called_when_parsing_raises_error(parse_json, handle_error, web_request):
    val_err = ValidationError('error occurred')
    parse_json.side_effect = val_err
    p = Parser()
    p.parse({'foo': Arg()}, web_request, locations=('json',))
    handle_error.assert_called
    parse_json.side_effect = ValidationError('another exception')
    p.parse({'foo': Arg()}, web_request, locations=('json',))
    assert handle_error.call_count == 2

def test_handle_error_reraises_errors():
    p = Parser()
    with pytest.raises(ValidationError):
        p.handle_error(ValidationError('error raised'))

def test_passing_exception_as_error_argument():
    arg = Arg(int, validate=lambda n: n == 42,
        error=AttributeError('an error occurred.'))
    with pytest.raises(ValidationError) as excinfo:
        arg.validated('foo', 41)
    assert 'an error occurred' in str(excinfo)

@mock.patch('webargs.core.Parser.parse_headers')
def test_locations_as_init_arguments(parse_headers, web_request):
    p = Parser(locations=('headers',))
    p.parse({'foo': Arg()}, web_request)
    assert parse_headers.called

@mock.patch('webargs.core.Parser.parse_files')
def test_parse_files(parse_files, web_request):
    p = Parser()
    p.parse({'foo': Arg()}, web_request, locations=('files',))
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
        p.parse({'foo': Arg()}, web_request)


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
        parser.parse({'foo': Arg()}, web_request)


def test_custom_location_handler(web_request):
    web_request.data = {'foo': 42}

    parser = Parser()

    @parser.location_handler('data')
    def parse_data(req, name, arg):
        return req.data.get(name)

    result = parser.parse({'foo': Arg(int)}, web_request, locations=('data', ))
    assert result['foo'] == 42

def test_custom_location_handler_with_dest(web_request):
    web_request.data = {'X-Foo': 42}
    parser = Parser()

    @parser.location_handler('data')
    def parse_data(req, name, arg):
        assert name == 'X-Foo'
        return req.data.get(name)

    result = parser.parse({'X-Foo': Arg(int, dest='x_foo')}, web_request, locations=('data', ))
    assert result['x_foo'] == 42

def test_missing_is_falsy():
    assert bool(Missing) is False

def test_full_input_validation(web_request):

    web_request.json = {'foo': 41, 'bar': 42}

    parser = MockRequestParser()
    args = {'foo': Arg(int), 'bar': Arg(int)}
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

    args = {'a': Arg(int), 'b': Arg(int)}
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

def test_full_input_validation_with_custom_error(web_request):
    web_request.json = {'foo': 41}
    parser = MockRequestParser(error='cool custom message')
    args = {'foo': Arg(int)}
    with pytest.raises(ValidationError) as excinfo:
        # Test that `validate` receives dictionary of args
        parser.parse(args, web_request, locations=('json', ),
                     validate=lambda args: False)
    assert 'cool custom message' in str(excinfo)

def test_required_with_custom_error(web_request):
    web_request.json = {}
    parser = MockRequestParser()
    args = {'foo': Arg(unicode, required='We need foo')}
    with pytest.raises(RequiredArgMissingError) as excinfo:
        # Test that `validate` receives dictionary of args
        parser.parse(args, web_request, locations=('json', ))

    assert 'We need foo' in excinfo.value.message
    assert 'foo' in excinfo.value.arg_name

def test_required_with_custom_error_and_validation_error(web_request):
    web_request.json = {'foo': ''}
    parser = MockRequestParser()
    args = {'foo': Arg(
        unicode, required='We need foo', validate=lambda s: len(s) > 1,
        error='foo required length is 3')}
    with pytest.raises(ValidationError) as excinfo:
        # Test that `validate` receives dictionary of args
        parser.parse(args, web_request, locations=('json', ))

    assert 'foo required length is 3' in excinfo.value.message
    assert 'foo' in excinfo.value.arg_name

def test_full_input_validator_receives_nonascii_input(web_request):
    def validate(val):
        return False
    text = u'øœ∑∆∑'
    web_request.json = {'text': text}
    parser = MockRequestParser()
    args = {'text': Arg(unicode)}
    with pytest.raises(ValidationError):
        parser.parse(args, web_request, locations=('json', ), validate=validate)

def test_get_value_basic():
    assert get_value({'foo': 42}, 'foo', False) == 42
    assert get_value({'foo': 42}, 'bar', False) is Missing
    assert get_value({'foos': ['a', 'b']}, 'foos', True) == ['a', 'b']
    # https://github.com/sloria/webargs/pull/30
    assert get_value({'foos': ['a', 'b']}, 'bar', True) is Missing


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
    assert get_value(input_dict, 'foos', multiple=True) == ['a', 'b']

def test_parse_with_dest(web_request):
    web_request.json = {'Content-Type': 'application/json'}

    parser = MockRequestParser()
    args = {'Content-Type': Arg(dest='content_type')}
    parsed = parser.parse(args, web_request, locations=('json',))
    assert parsed == {'content_type': 'application/json'}

def test_parse_nested_with_dest(web_request):
    parser = MockRequestParser()

    web_request.json = dict(nested_arg=dict(wrong='OK'))
    args = dict(nested_arg=Arg(dict(wrong=Arg(dest='right'))))

    parsed = parser.parse(args, web_request, locations=('json',))
    assert parsed == dict(nested_arg=dict(right='OK'))

def test_parse_nested_with_missing_key_and_dest(web_request):
    parser = MockRequestParser()

    web_request.json = dict(nested_arg=dict(payload='OK'))
    args = dict(nested_arg=Arg(dict(missing=Arg(dest='found'))))

    parsed = parser.parse(args, web_request, locations=('json',))
    assert parsed == dict(nested_arg=dict(found=None))

def test_parse_nested_with_default(web_request):
    parser = MockRequestParser()

    web_request.json = dict(nested_arg=dict())
    args = dict(nested_arg=Arg(dict(missing=Arg(default=False))))

    parsed = parser.parse(args, web_request, locations=('json',))
    assert parsed == dict(nested_arg=dict(missing=False))

def test_metadata_can_be_stored_on_args():
    # Extra params are stored as metadata
    arg = Arg(int, description='Just a number.')
    assert arg.metadata['description'] == 'Just a number.'

def test_use_args(web_request, parser):
    user_args = {
        'username': Arg(str),
        'password': Arg(str)
    }
    web_request.json = {'username': 'foo', 'password': 'bar'}

    @parser.use_args(user_args, web_request)
    def viewfunc(args):
        return args
    assert viewfunc() == {'username': 'foo', 'password': 'bar'}

def test_use_args_with_custom_locations_in_parser(web_request, parser):
    custom_args = {
        'foo': Arg(str),
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
        'username': Arg(str),
        'password': Arg(str),
    }
    web_request.json = {'username': 'foo', 'password': 'bar'}

    @parser.use_kwargs(user_args, web_request)
    def viewfunc(username, password):
        return {'username': username, 'password': password}
    assert viewfunc() == {'username': 'foo', 'password': 'bar'}


def test_use_kwargs_with_arg_missing(web_request, parser):
    user_args = {
        'username': Arg(str),
        'password': Arg(str),
    }
    web_request.json = {'username': 'foo'}

    @parser.use_kwargs(user_args, web_request)
    def viewfunc(username, password):
        return {'username': username, 'password': password}
    assert viewfunc() == {'username': 'foo', 'password': None}

def test_type_conversion_with_multiple_and_arg_missing(web_request, parser):
    # arg missing in request
    web_request.json = {}
    args = {'ids': Arg(int, multiple=True)}

    result = parser.parse(args, web_request)
    assert 'ids' in result

def test_type_conversion_with_multiple_and_arg_missing_allowed(web_request, parser):
    # arg missing in request
    web_request.json = {}
    args = {'ids': Arg(int, multiple=True, allow_missing=True)}

    result = parser.parse(args, web_request)
    assert 'ids' not in result

def test_type_conversion_with_multiple_required(web_request, parser):
    web_request.json = {}
    args = {'ids': Arg(int, multiple=True, required=True)}
    with pytest.raises(RequiredArgMissingError) as excinfo:
        parser.parse(args, web_request)
    assert 'Required parameter "ids" not found' in str(excinfo)

def test_use_kwargs_with_arg_allowed_missing(web_request, parser):
    user_args = {
        'username': Arg(str),
        'password': Arg(str, allow_missing=True),
    }
    web_request.json = {'username': 'foo'}

    @parser.use_kwargs(user_args, web_request)
    def viewfunc(username, password):
        return {'username': username, 'password': password}
    assert viewfunc() == {'username': 'foo', 'password': None}

def test_arg_location_param(web_request, parser):
    web_request.cookies = {'foo': 42}
    args = {'foo': Arg(location='cookies')}

    parsed = parser.parse(args, web_request)

    assert parsed['foo'] == 42

def test_validation_errors_in_validator_are_passed_to_handle_error(parser, web_request):
    def validate(value):
        raise ValidationError('Something went wrong.')
    args = {
        'name': Arg(validate=validate, location='json')
    }
    web_request.json = {'name': 'invalid'}
    with pytest.raises(ValidationError) as excinfo:
        parser.parse(args, web_request)
    exc = excinfo.value
    assert isinstance(exc, ValidationError)
    assert str(exc) == 'Something went wrong.'

def test_multiple_validators_may_be_specified_for_an_arg(parser, web_request):
    def validate_len(val):
        if len(val) < 6:
            raise ValidationError('Must be greater than 6 characters.')

    def has_digit(val):
        if not any(ch.isdigit() for ch in val):
            raise ValidationError('Must have a digit.')
    args = {
        'password': Arg(validate=[validate_len, has_digit])
    }
    web_request.json = {'password': '123'}
    with pytest.raises(ValidationError) as excinfo:
        parser.parse(args, web_request)
    assert 'Must be greater than 6 characters.' in str(excinfo)

    web_request.json = {'password': 'abcdefhij'}
    with pytest.raises(ValidationError) as excinfo:
        parser.parse(args, web_request)
    assert 'Must have a digit.' in str(excinfo)

def test_error_raised_if_validate_is_uncallable():
    with pytest.raises(ValueError) as excinfo:
        Arg(validate='uncallable')
    assert '{0!r} is not a callable or list of callables.'.format('uncallable') in str(excinfo)


class TestValidationError:

    def test_can_store_status_code(self):
        err = ValidationError('foo', status_code=401)
        assert err.status_code == 401

    def test_can_store_extra_data(self):
        err = ValidationError('foo', headers={'X-Food-Header': 'pizza'})
        assert err.data['headers'] == {'X-Food-Header': 'pizza'}

    def test_str(self):
        err = ValidationError('foo', status_code=403)
        assert str(err) == 'foo'

    def test_repr(self):
        err = ValidationError('foo', status_code=403)
        assert repr(err) == ('ValidationError({0!r}, '
                'status_code=403)'.format(unicode('foo')))
