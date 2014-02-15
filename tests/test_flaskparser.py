# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import mock

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException
import pytest

from webargs import Arg
from webargs.compat import text_type
from webargs.flaskparser import FlaskParser, use_args, abort

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


def test_parsing_json_default(testapp):
    with testapp.test_request_context('/myendpoint', method='post',
                                    data=json.dumps({}),
                                    content_type='application/json'):
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

@mock.patch('webargs.flaskparser.abort')
def test_abort_called_when_required_arg_not_present(mock_abort, testapp):
    args = {'required': Arg(required=True)}
    with testapp.test_request_context('/foo', method='post',
        data=json.dumps({}), content_type='application/json'):
        parser.parse(args)
        assert mock_abort.called_once_with(400)

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

def test_unicode_arg(testapp):
    with testapp.test_request_context('/foo?name=Früd'):
        args = parser.parse(hello_args)
        assert args['name'] == 'Früd'

def test_abort_with_message():
    with pytest.raises(HTTPException) as excinfo:
        abort(400, message='custom error message')
    assert excinfo.value.data['message'] == 'custom error message'
