import json
from bottle import Bottle, HTTPResponse, debug, request, response, error

import marshmallow as ma
from webargs import fields, ValidationError
from webargs.bottleparser import parser, use_args, use_kwargs

hello_args = {
    'name': fields.Str(missing='World', validate=lambda n: len(n) >= 3),
}
hello_multiple = {
    'name': fields.List(fields.Str())
}

class HelloSchema(ma.Schema):
    name = fields.Str(missing='World', validate=lambda n: len(n) >= 3)

hello_many_schema = HelloSchema(strict=True, many=True)


app = Bottle()
debug(True)

@app.route('/echo', method=['GET', 'POST'])
def echo():
    return parser.parse(hello_args, request)

@app.route('/echo_query')
def echo_query():
    return parser.parse(hello_args, request, locations=('query', ))

@app.route('/echo_use_args', method=['GET', 'POST'])
@use_args(hello_args)
def echo_use_args(args):
    return args

@app.route('/echo_use_kwargs', method=['GET', 'POST'])
@use_kwargs(hello_args)
def echo_use_kwargs(name):
    return {'name': name}

@app.route('/echo_use_args_validated', method=['GET', 'POST'])
@use_args({'value': fields.Int()}, validate=lambda args: args['value'] > 42)
def echo_use_args_validated(args):
    return args

@app.route('/echo_multi', method=['GET', 'POST'])
def echo_multi():
    return parser.parse(hello_multiple, request)

@app.route('/echo_many_schema', method=['GET', 'POST'])
def echo_many_schema():
    arguments = parser.parse(hello_many_schema, request, locations=('json', ))
    return HTTPResponse(body=json.dumps(arguments), content_type='application/json')

@app.route('/echo_use_args_with_path_param/<name>')
@use_args({'value': fields.Int()})
def echo_use_args_with_path_param(args, name):
    return args

@app.route('/echo_use_kwargs_with_path_param/<name>')
@use_kwargs({'value': fields.Int()})
def echo_use_kwargs_with_path_param(name, value):
    return {'value': value}

@app.route('/error', method=['GET', 'POST'])
def always_error():
    def always_fail(value):
        raise ValidationError('something went wrong')
    args = {'text': fields.Str(validate=always_fail)}
    return parser.parse(args)

@app.route('/error400', method=['GET', 'POST'])
def error400():
    def always_fail(value):
        raise ValidationError('something went wrong', status_code=400)
    args = {'text': fields.Str(validate=always_fail)}
    return parser.parse(args)

@app.route('/echo_headers')
def echo_headers():
    return parser.parse(hello_args, request, locations=('headers', ))

@app.route('/echo_cookie')
def echo_cookie():
    return parser.parse(hello_args, request, locations=('cookies',))

@app.route('/echo_file', method=['POST'])
def echo_file():
    args = {'myfile': fields.Field()}
    result = parser.parse(args, locations=('files', ))
    myfile = result['myfile']
    content = myfile.file.read().decode('utf8')
    return {'myfile': content}

@app.route('/echo_nested', method=['POST'])
def echo_nested():
    args = {
        'name': fields.Nested({'first': fields.Str(),
                     'last': fields.Str()})
    }
    return parser.parse(args)

@app.route('/echo_nested_many', method=['POST'])
def echo_nested_many():
    args = {
        'users': fields.Nested({'id': fields.Int(), 'name': fields.Str()}, many=True)
    }
    return parser.parse(args)

@error(422)
def handle_422(err):
    response.content_type = 'application/json'
    return err.body
