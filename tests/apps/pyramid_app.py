from pyramid.config import Configurator
import marshmallow as ma

from webargs import fields, ValidationError
from webargs.pyramidparser import parser, use_args, use_kwargs

hello_args = {
    'name': fields.Str(missing='World', validate=lambda n: len(n) >= 3),
}
hello_multiple = {
    'name': fields.List(fields.Str())
}

class HelloSchema(ma.Schema):
    name = fields.Str(missing='World', validate=lambda n: len(n) >= 3)

hello_many_schema = HelloSchema(strict=True, many=True)

def echo(request):
    return parser.parse(hello_args, request)

def echo_query(request):
    return parser.parse(hello_args, request, locations=('query', ))

@use_args(hello_args)
def echo_use_args(request, args):
    return args

@use_args({'value': fields.Int()}, validate=lambda args: args['value'] > 42)
def echo_use_args_validated(request, args):
    return args

@use_kwargs(hello_args)
def echo_use_kwargs(request, name):
    return {'name': name}

def echo_multi(request):
    return parser.parse(hello_multiple, request)

def echo_many_schema(request):
    return parser.parse(hello_many_schema, request, locations=('json', ))

@use_args({'value': fields.Int()})
def echo_use_args_with_path_param(request, args):
    return args

@use_kwargs({'value': fields.Int()})
def echo_use_kwargs_with_path_param(request, value):
    return {'value': value}

def always_error(request):
    def always_fail(value):
        raise ValidationError('something went wrong')
    argmap = {'text': fields.Str(validate=always_fail)}
    return parser.parse(argmap, request)

def error400(request):
    def always_fail(value):
        raise ValidationError('something went wrong', status_code=400)
    argmap = {'text': fields.Str(validate=always_fail)}
    return parser.parse(argmap, request)

def echo_headers(request):
    return parser.parse(hello_args, request, locations=('headers', ))

def echo_cookie(request):
    return parser.parse(hello_args, request, locations=('cookies',))

def echo_file(request):
    args = {'myfile': fields.Field()}
    result = parser.parse(args, request, locations=('files', ))
    myfile = result['myfile']
    content = myfile.file.read().decode('utf8')
    return {'myfile': content}

def echo_nested(request):
    argmap = {
        'name': fields.Nested({'first': fields.Str(),
                     'last': fields.Str()})
    }
    return parser.parse(argmap, request)

def echo_nested_many(request):
    argmap = {
        'users': fields.Nested({'id': fields.Int(), 'name': fields.Str()}, many=True)
    }
    return parser.parse(argmap, request)

def echo_matchdict(request):
    return parser.parse({'mymatch': fields.Int()}, request, locations=('matchdict', ))

class EchoCallable(object):
    def __init__(self, request):
        self.request = request

    @use_args({'value': fields.Int()})
    def __call__(self, args):
        return args


def add_route(config, route, view, route_name=None, renderer='json'):
    """Helper for adding a new route-view pair."""
    route_name = route_name or view.__name__
    config.add_route(route_name, route)
    config.add_view(view, route_name=route_name, renderer=renderer)

def create_app():
    config = Configurator()

    add_route(config, '/echo', echo)
    add_route(config, '/echo_query', echo_query)
    add_route(config, '/echo_use_args', echo_use_args)
    add_route(config, '/echo_use_args_validated', echo_use_args_validated)
    add_route(config, '/echo_use_kwargs', echo_use_kwargs)
    add_route(config, '/echo_multi', echo_multi)
    add_route(config, '/echo_many_schema', echo_many_schema)
    add_route(config, '/echo_use_args_with_path_param/{name:\w+}',
              echo_use_args_with_path_param)
    add_route(config, '/echo_use_kwargs_with_path_param/{name:\w+}',
              echo_use_kwargs_with_path_param)
    add_route(config, '/error', always_error)
    add_route(config, '/error400', error400)
    add_route(config, '/echo_headers', echo_headers)
    add_route(config, '/echo_cookie', echo_cookie)
    add_route(config, '/echo_file', echo_file)
    add_route(config, '/echo_nested', echo_nested)
    add_route(config, '/echo_nested_many', echo_nested_many)
    add_route(config, '/echo_callable', EchoCallable)
    add_route(config, '/echo_matchdict/{mymatch:\d+}', echo_matchdict)

    return config.make_wsgi_app()
