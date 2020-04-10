"""Flask request argument parsing module.

Example: ::

    from flask import Flask

    from webargs import fields
    from webargs.flaskparser import use_args

    app = Flask(__name__)

    hello_args = {
        'name': fields.Str(required=True)
    }

    @app.route('/')
    @use_args(hello_args)
    def index(args):
        return 'Hello ' + args['name']
"""
import flask
from werkzeug.exceptions import default_exceptions
from werkzeug.utils import escape

from webargs import core
from webargs.compat import MARSHMALLOW_VERSION_INFO
from webargs.multidictproxy import MultiDictProxy


class VerboseError:
    """Mixin class for handling verbose error information and additional
    headers.
    """

    def __init__(self, exc, **kwargs):
        # Note that this will call the __init__() of the sibling class to which
        # it is mixed in!
        super().__init__()
        self.exc = exc
        self.messages = kwargs.get("messages")
        self.extra_headers = kwargs.get("headers")
        self.data = kwargs

    def get_description(self, environ):
        if self.messages is None:
            return super().get_description()
        html = []
        for source, errors in self.messages.items():
            html.append(f"<h2>Errors in {escape(source)}</h2>")
            html.append("<p>")
            if isinstance(errors, dict):
                for field, message in errors.items():
                    if isinstance(message, list):
                        message = ", ".join(message)
                    html.append(f"{escape(field)}: {escape(message)}<br>")
            else:
                html.append(escape(errors))
            html.append("</p>")
        return "\n".join(html)

    def get_headers(self, environ):
        if self.extra_headers:
            extra = list(self.extra_headers.items())
        else:
            extra = []
        return super().get_headers(environ) + extra


def abort(http_status_code, exc=None, **kwargs):
    """Raise a HTTPException for the given http_status_code. Attach any keyword
    arguments to the exception for later processing.
    """
    # Determine the HTTPException subclass to use.
    http_exception_class = default_exceptions[http_status_code]

    # Mix in our special behaviour.
    class ArgumentValidationError(VerboseError, http_exception_class):
        pass

    # Actually raise the exception.
    raise ArgumentValidationError(exc, **kwargs)


def is_json_request(req):
    return core.is_json(req.mimetype)


class FlaskParser(core.Parser):
    """Flask request argument parser."""

    __location_map__ = dict(
        view_args="load_view_args",
        path="load_view_args",
        **core.Parser.__location_map__,
    )

    def _raw_load_json(self, req):
        """Return a json payload from the request for the core parser's load_json

        Checks the input mimetype and may return 'missing' if the mimetype is
        non-json, even if the request body is parseable as json."""
        if not is_json_request(req):
            return core.missing

        return core.parse_json(req.get_data(cache=True))

    def _handle_invalid_json_error(self, error, req, *args, **kwargs):
        abort(400, exc=error, messages={"json": ["Invalid JSON body."]})

    def load_view_args(self, req, schema):
        """Return the request's ``view_args`` or ``missing`` if there are none."""
        return req.view_args or core.missing

    def load_querystring(self, req, schema):
        """Return query params from the request as a MultiDictProxy."""
        return MultiDictProxy(req.args, schema)

    def load_form(self, req, schema):
        """Return form values from the request as a MultiDictProxy."""
        return MultiDictProxy(req.form, schema)

    def load_headers(self, req, schema):
        """Return headers from the request as a MultiDictProxy."""
        return MultiDictProxy(req.headers, schema)

    def load_cookies(self, req, schema):
        """Return cookies from the request."""
        return req.cookies

    def load_files(self, req, schema):
        """Return files from the request as a MultiDictProxy."""
        return MultiDictProxy(req.files, schema)

    def handle_error(self, error, req, schema, *, error_status_code, error_headers):
        """Handles errors during parsing. Aborts the current HTTP request and
        responds with a 422 error.
        """
        status_code = error_status_code or self.DEFAULT_VALIDATION_STATUS
        # on marshmallow 2, a many schema receiving a non-list value will
        # produce this specific error back -- reformat it to match the
        # marshmallow 3 message so that Flask can properly encode it
        messages = error.messages
        if (
            MARSHMALLOW_VERSION_INFO[0] < 3
            and schema.many
            and messages == {0: {}, "_schema": ["Invalid input type."]}
        ):
            messages.pop(0)
        abort(
            status_code,
            exc=error,
            messages=error.messages,
            schema=schema,
            headers=error_headers,
        )

    def get_default_request(self):
        """Override to use Flask's thread-local request object by default"""
        return flask.request


parser = FlaskParser()
use_args = parser.use_args
use_kwargs = parser.use_kwargs
