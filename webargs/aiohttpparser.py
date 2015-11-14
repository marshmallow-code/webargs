# -*- coding: utf-8 -*-
"""aiohttp request argument parsing module.

Example: ::

    import asyncio
    from aiohttp import web

    from webargs import fields
    from webargs.aiohttpparser import use_args


    hello_args = {
        'name': fields.Str(required=True)
    }
    @asyncio.coroutine
    @use_args(hello_args)
    def index(request, args):
        return web.Response(
            body='Hello {}'.format(args['name']).encode('utf-8')
        )

    app = web.Application()
    app.router.add_route('GET', '/', index)
"""
import asyncio
import json

from aiohttp import web

from webargs import core
from webargs.async import AsyncParser


def is_json_request(req):
    content_type = req.content_type
    return core.is_json(content_type)


class HTTPUnprocessableEntity(web.HTTPClientError):
    status_code = 422


class AIOHTTPParser(AsyncParser):
    """aiohttp request argument parser."""

    __location_map__ = dict(
        match_info='parse_match_info',
        **core.Parser.__location_map__
    )

    def parse_querystring(self, req, name, field):
        """Pull a querystring value from the request."""
        return core.get_value(req.GET, name, field)

    @asyncio.coroutine
    def parse_form(self, req, name, field):
        """Pull a form value from the request."""
        post_data = self._cache.get('post')
        if post_data is None:
            yield from req.post()
            self._cache['post'] = req.POST
        return core.get_value(self._cache['post'], name, field)

    @asyncio.coroutine
    def parse_json(self, req, name, field):
        """Pull a json value from the request."""
        if req.has_body and is_json_request(req):
            json_data = self._cache.get('json')
            if json_data is None:
                self._cache['json'] = yield from req.json()
            return core.get_value(self._cache['json'], name, field)
        else:
            return core.missing

    def parse_headers(self, req, name, field):
        """Pull a value from the header data."""
        return core.get_value(req.headers, name, field)

    def parse_cookies(self, req, name, field):
        """Pull a value from the cookiejar."""
        return core.get_value(req.cookies, name, field)

    def parse_files(self, req, name, field):
        raise NotImplementedError(
            'parse_files is not implemented. You may be able to use parse_form for '
            'parsing upload data.'
        )

    def parse_match_info(self, req, name, field):
        """Pull a value from the request's ``match_info``."""
        return core.get_value(req.match_info, name, field)

    def get_request_from_view_args(self, view, args, kwargs):
        """Get request object from a handler function or method. Used internally by
        ``use_args`` and ``use_kwargs``.
        """
        if len(args) > 1:
            req = args[1]
        else:
            req = args[0]
        assert isinstance(req, web.Request), 'Request argument not found for handler'
        return req

    def handle_error(self, error):
        """Handle ValidationErrors and return a JSON response of error messages to the client."""
        raise HTTPUnprocessableEntity(
            body=json.dumps(error.messages).encode('utf-8'),
            content_type='application/json'
        )


parser = AIOHTTPParser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs
