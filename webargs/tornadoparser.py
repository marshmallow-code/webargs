# -*- coding: utf-8 -*-
"""Tornado request argument parsing module.

Example: ::

    import tornado.web
    from marshmallow import fields
    from webargs.tornadoparser import use_args

    class HelloHandler(tornado.web.RequestHandler):

        @use_args({'name': fields.Str(missing='World')})
        def get(self, args):
            response = {'message': 'Hello {}'.format(args['name'])}
            self.write(response)
"""
import tornado.web
from tornado.escape import _unicode

from marshmallow.compat import basestring
from webargs import core


class HTTPError(tornado.web.HTTPError):
    """`tornado.web.HTTPError` that stores validation errors."""

    def __init__(self, *args, **kwargs):
        self.messages = kwargs.pop('messages', {})
        super(HTTPError, self).__init__(*args, **kwargs)

def parse_json_body(req):
    """Return the decoded JSON body from the request."""
    content_type = req.headers.get('Content-Type')
    if content_type and core.is_json(content_type):
        try:
            return core.parse_json(req.body)
        except (TypeError, ValueError):
            pass
    return {}

# From tornado.web.RequestHandler.decode_argument
def decode_argument(value, name=None):
    """Decodes an argument from the request.
    """
    try:
        return _unicode(value)
    except UnicodeDecodeError:
        raise HTTPError(400, 'Invalid unicode in %s: %r' %
                        (name or 'url', value[:40]))

def get_value(d, name, field):
    """Handle gets from 'multidicts' made of lists

    It handles cases: ``{"key": [value]}`` and ``{"key": value}``
    """
    multiple = core.is_multiple(field)
    value = d.get(name, core.missing)
    if value is core.missing:
        return core.missing
    if multiple and value is not core.missing:
        return [decode_argument(v, name) if isinstance(v, basestring) else v
                for v in value]
    ret = value
    if value and isinstance(value, (list, tuple)):
        ret = value[0]
    if isinstance(ret, basestring):
        return decode_argument(ret, name)
    else:
        return ret

class TornadoParser(core.Parser):
    """Tornado request argument parser."""

    def __init__(self, *args, **kwargs):
        super(TornadoParser, self).__init__(*args, **kwargs)
        self.json = None

    def parse_json(self, req):
        """Pull a json value from the request."""
        json_data = self._cache.get('json')
        if json_data is None:
            self._cache['json'] = json_data = parse_json_body(req)
            if json_data is None:
                return {}
        return json_data

    def parse_querystring(self, req):
        """Pull a querystring value from the request."""
        return self._flatten_multidict(req.query_arguments)

    def parse_form(self, req):
        """Pull a form value from the request."""
        return self._flatten_multidict(req.body_arguments)

    def parse_headers(self, req):
        """Pull a value from the header data."""
        return req.headers

    def parse_cookies(self, req):
        """Pull a value from the header data."""
        return self._flatten_cookies(req.cookies)

    def parse_files(self, req):
        """Pull a file from the request."""
        return self._flatten_files(req.files)

    def handle_error(self, error):
        """Handles errors during parsing. Raises a `tornado.web.HTTPError`
        with a 400 error.
        """
        status_code = getattr(error, 'status_code', core.DEFAULT_VALIDATION_STATUS)
        if status_code == 422:
            reason = 'Unprocessable Entity'
        else:
            reason = None
        raise HTTPError(status_code, log_message=str(error.messages),
                reason=reason, messages=error.messages)

    def get_request_from_view_args(self, view, args, kwargs):
        return args[0].request

    def _flatten_multidict(self, multidict):
        flat = {}
        for key, value in multidict.items():
            if len(value) == 1:
                flat[key] = value[0].decode('utf-8')
            else:
                flat[key] = list(map(lambda x: x.decode('utf-8'), value))
        return flat

    def _flatten_files(self, multidict):
        flat = {}
        for key, value in multidict.items():
            if len(value) == 1:
                flat[key] = value[0]
            else:
                flat[key] = value
        return flat

    def _flatten_cookies(self, cookies):
        flat = {}
        for key, value in cookies.items():
            current = flat.get(key)
            if current is None:
                flat[key] = value.value
            elif isinstance(current, list):
                current.append(value.value)
            else:
                flat[key] = [current, value.value]
        return flat

parser = TornadoParser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs
