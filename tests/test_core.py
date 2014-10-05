# -*- coding: utf-8 -*-
import mock

import pytest

from webargs.core import Parser, Arg, ValidationError, Missing, get_value, PY2

if not PY2:
    unicode = str

@pytest.fixture
def request():
    return mock.Mock()

class MockRequestParser(Parser):
    """A minimal parser implementation that parses mock requests."""

    def parse_json(self, request, name, arg):
        return get_value(request.json, name, arg.multiple)

# Arg tests

def test_bad_validate_param():
    with pytest.raises(ValueError):
        Arg(validate='bad')

def test_validated():
    arg = Arg(validate=lambda x: x == 42)
    assert arg.validated(42) == 42
    with pytest.raises(ValidationError):
        arg.validated(32)

def test_validated_with_nonascii_input():
    arg = Arg(validate=lambda t: False)
    text = u'øˆ∆´ƒº'
    with pytest.raises(ValidationError) as excinfo:
        arg.validated(text)
    assert text in unicode(excinfo)

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

def test_conversion_to_str():
    arg = Arg(str)
    assert arg.validated(42) == '42'

def test_use_param():
    arg = Arg(use=lambda x: x.upper())
    assert arg.validated('foo') == 'FOO'

def test_convert_and_use_params():
    arg = Arg(float, use=lambda val: val + 1)
    assert arg.validated(41) == 42.0

def test_error_raised_if_use_is_uncallable():
    with pytest.raises(ValueError) as excinfo:
        Arg(use='bad')
    assert '{0!r} is not callable.'.format('bad') in str(excinfo)

def test_use_is_called_before_validate():
    arg = Arg(use=lambda x: x + 1, validate=lambda x: x == 41)
    with pytest.raises(ValidationError):
        arg.validated(41)

def test_use_can_be_none():
    arg = Arg(use=None)
    assert arg.validated(41) == 41

def test_validate_can_be_none():
    arg = Arg(validate=None)
    assert arg.validated(41) == 41

def test_multiple_with_type_arg():
    arg = Arg(int, multiple=True)
    assert arg.validated(['1', 2, 3.0]) == [1, 2, 3]

def test_multiple_with_use_arg():
    arg = Arg(multiple=True, use=lambda x: x.upper())
    assert arg.validated(['foo', 'bar']) == ['FOO', 'BAR']

# Parser tests

@mock.patch('webargs.core.Parser.parse_json')
def test_parse_json_called_by_parse_arg(parse_json, request):
    arg = Arg()
    p = Parser()
    p.parse_arg('foo', arg, request)
    assert parse_json.called

@mock.patch('webargs.core.Parser.parse_querystring')
def test_parse_querystring_called_by_parse_arg(parse_querystring, request):
    arg = Arg()
    p = Parser()
    p.parse_arg('foo', arg, request)
    assert parse_querystring.called

@mock.patch('webargs.core.Parser.parse_form')
def test_parse_form_called_by_parse_arg(parse_form, request):
    arg = Arg()
    p = Parser()
    p.parse_arg('foo', arg, request)
    assert parse_form.called

@mock.patch('webargs.core.Parser.parse_json')
def test_parse_json_not_called_when_json_not_a_target(parse_json, request):
    arg = Arg()
    p = Parser()
    p.parse_arg('foo', arg, request, targets=('form', 'querystring'))
    assert parse_json.call_count == 0

@mock.patch('webargs.core.Parser.parse_headers')
def test_parse_headers_called_when_headers_is_a_target(parse_headers, request):
    arg = Arg()
    p = Parser()
    p.parse_arg('foo', arg, request)
    assert parse_headers.call_count == 0
    p.parse_arg('foo', arg, request, targets=('headers',))
    assert parse_headers.called

@mock.patch('webargs.core.Parser.parse_cookies')
def test_parse_cookies_called_when_cookies_is_a_target(parse_cookies, request):
    arg = Arg()
    p = Parser()
    p.parse_arg('foo', arg, request)
    assert parse_cookies.call_count == 0
    p.parse_arg('foo', arg, request, targets=('cookies',))
    assert parse_cookies.called

@mock.patch('webargs.core.Parser.fallback')
def test_fallback_used_if_all_other_functions_return_none(fallback, request):
    arg = Arg()
    p = Parser()
    p.parse({'foo': arg}, request)
    assert fallback.called

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

@mock.patch('webargs.core.Parser.parse_json')
def test_parse_required_arg_raises_validation_error(parse_json, request):
    arg = Arg(required=True)
    p = Parser()
    parse_json.return_value = Missing
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

