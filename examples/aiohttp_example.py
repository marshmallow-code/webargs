"""A simple number and datetime addition JSON API.
Run the app:

    $ python examples/aiohttp_example.py

Try the following with httpie (a cURL-like utility, http://httpie.org):

    $ pip install httpie
    $ http GET :5001/
    $ http GET :5001/ name==Ada
    $ http POST :5001/add x=40 y=2
    $ http POST :5001/dateadd value=1973-04-10 addend=63
    $ http POST :5001/dateadd value=2014-10-23 addend=525600 unit=minutes
"""
import asyncio
import datetime as dt

from aiohttp import web
from aiohttp.web import json_response
from webargs import fields, validate
from webargs.aiohttpparser import use_args, use_kwargs

hello_args = {
    'name': fields.Str(missing='Friend')
}
@asyncio.coroutine
@use_args(hello_args)
def index(request, args):
    """A welcome page.
    """
    return json_response({'message': 'Welcome, {}!'.format(args['name'])})

add_args = {
    'x': fields.Float(required=True),
    'y': fields.Float(required=True),
}
@asyncio.coroutine
@use_kwargs(add_args)
def add(request, x, y):
    """An addition endpoint."""
    return json_response({'result': x + y})

dateadd_args = {
    'value': fields.DateTime(required=False),
    'addend': fields.Int(required=True, validate=validate.Range(min=1)),
    'unit': fields.Str(missing='days', validate=validate.OneOf(['minutes', 'days']))
}
@asyncio.coroutine
@use_kwargs(dateadd_args)
def dateadd(request, value, addend, unit):
    """A datetime adder endpoint."""
    value = value or dt.datetime.utcnow()
    if unit == 'minutes':
        delta = dt.timedelta(minutes=addend)
    else:
        delta = dt.timedelta(days=addend)
    result = value + delta
    return json_response({'result': result.isoformat()})


def create_app():
    app = web.Application()
    app.router.add_route('GET', '/', index)
    app.router.add_route('POST', '/add', add)
    app.router.add_route('POST', '/dateadd', dateadd)
    return app

def run(app, port=5001):
    loop = asyncio.get_event_loop()
    handler = app.make_handler()
    f = loop.create_server(handler, '0.0.0.0', port)
    srv = loop.run_until_complete(f)
    print('serving on', srv.sockets[0].getsockname())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(handler.finish_connections(1.0))
        srv.close()
        loop.run_until_complete(srv.wait_closed())
        loop.run_until_complete(app.finish())
    loop.close()

if __name__ == '__main__':
    app = create_app()
    run(app)
