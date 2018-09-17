# -*- coding: utf-8 -*-
"""Sanic request argument parsing module.

Example: ::

    from sanic import Sanic

    from webargs import fields
    from webargs.sanicparser import use_args

    app = Sanic(__name__)

    hello_args = {
        'name': fields.Str(required=True)
    }

    @app.route('/')
    @use_args(hello_args)
    async def index(args):
        return 'Hello ' + args['name']
"""
import sanic

from webargs import core
from webargs.asyncparser import AsyncParser


@sanic.exceptions.add_status_code(422)
class HandleValidationError(sanic.exceptions.SanicException):
    pass


def abort(http_status_code, exc=None, **kwargs):
    """Raise a HTTPException for the given http_status_code. Attach any keyword
    arguments to the exception for later processing.

    From Flask-Restful. See NOTICE file for license information.
    """
    try:
        sanic.exceptions.abort(http_status_code, exc)
    except sanic.exceptions.SanicException as err:
        err.data = kwargs
        err.exc = exc
        raise err


def is_json_request(req):
    content_type = req.content_type
    return core.is_json(content_type)


class SanicParser(AsyncParser):
    """Sanic request argument parser."""

    __location_map__ = dict(view_args="parse_view_args", **core.Parser.__location_map__)

    def parse_view_args(self, req, name, field):
        """Pull a value from the request's ``view_args``."""
        return core.get_value(req.match_info, name, field)

    def get_request_from_view_args(self, view, args, kwargs):
        """Get request object from a handler function or method. Used internally by
        ``use_args`` and ``use_kwargs``.
        """
        if len(args) > 1 and isinstance(args[1], sanic.request.Request):
            req = args[1]
        else:
            req = args[0]
        assert isinstance(
            req, sanic.request.Request
        ), "Request argument not found for handler"
        return req

    def parse_json(self, req, name, field):
        """Pull a json value from the request."""
        if not (req.body and is_json_request(req)):
            return core.missing
        json_data = req.json
        if json_data is None:
            return core.missing
        return core.get_value(json_data, name, field, allow_many_nested=True)

    def parse_querystring(self, req, name, field):
        """Pull a querystring value from the request."""
        return core.get_value(req.args, name, field)

    def parse_form(self, req, name, field):
        """Pull a form value from the request."""
        try:
            return core.get_value(req.form, name, field)
        except AttributeError:
            pass
        return core.missing

    def parse_headers(self, req, name, field):
        """Pull a value from the header data."""
        return core.get_value(req.headers, name, field)

    def parse_cookies(self, req, name, field):
        """Pull a value from the cookiejar."""
        return core.get_value(req.cookies, name, field)

    def parse_files(self, req, name, field):
        """Pull a file from the request."""
        return core.get_value(req.files, name, field)

    def handle_error(self, error, req, schema):
        """Handles errors during parsing. Aborts the current HTTP request and
        responds with a 422 error.
        """

        status_code = getattr(error, "status_code", self.DEFAULT_VALIDATION_STATUS)
        abort(status_code, exc=error, messages=error.messages, schema=schema)


parser = SanicParser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs
