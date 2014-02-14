# -*- coding: utf-8 -*-
import mock

import pytest

from webargs.core import Parser, Arg, ValidationError, DEFAULT_TARGETS

@pytest.fixture
def request():
    return mock.Mock()

# Arg tests

def test_bad_validate_param():
    with pytest.raises(ValueError):
        Arg(validate='bad')

def test_validated():
    arg = Arg(validate=lambda x: x == 42)
    assert arg.validated(42) == 42
    with pytest.raises(ValidationError):
        arg.validated(32)

def test_validated_with_conversion():
    arg = Arg(validate=lambda x: x == 42, type_=int)
    assert arg.validated('42') == 42

def test_validated_with_bad_type():
    arg = Arg(type_=int)
    assert arg.validated(42) == 42
    with pytest.raises(ValidationError):
        arg.validated('nonint')

def test_custom_error():
    arg = Arg(type_=int, error='not an int!')
    with pytest.raises(ValidationError) as excinfo:
        arg.validated('badinput')
    assert 'not an int!' in str(excinfo)

def test_default_valdation_msg():
    arg = Arg(validate=lambda x: x == 42)
    with pytest.raises(ValidationError) as excinfo:
        arg.validated(1)
    assert 'Validator <lambda>(1) is not True' in str(excinfo)

# Parser tests

@mock.patch('webargs.core.Parser.parse_json')
def test_parse_json_called_by_parse_arg(parse_json, request):
    arg = Arg()
    p = Parser()
    p.parse_arg('foo', arg, request)
    assert parse_json.called_once_with(request, 'foo')


@mock.patch('webargs.core.Parser.parse_querystring')
def test_parse_querystring_called_by_parse_arg(parse_querystring, request):
    arg = Arg()
    p = Parser()
    p.parse_arg('foo', arg, request)
    assert parse_querystring.called_once_with(request, 'foo')

@mock.patch('webargs.core.Parser.parse_form')
def test_parse_form_called_by_parse_arg(parse_form, request):
    arg = Arg()
    p = Parser()
    p.parse_arg('foo', arg, request)
    assert parse_form.called_once_with(request, 'foo')

@mock.patch('webargs.core.Parser.parse_headers')
def test_parse_headers_called_by_parse_arg(parse_headers, request):
    arg = Arg()
    p = Parser()
    p.parse_arg('foo', arg, request)
    assert parse_headers.called_once_with(request, 'foo')

@mock.patch('webargs.core.Parser.parse_json')
def test_parse_json_not_called_when_json_not_a_target(parse_json, request):
    arg = Arg()
    p = Parser()
    p.parse_arg('foo', arg, request, targets=('form', 'querystring'))
    assert parse_json.call_count == 0

@mock.patch('webargs.core.Parser.fallback')
def test_fallback_used_if_all_other_functions_return_none(fallback, request):
    arg = Arg()
    p = Parser()
    p.parse_arg('foo', arg, request)
    assert fallback.called_once_with(request, 'foo')

@mock.patch('webargs.core.Parser.parse_json')
def test_parse(parse_json, request):
    parse_json.return_value = 42
    argmap = {
        'username': Arg(),
        'password': Arg()
    }
    p = Parser()
    ret = p.parse(argmap, request)
    assert {'username': 42, 'password': 42} == ret

def test_parse_required_arg_raises_validation_error(request):
    arg = Arg(required=True)
    p = Parser()
    with pytest.raises(ValidationError) as excinfo:
        p.parse_arg('foo', arg, request)
    assert 'Required parameter ' + repr('foo') + ' not found.' in str(excinfo)

@mock.patch('webargs.core.Parser.parse_json')
def test_parse_required_arg(parse_json, request):
    arg = Arg(required=True)
    parse_json.return_value = 42
    p = Parser()
    result = p.parse_arg('foo', arg, request, targets=('json', ))
    assert result == 42

def test_default_targets():
    assert set(DEFAULT_TARGETS) == set(['json', 'querystring', 'form'])

def test_value_error_raised_if_invalid_target(request):
    arg = Arg()
    p = Parser()
    with pytest.raises(ValueError) as excinfo:
        p.parse_arg('foo', arg, request, targets=('invalidtarget', 'headers'))
    assert 'Invalid targets arguments: {0}'.format(['invalidtarget']) in str(excinfo)
