"""A simple number and datetime addition JSON API.
Run the app:

    $ python examples/pyramid_example.py

Try the following with httpie (a cURL-like utility, http://httpie.org):

    $ pip install httpie
    $ http GET :5001/
    $ http GET :5001/ name==Ada
    $ http POST :5001/add x=40 y=2
    $ http POST :5001/dateadd value=1973-04-10 addend=63
    $ http POST :5001/dateadd value=2014-10-23 addend=525600 unit=minutes
"""

import datetime as dt

from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.view import view_config
from pyramid.renderers import JSON
from webargs import fields, validate
from webargs.pyramidparser import use_args, use_kwargs


hello_args = {"name": fields.Str(missing="Friend")}


@view_config(route_name="hello", request_method="GET", renderer="json")
@use_args(hello_args)
def index(request, args):
    """A welcome page.
    """
    return {"message": "Welcome, {}!".format(args["name"])}


add_args = {"x": fields.Float(required=True), "y": fields.Float(required=True)}


@view_config(route_name="add", request_method="POST", renderer="json")
@use_kwargs(add_args)
def add(request, x, y):
    """An addition endpoint."""
    return {"result": x + y}


dateadd_args = {
    "value": fields.Date(required=False),
    "addend": fields.Int(required=True, validate=validate.Range(min=1)),
    "unit": fields.Str(missing="days", validate=validate.OneOf(["minutes", "days"])),
}


@view_config(route_name="dateadd", request_method="POST", renderer="json")
@use_kwargs(dateadd_args)
def dateadd(request, value, addend, unit):
    """A date adder endpoint."""
    value = value or dt.datetime.utcnow()
    if unit == "minutes":
        delta = dt.timedelta(minutes=addend)
    else:
        delta = dt.timedelta(days=addend)
    result = value + delta
    return {"result": result}


if __name__ == "__main__":
    config = Configurator()

    json_renderer = JSON()
    json_renderer.add_adapter(dt.datetime, lambda v, request: v.isoformat())
    config.add_renderer("json", json_renderer)

    config.add_route("hello", "/")
    config.add_route("add", "/add")
    config.add_route("dateadd", "/dateadd")
    config.scan(__name__)
    app = config.make_wsgi_app()
    server = make_server("0.0.0.0", 5001, app)
    server.serve_forever()
