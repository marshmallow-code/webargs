# -*- coding: utf-8 -*-
from flask import request
from flask import abort as flask_abort
from werkzeug.exceptions import HTTPException

from webargs import core

def abort(http_status_code, **kwargs):
    """Raise a HTTPException for the given http_status_code. Attach any keyword
    arguments to the exception for later processing.

    From Flask-Restful. See NOTICE file for license information.
    """
    try:
        flask_abort(http_status_code)
    except HTTPException as err:
        if len(kwargs):
            err.data = kwargs
        raise err


class FlaskParser(core.Parser):

    def parse_json(self, req, name):
        """Pull the json value from the request."""
        try:
            return req.json.get(name, None)
        except AttributeError:
            return None

    def parse_querystring(self, req, name):
        """Pull the querystring value from the request."""
        try:
            return req.args.get(name, None)
        except AttributeError:
            return None

    def parse_form(self, req, name):
        """Pull the form value from the request."""
        try:
            return req.form.get(name, None)
        except AttributeError:
            return None

    def parse_headers(self, req, name):
        """Pull the value from the header data."""
        return req.headers.get(name, None)

    def parse_cookies(self, req, name):
        return req.cookies.get(name, None)

    def handle_error(self, error):
        abort(400, message=error)

    def parse(self, argmap, req=None, *args, **kwargs):
        req_obj = req or request
        return super(FlaskParser, self).parse(argmap, req_obj, *args, **kwargs)
