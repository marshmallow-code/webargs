import json

from klein.test.test_resource import requestMock
from marshmallow import missing

from webargs.twistedparser import parser


def test_parse_json(data={"foo": "bar"}):
    req = requestMock(b'/path',
                      body=json.dumps(data).encode(),
                      headers={'content-type': ['application/json']})

    assert parser.parse_json(req, 'foo', 'field') == data.get('foo')
    assert parser.parse_json(req, 'bar', 'field') is missing


def test_parse_json_big():
    test_parse_json({"foo": 'bar' * 1024 * 1024})
