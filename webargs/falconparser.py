# -*- coding: utf-8 -*-
"""Falcon request argument parsing module.
"""
import logging

import falcon

from webargs import core

logger = logging.getLogger(__name__)

HTTP_422 = '422 Unprocessable entity'

def parse_json_body(req):
    if req.content_length in (None, 0):
        # Nothing to do
        return {}
    content_type = req.get_header('Content-Type')
    if content_type and 'application/json' in content_type:
        body = req.stream.read()
        if body:
            try:
                return core.parse_json(body)
            except (TypeError, ValueError):
                pass
    return {}

class HTTPError(falcon.HTTPError):
    """HTTPError that stores a dictionary of validation error messages.
    """

    def __init__(self, status, errors, *args, **kwargs):
        self.errors = errors
        super(HTTPError, self).__init__(status, *args, **kwargs)

    def to_dict(self, *args, **kwargs):
        """Override `falcon.HTTPError` to include error messages in responses."""
        ret = super(HTTPError, self).to_dict(*args, **kwargs)
        if self.errors is not None:
            ret['errors'] = self.errors
        return ret


class FalconParser(core.Parser):
    """Falcon request argument parser."""

    def parse_querystring(self, req, name, field):
        """Pull a querystring value from the request."""
        return core.get_value(req.params, name, field)

    def parse_form(self, req, name, field):
        """Pull a form value from the request."""
        return core.get_value(req.params, name, field)

    def parse_json(self, req, name, field):
        """Pull a JSON body value from the request."""
        json_body = self._cache.get('json')
        if json_body is None:
            self._cache['json'] = json_body = parse_json_body(req)
        return core.get_value(json_body, name, field)

    def parse_headers(self, req, name, field):
        """Pull a header value from the request."""
        # Use req.get_headers rather than req.headers for performance
        return req.get_header(name, required=False) or core.missing

    def parse_cookies(self, req, name, field):
        """Pull a cookie value from the request."""
        cookies = self._cache.get('cookies')
        if cookies is None:
            self._cache['cookies'] = cookies = req.cookies
        return core.get_value(cookies, name, field)

    def get_request_from_view_args(self, args, kwargs):
        """Get request from a resource method's arguments. Assumes that
        request is the second argument.
        """
        req = args[1]
        assert isinstance(req, falcon.Request), 'Argument is not a falcon.Request'
        return req

    def parse_files(self, req, name, field):
        raise NotImplementedError('Parsing files not yet supported by {0}'
            .format(self.__class__.__name__))

    def handle_error(self, error):
        """Handles errors during parsing."""
        logger.error(error)
        raise HTTPError(HTTP_422, errors=error.messages)

parser = FalconParser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs
