import pytest
import webtest_aiohttp
from aiohttp.web import Application, json_response

from webargs import fields
from webargs.aiohttpparser import parser, use_args, use_kwargs

##### Test app handlers #####

hello_args = {"name": fields.Str(missing="World", validate=lambda n: len(n) >= 3)}


async def echo_parse(request):
    parsed = await parser.parse(hello_args, request, location="query")
    return json_response(parsed)


@use_args(hello_args, location="query")
async def echo_use_args(request, args):
    return json_response(args)


@use_kwargs(hello_args, location="query")
async def echo_use_kwargs(request, name):
    return json_response({"name": name})


##### Fixtures #####


@pytest.fixture()
def app():
    app_ = Application()
    app_.router.add_route("GET", "/echo", echo_parse)
    app_.router.add_route("GET", "/echo_use_args", echo_use_args)
    app_.router.add_route("GET", "/echo_use_kwargs", echo_use_kwargs)
    return app_


@pytest.fixture()
def testapp(app, loop):
    return webtest_aiohttp.TestApp(app, loop=loop)


##### Tests #####


def test_async_parse(testapp):
    assert testapp.get("/echo?name=Steve").json == {"name": "Steve"}


def test_async_use_args(testapp):
    assert testapp.get("/echo_use_args?name=Steve").json == {"name": "Steve"}


def test_async_use_kwargs(testapp):
    assert testapp.get("/echo_use_kwargs?name=Steve").json == {"name": "Steve"}
