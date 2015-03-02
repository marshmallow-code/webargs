# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import mock
import io

from flask import Flask, jsonify
from flask.views import MethodView
from werkzeug.exceptions import HTTPException
from werkzeug.datastructures import ImmutableMultiDict
import pytest

from webargs import Arg, Missing
from webargs.core import ValidationError
from webargs.flaskparser import FlaskParser, use_args, use_kwargs, abort

from .compat import text_type

class TestAppConfig:
    TESTING = True
    DEBUG = True

parser = FlaskParser()

hello_args = {
    'name': Arg(text_type, default='World'),
}

@pytest.fixture
def testapp():
    app = Flask(__name__)
    app.config.from_object(TestAppConfig)

    @app.route('/handleform', methods=['post'])
    def handleform():
        """View that just returns the jsonified args."""
        args = parser.parse(hello_args, locations=('form', ))
        return jsonify(args)
    return app


def test_parsing_get_args_in_request_context(testapp):
    with testapp.test_request_context('/myendpoint?name=Fred', method='get'):
        args = parser.parse(hello_args)
        assert args == {'name': 'Fred'}

def test_parsing_get_args_with_query_location_specified(testapp):
    with testapp.test_request_context('/myendpoint?name=Fred', method='get'):
        args = parser.parse(hello_args, locations=('query', ))
        assert args == {'name': 'Fred'}

def test_parsing_get_args_default(testapp):
    with testapp.test_request_context('/myendpoint', method='get'):
        args = parser.parse(hello_args)
        assert args == {'name': 'World'}

def test_parsing_json_in_request_context(testapp):
    with testapp.test_request_context('/myendpoint', method='post',
                                    data=json.dumps({'name': 'Fred'}),
                                        content_type='application/json'):
        args = parser.parse(hello_args)
        assert args['name'] == 'Fred'

def test_parsing_json_with_charset(testapp):
    with testapp.test_request_context('/myendpoint', method='post',
                                      data=json.dumps({'name': 'Fred'}),
                                      content_type='application/json;charset=UTF-8'):
        args = parser.parse(hello_args)
        assert args == {'name': 'Fred'}

def test_arg_with_location(testapp):
    testargs = {
        'name': Arg(str, location='json'),
        'age': Arg(int, location='querystring'),
    }
    with testapp.test_request_context('/myendpoint?age=42', method='post',
            data=json.dumps({'name': 'Fred'}), content_type='application/json'):
        args = parser.parse(testargs)
        assert args['name'] == 'Fred'
        assert args['age'] == 42


def test_nested_args(testapp):
    testargs = {
        'name': Arg({'first': Arg(str, use=lambda v: v.lower()),
                     'last': Arg(str, use=lambda v: v.upper())})
    }
    with testapp.test_request_context('/myendpoint', method='post',
            data=json.dumps({'name': {'first': 'sTevE', 'last': 'LoRiA'}}),
            content_type='application/json'):
        args = parser.parse(testargs)
        assert args['name']['first'] == 'steve'
        assert args['name']['last'] == 'LORIA'

def test_nested_multiple_args(testapp):
    testargs = {
        'users': Arg({'id': Arg(), 'name': Arg()}, multiple=True)
    }
    in_data = {'users': [{'id': 1, 'name': 'foo'}, {'id': 2, 'name': 'bar'}]}
    with testapp.test_request_context('/myendpoint', method='post',
            data=json.dumps(in_data),
            content_type='application/json'):
        args = parser.parse(testargs)
        users = args['users']
        assert users[0]['id'] == 1
        assert users[1]['id'] == 2


def test_parsing_json_default(testapp):
    with testapp.test_request_context('/myendpoint', method='post',
                                    data=json.dumps({}),
                                    content_type='application/json'):
        args = parser.parse(hello_args)
        assert args == {'name': 'World'}

def test_parsing_arg_with_default_and_set_location(testapp):
    # Regression test for issue #11
    page = {
        'p': Arg(int,
                default=1,
                validate=lambda p: p > 0,
                error=u"La page demandée n'existe pas",
                location='querystring'),
    }
    with testapp.test_request_context('/myendpoint', method='post',
            data=json.dumps({}), content_type='application/json'):
        args = parser.parse(page)
        assert args['p'] == 1


def test_parsing_json_if_no_json(testapp):
    with testapp.test_request_context('/myendpoint', method='post'):
        args = parser.parse(hello_args)
        assert args == {'name': 'World'}


def test_parsing_form(testapp):
    test_client = testapp.test_client()
    res = test_client.post('/handleform', data={'name': 'Fred'})
    assert json.loads(res.data.decode('utf-8')) == {'name': 'Fred'}