@mock.patch('webargs.core.Parser.parse_form')
def test_parse_required_multiple_arg(parse_form, request):
    parse_form.return_value = []
    arg = Arg(multiple=True, required=True)
    p = Parser()
    with pytest.raises(ValidationError):
        p.parse_arg('foo', arg, request)

    parse_form.return_value = None
    with pytest.raises(ValidationError):
        p.parse_arg('foo', arg, request)

def test_default_targets():
    assert set(Parser.DEFAULT_TARGETS) == set(['json', 'querystring', 'form'])

def test_value_error_raised_if_invalid_target(request):
    arg = Arg()
    p = Parser()
    with pytest.raises(ValueError) as excinfo:
        p.parse_arg('foo', arg, request, targets=('invalidtarget', 'headers'))
    assert 'Invalid targets arguments: {0}'.format(['invalidtarget']) in str(excinfo)

@mock.patch('webargs.core.Parser.parse_json')
def test_conversion(parse_json, request):
    parse_json.return_value = 42
    arg = Arg(str)
    assert Parser().parse_arg('foo', arg, request, targets=('json',)) == '42'

@mock.patch('webargs.core.Parser.handle_error')
@mock.patch('webargs.core.Parser.parse_json')
def test_handle_error_called_when_parsing_raises_error(parse_json, handle_error, request):
    val_err = ValidationError('error occurred')
    parse_json.side_effect = val_err
    p = Parser()
    p.parse({'foo': Arg()}, request, targets=('json',))
    assert handle_error.called
    parse_json.side_effect = Exception('generic exception')
    p.parse({'foo': Arg()}, request, targets=('json',))
    assert handle_error.call_count == 2

def test_handle_error_reraises_errors():
    p = Parser()
    with pytest.raises(ValidationError):
        p.handle_error(ValidationError('error raised'))

def test_passing_exception_as_error_argument():
    arg = Arg(int, validate=lambda n: n == 42,
        error=AttributeError('an error occurred.'))
    with pytest.raises(ValidationError) as excinfo:
        arg.validated(41)
    assert 'an error occurred' in str(excinfo)

@mock.patch('webargs.core.Parser.parse_headers')
def test_targets_as_init_arguments(parse_headers, request):
    p = Parser(targets=('headers',))
    p.parse({'foo': Arg()}, request)
    assert parse_headers.called

@mock.patch('webargs.core.Parser.parse_files')
def test_parse_files(parse_files, request):
    p = Parser()
    p.parse({'foo': Arg()}, request, targets=('files',))
    assert parse_files.called

@mock.patch('webargs.core.Parser.parse_json')
def test_custom_error_handler(parse_json, request):
    class CustomError(Exception):
        pass

    def error_handler(error):
        raise CustomError(error)
    parse_json.side_effect = AttributeError('parse_json failed')
    p = Parser(error_handler=error_handler)
    with pytest.raises(CustomError):
        p.parse({'foo': Arg()}, request)


@mock.patch('webargs.core.Parser.parse_json')
def test_custom_error_handler_decorator(parse_json, request):
    class CustomError(Exception):
        pass
    parse_json.side_effect = AttributeError('parse_json failed')

    parser = Parser()

    @parser.error_handler
    def handle_error(error):
        raise CustomError(error)

    with pytest.raises(CustomError):
        parser.parse({'foo': Arg()}, request)


def test_custom_target_handler(request):
    request.data = {'foo': 42}

    parser = Parser()

    @parser.target_handler('data')
    def parse_data(req, name, arg):
        return req.data.get(name)

    result = parser.parse({'foo': Arg(int)}, request, targets=('data', ))
    assert result['foo'] == 42


def test_missing_is_falsy():
    assert bool(Missing) is False

def test_full_input_validation(request):

    request.json = {'foo': 41, 'bar': 42}

    parser = MockRequestParser()
    args = {'foo': Arg(int), 'bar': Arg(int)}
    with pytest.raises(ValidationError):
        # Test that `validate` receives dictionary of args
        parser.parse(args, request, targets=('json', ),
                     validate=lambda args: args['foo'] > args['bar'])

def test_full_input_validation_with_custom_error(request):
    request.json = {'foo': 41}
    parser = MockRequestParser(error='cool custom message')
    args = {'foo': Arg(int)}
    with pytest.raises(ValidationError) as excinfo:
        # Test that `validate` receives dictionary of args
        parser.parse(args, request, targets=('json', ),
                     validate=lambda args: False)
    assert 'cool custom message' in str(excinfo)

def test_full_input_validator_receives_nonascii_input(request):
    def validate(val):
        return False
    text = u'øœ∑∆∑'
    request.json = {'text': text}
    parser = MockRequestParser()
    args = {'text': Arg(unicode)}
    with pytest.raises(ValidationError):
        parser.parse(args, request, targets=('json', ), validate=validate)
