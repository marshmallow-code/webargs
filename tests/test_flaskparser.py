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

from webargs import Arg
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
        args = parser.parse(hello_args, targets=('form', ))
        return jsonify(args)
    return app


def test_parsing_get_args_in_request_context(testapp):
    with testapp.test_request_context('/myendpoint?name=Fred', method='get'):
        args = parser.parse(hello_args)
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

def test_arg_with_target(testapp):
    testargs = {
        'name': Arg(str, target='json'),
        'age': Arg(int, target='querystring'),
    }
    with testapp.test_request_context('/myendpoint?age=42', method='post',
        data=json.dumps({'name': 'Fred'}), content_type='application/json'):
        args = parser.parse(testargs)
        assert args['name'] == 'Fred'
        assert args['age'] == 42


def test_parsing_json_default(testapp):
    with testapp.test_request_context('/myendpoint', method='post',
                                    data=json.dumps({}),
                                    content_type='application/json'):
        args = parser.parse(hello_args)
        assert args == {'name': 'World'}


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
    argmap = {'value': Arg(validate=lambda x: x == 42, type_=int)}
    with testapp.test_request_context('/foo', method='post',
        data=json.dumps({'value': 41}), content_type='application/json'):
        parser.parse(argmap)
        assert mock_abort.called_once_with(400)

@mock.patch('webargs.flaskparser.abort')
def test_abort_called_on_type_conversion_error(mock_abort, testapp):
    argmap = {'value': Arg(type_=int)}
    with testapp.test_request_context('/foo', method='post',
        data=json.dumps({'value': 'badinput'}), content_type='application/json'):
        parser.parse(argmap)
        assert mock_abort.called_once_with(400)

def test_use_args_decorator(testapp):
    @testapp.route('/foo/', methods=['post', 'get'])
    @parser.use_args({'myvalue': Arg(type_=int)})
    def echo(args):
        return jsonify(args)
    test_client = testapp.test_client()
    res = test_client.post('/foo/', data={'myvalue': 23})
    assert json.loads(res.data.decode('utf-8')) == {'myvalue': 23}


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

def test_multiple_arg_allowed_missing(testapp):
    args = {'name': Arg(str, multiple=True, allow_missing=True)}
    with testapp.test_request_context(path='/foo', method='post'):
        args = parser.parse(args)
        assert 'name' not in args

def test_parsing_headers(testapp):
    with testapp.test_request_context('/foo', headers={'Name': 'Fred'}):
        args = parser.parse(hello_args, targets=('headers',))
        # Header key is lowercased
        assert args['name'] == 'Fred'

def test_parsing_cookies(testapp):
    @testapp.route('/getcookiearg')
    def echo():
        args = parser.parse(hello_args, targets=('cookies',))
        return jsonify(args)
    testclient = testapp.test_client()
    testclient.set_cookie('localhost', key='name', value='Fred')
    res = testclient.get('/getcookiearg')
    assert json.loads(res.data.decode('utf-8')) == {'name': 'Fred'}

def test_parse_form_returns_none_if_no_form():
    req = mock.Mock()
    req.form.get.side_effect = AttributeError('no form')
    assert parser.parse_form(req, 'foo', Arg()) is None

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
        args = parser.parse(file_args, targets=('files', ))
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

def test_parse_multiple_arg_with_single_value(testapp):
    multargs = {'name': Arg(multiple=True)}
    with testapp.test_request_context('/foo?name=steve'):
        args = parser.parse(multargs)
        assert args['name'] == ['steve']

def test_parse_multiple_arg_defaults_to_empty_list(testapp):
    multargs = {'name': Arg(multiple=True)}
    with testapp.test_request_context('/foo'):
        args = parser.parse(multargs)
        assert args['name'] == []

def test_parse_multiple_json(testapp):
    multargs = {'name': Arg(multiple=True)}
    with testapp.test_request_context('/foo', data=json.dumps({'name': 'steve'}),
            content_type='application/json', method='POST'):
        args = parser.parse(multargs, targets=('json',))
        assert args['name'] == ['steve']