def test_parsing_form_default(testapp):
    test_client = testapp.test_client()
    res = test_client.post('/handleform')
    assert json.loads(res.data.decode('utf-8')) == {'name': 'World'}

@mock.patch('webargs.flaskparser.abort')
def test_abort_called_on_validation_error(mock_abort, testapp):
    def validate(x):
        return x == 42

    argmap = {'value': Arg(validate=validate, type_=int)}
    with testapp.test_request_context('/foo', method='post',
            data=json.dumps({'value': 41}), content_type='application/json'):
        parser.parse(argmap)
    mock_abort.assert_called
    abort_args, abort_kwargs = mock_abort.call_args
    assert abort_args[0] == 400
    expected_msg = u'Validator {0}({1}) is not True'.format(validate.__name__, 41)
    assert abort_kwargs['message'] == expected_msg
    assert type(abort_kwargs['exc']) == ValidationError

@mock.patch('webargs.flaskparser.abort')
def test_abort_called_on_type_conversion_error(mock_abort, testapp):
    argmap = {'value': Arg(type_=int)}
    with testapp.test_request_context('/foo', method='post',
            data=json.dumps({'value': 'badinput'}), content_type='application/json'):
        parser.parse(argmap)
    mock_abort.assert_called_once
    abort_args, abort_kwargs = mock_abort.call_args
    assert 'Expected type "integer" for value, got "string"' in abort_kwargs['message']
    assert type(abort_kwargs['exc']) == ValidationError

def test_use_args_decorator(testapp):
    @testapp.route('/foo/', methods=['post', 'get'])
    @parser.use_args({'myvalue': Arg(type_=int)})
    def echo(args):
        return jsonify(args)
    test_client = testapp.test_client()
    res = test_client.post('/foo/', data={'myvalue': 23})
    assert json.loads(res.data.decode('utf-8')) == {'myvalue': 23}


def test_use_args_with_validate_parameter(testapp):
    @testapp.route('/foo/', methods=['post', 'get'])
    @parser.use_args({'myvalue': Arg(int)}, validate=lambda args: args['myvalue'] > 42)
    def echo(args):
        return jsonify(args)

    test_client = testapp.test_client()
    res = test_client.post('/foo/', data={'myvalue': 41})
    assert res.status_code == 400


def test_use_args_decorator_on_a_method(testapp):
    class MyMethodView(MethodView):
        @parser.use_args({'myvalue': Arg(int)})
        def post(self, args):
            return jsonify(args)
    testapp.add_url_rule('/methodview/',
        view_func=MyMethodView.as_view(str('mymethodview')))
    test_client = testapp.test_client()
    res = test_client.post('/methodview/', data={'myvalue': 42})
    assert json.loads(res.data.decode('utf-8')) == {'myvalue': 42}

def test_use_kwargs_decorator_on_a_method(testapp):

    class MyMethodView(MethodView):
        @parser.use_kwargs({'myvalue': Arg(int)})
        def post(self, myvalue):
            return jsonify({'myvalue': myvalue})

    testapp.add_url_rule('/methodview/',
        view_func=MyMethodView.as_view(str('mymethodview')))
    test_client = testapp.test_client()
    res = test_client.post('/methodview/', data={'myvalue': 42})
    assert json.loads(res.data.decode('utf-8')) == {'myvalue': 42}


def test_use_args_decorator_with_url_parameters(testapp):
    @testapp.route('/foo/<int:id>', methods=['post', 'get'])
    @parser.use_args({'myvalue': Arg(type_=int)})
    def echo(args, id):
        assert id == 42
        return jsonify(args)
    test_client = testapp.test_client()
    res = test_client.post('/foo/42', data={'myvalue': 23})
    assert json.loads(res.data.decode('utf-8')) == {'myvalue': 23}

def test_use_args_singleton(testapp):
    @testapp.route('/foo/')
    @use_args({'myvalue': Arg(int)})
    def echo(args):
        return jsonify(args)
    test_client = testapp.test_client()
    res = test_client.get('/foo/?myvalue=42')
    assert json.loads(res.data.decode('utf-8')) == {'myvalue': 42}

def test_use_args_doesnt_change_docstring(testapp):
    @testapp.route('/foo/', methods=['post', 'get'])
    @parser.use_args({'myvalue': Arg(type_=int)})
    def echo(args, id):
        """Echo docstring."""
        return jsonify(args)
    assert echo.__doc__ == 'Echo docstring.'

def test_use_kwargs_decorator(testapp):
    @testapp.route('/foo/', methods=['post', 'get'])
    @parser.use_kwargs({'myvalue': Arg(type_=int)})
    def echo(myvalue):
        return jsonify(myvalue=myvalue)
    test_client = testapp.test_client()
    res = test_client.post('/foo/', data={'myvalue': 23})
    assert json.loads(res.data.decode('utf-8')) == {'myvalue': 23}

def test_use_kwargs_with_missing_data(testapp):
    @testapp.route('/foo/', methods=['post', 'get'])
    @parser.use_kwargs({'username': Arg(str), 'password': Arg(str)})
    def echo(username, password):
        return jsonify(username=username, password=password)
    test_client = testapp.test_client()
    res = test_client.post('/foo/', data={'username': 'foo'})
    expected = {'username': 'foo', 'password': None}
    assert json.loads(res.data.decode('utf-8')) == expected

def test_use_kwargs_decorator_with_url_parameters(testapp):
    @testapp.route('/foo/<int:id>', methods=['post', 'get'])
    @parser.use_kwargs({'myvalue': Arg(type_=int)})
    def echo(myvalue, id):
        assert id == 42
        return jsonify(myvalue=myvalue)
    test_client = testapp.test_client()
    res = test_client.post('/foo/42', data={'myvalue': 23})
    assert json.loads(res.data.decode('utf-8')) == {'myvalue': 23}

def test_use_kwargs_singleton(testapp):
    @testapp.route('/foo/')
    @use_kwargs({'myvalue': Arg(int)})
    def echo(myvalue):
        return jsonify(myvalue=myvalue)
    test_client = testapp.test_client()
    res = test_client.get('/foo/?myvalue=42')
    assert json.loads(res.data.decode('utf-8')) == {'myvalue': 42}

def test_use_kwargs_doesnt_change_docstring(testapp):
    @testapp.route('/foo/', methods=['post', 'get'])
    @parser.use_kwargs({'myvalue': Arg(type_=int)})
    def echo(args, id):
        """Echo docstring."""
        return jsonify(args)
    assert echo.__doc__ == 'Echo docstring.'

@mock.patch('webargs.flaskparser.abort')
def test_abort_called_when_required_arg_not_present(mock_abort, testapp):
    args = {'required': Arg(required=True)}
    with testapp.test_request_context('/foo', method='post',
            data=json.dumps({}), content_type='application/json'):
        parser.parse(args)
        assert mock_abort.called_once_with(400)

def test_arg_allowed_missing(testapp):
    # 'last' argument is allowed to be missing
    args = {'first': Arg(str), 'last': Arg(str, allow_missing=True)}
    with testapp.test_request_context('/foo', method='post',
            data=json.dumps({'first': 'Fred'}), content_type='application/json'):
        args = parser.parse(args)
        assert 'first' in args
        assert 'last' not in args

def test_arg_allowed_missing_when_none_is_passed(testapp):
    # 'last' argument is allowed to be missing
    args = {'first': Arg(str), 'last': Arg(allow_missing=True)}
    with testapp.test_request_context('/foo', method='post',
            data=json.dumps({'first': 'Fred', 'last': None}), content_type='application/json'):
        args = parser.parse(args)
        assert 'first' in args
        assert args['last'] is None

def test_arg_allow_missing_false(testapp):
    args = {'first': Arg(str), 'last': Arg(str, allow_missing=False)}
    with testapp.test_request_context('/foo', method='post',
            data=json.dumps({'first': 'Fred'}), content_type='application/json'):
        args = parser.parse(args)
        assert args['last'] is None

def test_multiple_arg_allowed_missing(testapp):
    args = {'name': Arg(str, multiple=True, allow_missing=True)}
    with testapp.test_request_context(path='/foo', method='post'):
        args = parser.parse(args)
        assert 'name' not in args

def test_multiple_arg_allowed_missing_int_conversion(testapp):
    args = {'ids': Arg(int, multiple=True, allow_missing=True)}
    with testapp.test_request_context(path='/foo', method='post',
            data=json.dumps({'fakedata': True}), content_type='application/json'):
        args = parser.parse(args)
        assert 'ids' not in args or len(args['ids']) == 0

def test_multiple_arg_allowed_missing_false_int_conversion(testapp):
    args = {'ids': Arg(int, multiple=True, allow_missing=False)}
    with testapp.test_request_context(path='/foo', method='post',
            data=json.dumps({'fakedata': True}), content_type='application/json'):
        args = parser.parse(args)
        assert 'ids' in args

@mock.patch('webargs.flaskparser.abort')
def test_multiple_arg_required_int_conversion_required(mock_abort, testapp):
    args = {'ids': Arg(int, multiple=True, required=True)}
    with testapp.test_request_context(path='/foo', method='post',
            data=json.dumps({}), content_type='application/json'):
        args = parser.parse(args)
    mock_abort.assert_called_once


def test_parsing_headers(testapp):
    with testapp.test_request_context('/foo', headers={'Name': 'Fred'}):
        args = parser.parse(hello_args, locations=('headers',))
        # Header key is lowercased
        assert args['name'] == 'Fred'

def test_parsing_cookies(testapp):
    @testapp.route('/getcookiearg')
    def echo():
        args = parser.parse(hello_args, locations=('cookies',))
        return jsonify(args)
    testclient = testapp.test_client()
    testclient.set_cookie('localhost', key='name', value='Fred')
    res = testclient.get('/getcookiearg')
    assert json.loads(res.data.decode('utf-8')) == {'name': 'Fred'}

def test_parse_form_returns_missing_if_no_form():
    req = mock.Mock()
    req.form.get.side_effect = AttributeError('no form')
    assert parser.parse_form(req, 'foo', Arg()) is Missing

def test_unicode_arg(testapp):
    with testapp.test_request_context('/foo?name=Früd'):
        args = parser.parse(hello_args)
        assert args['name'] == 'Früd'

def test_abort_with_message():
    with pytest.raises(HTTPException) as excinfo:
        abort(400, message='custom error message')
    assert excinfo.value.data['message'] == 'custom error message'


def test_parse_files(testapp):
    payload = {'myfile': (io.BytesIO(b'bar'), 'baz.txt')}
    file_args = {'myfile': Arg()}
    with testapp.test_request_context('/foo', method='POST',
            data=payload):
        args = parser.parse(file_args, locations=('files', ))
        assert args['myfile'].read() == b'bar'

@pytest.mark.parametrize('context', [
    # querystring
    {'path': '/foo?name=steve&name=Loria&nums=4&nums=2'},
    # form
    {'path': '/foo', 'method': 'POST', 'data': ImmutableMultiDict(
        [('name', 'steve'), ('name', 'Loria'),
         ('nums', 4), ('nums', 2)])},
])
def test_parse_multiple(context, testapp):
    multargs = {'name': Arg(multiple=True), 'nums': Arg(int, multiple=True)}
    with testapp.test_request_context(**context):
        args = parser.parse(multargs)
        assert args['name'] == ['steve', 'Loria']
        assert args['nums'] == [4, 2]


def test_parse_multiple_arg_defaults_to_empty_list(testapp):
    multargs = {'name': Arg(multiple=True)}
    with testapp.test_request_context('/foo'):
        args = parser.parse(multargs)
        assert args['name'] == []

@mock.patch('webargs.flaskparser.abort')
def test_multiple_required_arg(mock_abort, testapp):
    multargs = {'name': Arg(required=True, multiple=True)}
    with testapp.test_request_context('/foo'):
        parser.parse(multargs)
    assert mock_abort.called_once

def test_multiple_allow_missing(testapp):
    multargs = {'name': Arg(allow_missing=True, multiple=True)}
    with testapp.test_request_context('/foo'):
        args = parser.parse(multargs)
        assert 'name' not in args


def test_parse_multiple_json(testapp):
    multargs = {'name': Arg(multiple=True)}
    with testapp.test_request_context('/foo', data=json.dumps({'name': 'steve'}),
            content_type='application/json', method='POST'):
        args = parser.parse(multargs, locations=('json',))
        assert args['name'] == ['steve']

def test_parse_json_with_nonascii_characters(testapp):
    args = {'text': Arg(text_type)}
    text = u'øˆƒ£ºº∆ƒˆ∆'
    with testapp.test_request_context('/foo', data=json.dumps({'text': text}),
            content_type='application/json', method='POST'):
        result = parser.parse(args, locations=('json', ))
    assert result['text'] == text

def test_validation_error_with_status_code_and_data(testapp):
    def always_fail(value):
        raise ValidationError('something went wrong', status_code=401, extra='some data')
    args = {'text': Arg(validate=always_fail)}
    with testapp.test_request_context('/foo', data=json.dumps({'text': 'bar'}),
            content_type='application/json', method='POST'):
        with pytest.raises(HTTPException) as excinfo:
            parser.parse(args, locations=('json', ))
    exc = excinfo.value
    assert exc.code == 401
    assert exc.data['extra'] == 'some data'
