# -*- coding: utf-8 -*-
import json

from webargs import core


class DjangoParser(core.Parser):

    def parse_querystring(self, req, name):
        """Pull the querystring value from the request."""
        try:
            return req.GET.get(name, None)
        except AttributeError:
            return None

    def parse_form(self, req, name):
        """Pull the form value from the request."""
        try:
            return req.POST.get(name, None)
        except AttributeError:
            return None

    def parse_json(self, req, name):
        """Pull a json value from the request body."""
        try:
            reqdata = json.loads(req.body)
            return reqdata.get(name, None)
        except Exception:
            return None

    def parse_cookies(self, req, name):
        """Pull the value from the cookiejar."""
        try:
            return req.COOKIES.get(name, None)
        except AttributeError:
            return None
