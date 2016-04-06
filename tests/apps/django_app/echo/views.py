import json
from django.http import HttpResponse
from django.views.generic import View

import marshmallow as ma
from webargs import fields, ValidationError
from webargs.djangoparser import parser, use_args, use_kwargs

hello_args = {
    'name': fields.Str(missing='World', validate=lambda n: len(n) >= 3),
}
hello_multiple = {
    'name': fields.List(fields.Str())
}

class HelloSchema(ma.Schema):
    name = fields.Str(missing='World', validate=lambda n: len(n) >= 3)

hello_many_schema = HelloSchema(strict=True, many=True)

def json_response(data, **kwargs):
    return HttpResponse(
        json.dumps(data),
        content_type='application/json',
        **kwargs
    )

def echo(request):
    try:
        args = parser.parse(hello_args, request)
    except ValidationError as err:
        return json_response(err.messages, status=err.status_code)
    return json_response(args)

def echo_query(request):
    return json_response(parser.parse(hello_args, request, locations=('query', )))

@use_args(hello_args)
def echo_use_args(request, args):
    return json_response(args)

@use_kwargs(hello_args)
def echo_use_kwargs(request, name):
    return json_response({'name': name})

def echo_multi(request):
    return json_response(parser.parse(hello_multiple, request))

def echo_many_schema(request):
    try:
        return json_response(parser.parse(hello_many_schema, request, locations=('json', )))
    except ValidationError as err:
        return json_response(err.messages, status=err.status_code)

@use_args({'value': fields.Int()})
def echo_use_args_with_path_param(request, args, name):
    return json_response(args)

@use_kwargs({'value': fields.Int()})
def echo_use_kwargs_with_path_param(request, value, name):
    return json_response({'value': value})

def always_error(request):
    def always_fail(value):
        raise ValidationError('something went wrong')
    argmap = {'text': fields.Str(validate=always_fail)}
    try:
        return parser.parse(argmap, request)
    except ValidationError as err:
        return json_response(err.messages, status=err.status_code)

def error400(request):
    def always_fail(value):
        raise ValidationError('something went wrong', status_code=400)
    argmap = {'text': fields.Str(validate=always_fail)}
    try:
        return parser.parse(argmap, request)
    except ValidationError as err:
        return json_response(err.messages, status=err.status_code)

def echo_headers(request):
    return json_response(parser.parse(hello_args, request, locations=('headers', )))

def echo_cookie(request):
    return json_response(parser.parse(hello_args, request, locations=('cookies',)))

def echo_file(request):
    args = {'myfile': fields.Field()}
    result = parser.parse(args, request, locations=('files', ))
    myfile = result['myfile']
    content = myfile.read().decode('utf8')
    return json_response({'myfile': content})

def echo_nested(request):
    argmap = {
        'name': fields.Nested({'first': fields.Str(),
                     'last': fields.Str()})
    }
    return json_response(parser.parse(argmap, request))

def echo_nested_many(request):
    argmap = {
        'users': fields.Nested({'id': fields.Int(), 'name': fields.Str()}, many=True)
    }
    return json_response(parser.parse(argmap, request))

class EchoCBV(View):
    def get(self, request):
        try:
            args = parser.parse(hello_args, self.request)
        except ValidationError as err:
            return json_response(err.messages, status=err.status_code)
        return json_response(args)
    post = get

class EchoUseArgsCBV(View):
    @use_args(hello_args)
    def get(self, request, args):
        return json_response(args)
    post = get

class EchoUseArgsWithParamCBV(View):
    @use_args(hello_args)
    def get(self, request, args, pid):
        return json_response(args)
    post = get
