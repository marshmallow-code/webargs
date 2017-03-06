from __future__ import absolute_import

from webargs import core


class TwistedParser(core.Parser):

    def parse_json(self, req, name, field):
        ctype = req.getHeader('Content-Type')
        if ctype and core.is_json(ctype):
            body = req.content.read()
            req.content.seek(0)  # reset offset for further reads
            try:
                data = core.parse_json(body)
                return core.get_value(data, name, field)
            except (TypeError, ValueError):
                raise ValueError("Invalid json payload")
        return core.missing

    def parse_querystring(self, req, name, field):
        return self.get_val(req.args.get, name, field)

    def parse_form(self, req, name, field):
        # TODO: check for multipart flag.
        # Form values are stored in args as well.
        return self.get_val(req.args.get, name, field)

    def parse_headers(self, req, name, field):
        return self.get_val(req.requestHeaders.getRawHeaders, name, field)

    def parse_cookies(self, req, name, field):
        return self.get_val(req.getCookie, name, field)

    def get_val(self, getter, name, field):
        values = getter(name)
        if values:
            if not isinstance(values, list):
                values = [values]
            return values if core.is_multiple(field) else values[-1]
        else:
            return [] if core.is_multiple(field) else core.missing

    def get_request_from_view_args(self, func, args, kwargs):
        # First argument is request.
        return args[0]


parser = TwistedParser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs
