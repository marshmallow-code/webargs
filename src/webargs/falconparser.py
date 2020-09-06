"""Falcon request argument parsing module.
"""
import falcon
from falcon.util.uri import parse_query_string

from webargs import core
from webargs.multidictproxy import MultiDictProxy

HTTP_422 = "422 Unprocessable Entity"

# Mapping of int status codes to string status
status_map = {422: HTTP_422}


# Collect all exceptions from falcon.status_codes
def _find_exceptions():
    for name in filter(lambda n: n.startswith("HTTP"), dir(falcon.status_codes)):
        status = getattr(falcon.status_codes, name)
        status_code = int(status.split(" ")[0])
        status_map[status_code] = status


_find_exceptions()
del _find_exceptions


def is_json_request(req):
    content_type = req.get_header("Content-Type")
    return content_type and core.is_json(content_type)


# NOTE: Adapted from falcon.request.Request._parse_form_urlencoded
def parse_form_body(req):
    if (
        req.content_type is not None
        and "application/x-www-form-urlencoded" in req.content_type
    ):
        body = req.stream.read(req.content_length or 0)
        try:
            body = body.decode("ascii")
        except UnicodeDecodeError:
            body = None
            req.log_error(
                "Non-ASCII characters found in form body "
                "with Content-Type of "
                "application/x-www-form-urlencoded. Body "
                "will be ignored."
            )

        if body:
            return parse_query_string(body, keep_blank=req.options.keep_blank_qs_values)

    return core.missing


class HTTPError(falcon.HTTPError):
    """HTTPError that stores a dictionary of validation error messages."""

    def __init__(self, status, errors, *args, **kwargs):
        self.errors = errors
        super().__init__(status, *args, **kwargs)

    def to_dict(self, *args, **kwargs):
        """Override `falcon.HTTPError` to include error messages in responses."""
        ret = super().to_dict(*args, **kwargs)
        if self.errors is not None:
            ret["errors"] = self.errors
        return ret


class FalconParser(core.Parser):
    """Falcon request argument parser."""

    # Note on the use of MultiDictProxy throughout:
    # Falcon parses query strings and form values into ordinary dicts, but with
    # the values listified where appropriate
    # it is still therefore necessary in these cases to wrap them in
    # MultiDictProxy because we need to use the schema to determine when single
    # values should be wrapped in lists due to the type of the destination
    # field

    def load_querystring(self, req, schema):
        """Return query params from the request as a MultiDictProxy."""
        return MultiDictProxy(req.params, schema)

    def load_form(self, req, schema):
        """Return form values from the request as a MultiDictProxy

        .. note::

            The request stream will be read and left at EOF.
        """
        form = parse_form_body(req)
        if form is core.missing:
            return form
        return MultiDictProxy(form, schema)

    def _raw_load_json(self, req):
        """Return a json payload from the request for the core parser's load_json

        Checks the input mimetype and may return 'missing' if the mimetype is
        non-json, even if the request body is parseable as json."""
        if not is_json_request(req) or req.content_length in (None, 0):
            return core.missing
        body = req.stream.read(req.content_length)
        if body:
            return core.parse_json(body)
        return core.missing

    def load_headers(self, req, schema):
        """Return headers from the request."""
        # Falcon only exposes headers as a dict (not multidict)
        return req.headers

    def load_cookies(self, req, schema):
        """Return cookies from the request."""
        # Cookies are expressed in Falcon as a dict, but the possibility of
        # multiple values for a cookie is preserved internally -- if desired in
        # the future, webargs could add a MultiDict type for Cookies here built
        # from (req, schema), but Falcon does not provide one out of the box
        return req.cookies

    def get_request_from_view_args(self, view, args, kwargs):
        """Get request from a resource method's arguments. Assumes that
        request is the second argument.
        """
        req = args[1]
        if not isinstance(req, falcon.Request):
            raise TypeError("Argument is not a falcon.Request")
        return req

    def load_files(self, req, schema):
        raise NotImplementedError(
            "Parsing files not yet supported by {}".format(self.__class__.__name__)
        )

    def handle_error(self, error, req, schema, *, error_status_code, error_headers):
        """Handles errors during parsing."""
        status = status_map.get(error_status_code or self.DEFAULT_VALIDATION_STATUS)
        if status is None:
            raise LookupError("Status code {} not supported".format(error_status_code))
        raise HTTPError(status, errors=error.messages, headers=error_headers)

    def _handle_invalid_json_error(self, error, req, *args, **kwargs):
        status = status_map[400]
        messages = {"json": ["Invalid JSON body."]}
        raise HTTPError(status, errors=messages)


parser = FalconParser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs
