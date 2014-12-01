# -*- coding: utf-8 -*-
"""Pyramid request argument parsing.
"""
import logging

from webargs import core

logger = logging.getLogger(__name__)

class PyramidParser(core.Parser):
    """Pyramid request argument parser."""

    def parse_querystring(self, req, name, arg):
        """Pull a querystring value from the request."""
        return core.get_value(req.GET, name, arg.multiple)

    def parse_form(self, req, name, arg):
        """Pull a form value from the request."""
        return core.get_value(req.POST, name, arg.multiple)

    def parse_json(self, req, name, arg):
        """Pull a json value from the request."""
        try:
            json_data = req.json_body
        except ValueError:
            return core.Missing

        return core.get_value(json_data, name, arg.multiple)

    def parse_cookies(self, req, name, arg):
        """Pull the value from the cookiejar."""
        return core.get_value(req.cookies, name, arg.multiple)

    def parse_headers(self, req, name, arg):
        """Pull a value from the header data."""
        return core.get_value(req.headers, name, arg.multiple)

    def parse_files(self, req, name, arg):
        raise NotImplementedError('Files parsing not supported by {0}'
            .format(self.__class__.__name__))

parser = PyramidParser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs
