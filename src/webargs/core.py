import functools
import inspect
import typing
import logging
import warnings
from collections.abc import Mapping
import json

import marshmallow as ma
from marshmallow import ValidationError
from marshmallow.utils import missing

from webargs.compat import MARSHMALLOW_VERSION_INFO
from webargs.dict2schema import dict2schema
from webargs.fields import DelimitedList

logger = logging.getLogger(__name__)


__all__ = [
    "ValidationError",
    "dict2schema",
    "is_multiple",
    "Parser",
    "missing",
    "parse_json",
]


DEFAULT_VALIDATION_STATUS = 422  # type: int


def _callable_or_raise(obj):
    """Makes sure an object is callable if it is not ``None``. If not
    callable, a ValueError is raised.
    """
    if obj and not callable(obj):
        raise ValueError("{!r} is not callable.".format(obj))
    return obj


def is_multiple(field):
    """Return whether or not `field` handles repeated/multi-value arguments."""
    return isinstance(field, ma.fields.List) and not isinstance(field, DelimitedList)


def get_mimetype(content_type):
    return content_type.split(";")[0].strip() if content_type else None


# Adapted from werkzeug:
# https://github.com/mitsuhiko/werkzeug/blob/master/werkzeug/wrappers.py
def is_json(mimetype):
    """Indicates if this mimetype is JSON or not.  By default a request
    is considered to include JSON data if the mimetype is
    ``application/json`` or ``application/*+json``.
    """
    if not mimetype:
        return False
    if ";" in mimetype:  # Allow Content-Type header to be passed
        mimetype = get_mimetype(mimetype)
    if mimetype == "application/json":
        return True
    if mimetype.startswith("application/") and mimetype.endswith("+json"):
        return True
    return False


def parse_json(string, *, encoding="utf-8"):
    if isinstance(string, bytes):
        try:
            string = string.decode(encoding)
        except UnicodeDecodeError as exc:
            raise json.JSONDecodeError(
                "Bytes decoding error : {}".format(exc.reason),
                doc=str(exc.object),
                pos=exc.start,
            )
    return json.loads(string)


def _ensure_list_of_callables(obj):
    if obj:
        if isinstance(obj, (list, tuple)):
            validators = obj
        elif callable(obj):
            validators = [obj]
        else:
            raise ValueError("{!r} is not a callable or list of callables.".format(obj))
    else:
        validators = []
    return validators


class Parser:
    """Base parser class that provides high-level implementation for parsing
    a request.

    Descendant classes must provide lower-level implementations for reading
    data from  different locations, e.g. ``load_json``, ``load_querystring``,
    etc.

    :param str location: Default location to use for data
    :param callable error_handler: Custom error handler function.
    """

    #: Default location to check for data
    DEFAULT_LOCATION = "json"
    #: The marshmallow Schema class to use when creating new schemas
    DEFAULT_SCHEMA_CLASS = ma.Schema
    #: Default status code to return for validation errors
    DEFAULT_VALIDATION_STATUS = DEFAULT_VALIDATION_STATUS
    #: Default error message for validation errors
    DEFAULT_VALIDATION_MESSAGE = "Invalid value."

    #: Maps location => method name
    __location_map__ = {
        "json": "load_json",
        "querystring": "load_querystring",
        "query": "load_querystring",
        "form": "load_form",
        "headers": "load_headers",
        "cookies": "load_cookies",
        "files": "load_files",
        "json_or_form": "load_json_or_form",
    }

    def __init__(self, location=None, *, error_handler=None, schema_class=None):
        self.location = location or self.DEFAULT_LOCATION
        self.error_callback = _callable_or_raise(error_handler)
        self.schema_class = schema_class or self.DEFAULT_SCHEMA_CLASS

    def _get_loader(self, location):
        """Get the loader function for the given location.

        :raises: ValueError if a given location is invalid.
        """
        valid_locations = set(self.__location_map__.keys())
        if location not in valid_locations:
            msg = "Invalid location argument: {}".format(location)
            raise ValueError(msg)

        # Parsing function to call
        # May be a method name (str) or a function
        func = self.__location_map__.get(location)
        if func:
            if inspect.isfunction(func):
                function = func
            else:
                function = getattr(self, func)
        else:
            raise ValueError('Invalid location: "{}"'.format(location))
        return function

    def _load_location_data(self, *, schema, req, location):
        """Return a dictionary-like object for the location on the given request.

        Needs to have the schema in hand in order to correctly handle loading
        lists from multidict objects and `many=True` schemas.
        """
        loader_func = self._get_loader(location)
        data = loader_func(req, schema)
        # when the desired location is empty (no data), provide an empty
        # dict as the default so that optional arguments in a location
        # (e.g. optional JSON body) work smoothly
        if data is missing:
            data = {}
        return data

    def _on_validation_error(
        self, error, req, schema, location, *, error_status_code, error_headers
    ):
        # rewrite messages to be namespaced under the location which created
        # them
        # e.g. {"json":{"foo":["Not a valid integer."]}}
        #      instead of
        #      {"foo":["Not a valid integer."]}
        error.messages = {location: error.messages}
        error_handler = self.error_callback or self.handle_error
        error_handler(
            error,
            req,
            schema,
            error_status_code=error_status_code,
            error_headers=error_headers,
        )

    def _validate_arguments(self, data, validators):
        for validator in validators:
            if validator(data) is False:
                msg = self.DEFAULT_VALIDATION_MESSAGE
                raise ValidationError(msg, data=data)

    def _get_schema(self, argmap, req):
        """Return a `marshmallow.Schema` for the given argmap and request.

        :param argmap: Either a `marshmallow.Schema`, `dict`
            of argname -> `marshmallow.fields.Field` pairs, or a callable that returns
            a `marshmallow.Schema` instance.
        :param req: The request object being parsed.
        :rtype: marshmallow.Schema
        """
        if isinstance(argmap, ma.Schema):
            schema = argmap
        elif isinstance(argmap, type) and issubclass(argmap, ma.Schema):
            schema = argmap()
        elif callable(argmap):
            schema = argmap(req)
        else:
            schema = dict2schema(argmap, schema_class=self.schema_class)()
        if MARSHMALLOW_VERSION_INFO[0] < 3 and not schema.strict:
            warnings.warn(
                "It is highly recommended that you set strict=True on your schema "
                "so that the parser's error handler will be invoked when expected.",
                UserWarning,
            )
        return schema

    def parse(
        self,
        argmap,
        req=None,
        *,
        location=None,
        validate=None,
        error_status_code=None,
        error_headers=None
    ):
        """Main request parsing method.

        :param argmap: Either a `marshmallow.Schema`, a `dict`
            of argname -> `marshmallow.fields.Field` pairs, or a callable
            which accepts a request and returns a `marshmallow.Schema`.
        :param req: The request object to parse.
        :param str location: Where on the request to load values.
            Can be any of the values in :py:attr:`~__location_map__`. By
            default, that means one of ``('json', 'query', 'querystring',
            'form', 'headers', 'cookies', 'files', 'json_or_form')``.
        :param callable validate: Validation function or list of validation functions
            that receives the dictionary of parsed arguments. Validator either returns a
            boolean or raises a :exc:`ValidationError`.
        :param int error_status_code: Status code passed to error handler functions when
            a `ValidationError` is raised.
        :param dict error_headers: Headers passed to error handler functions when a
            a `ValidationError` is raised.

         :return: A dictionary of parsed arguments
        """
        req = req if req is not None else self.get_default_request()
        location = location or self.location
        if req is None:
            raise ValueError("Must pass req object")
        data = None
        validators = _ensure_list_of_callables(validate)
        schema = self._get_schema(argmap, req)
        try:
            location_data = self._load_location_data(
                schema=schema, req=req, location=location
            )
            result = schema.load(location_data)
            data = result.data if MARSHMALLOW_VERSION_INFO[0] < 3 else result
            self._validate_arguments(data, validators)
        except ma.exceptions.ValidationError as error:
            self._on_validation_error(
                error,
                req,
                schema,
                location,
                error_status_code=error_status_code,
                error_headers=error_headers,
            )
        return data

    def get_default_request(self):
        """Optional override. Provides a hook for frameworks that use thread-local
        request objects.
        """
        return None

    def get_request_from_view_args(self, view, args, kwargs):
        """Optional override. Returns the request object to be parsed, given a view
        function's args and kwargs.

        Used by the `use_args` and `use_kwargs` to get a request object from a
        view's arguments.

        :param callable view: The view function or method being decorated by
            `use_args` or `use_kwargs`
        :param tuple args: Positional arguments passed to ``view``.
        :param dict kwargs: Keyword arguments passed to ``view``.
        """
        return None

    @staticmethod
    def _update_args_kwargs(args, kwargs, parsed_args, as_kwargs):
        """Update args or kwargs with parsed_args depending on as_kwargs"""
        if as_kwargs:
            kwargs.update(parsed_args)
        else:
            # Add parsed_args after other positional arguments
            args += (parsed_args,)
        return args, kwargs

    def use_args(
        self,
        argmap,
        req=None,
        *,
        location=None,
        as_kwargs=False,
        validate=None,
        error_status_code=None,
        error_headers=None
    ):
        """Decorator that injects parsed arguments into a view function or method.

        Example usage with Flask: ::

            @app.route('/echo', methods=['get', 'post'])
            @parser.use_args({'name': fields.Str()}, location="querystring")
            def greet(args):
                return 'Hello ' + args['name']

        :param argmap: Either a `marshmallow.Schema`, a `dict`
            of argname -> `marshmallow.fields.Field` pairs, or a callable
            which accepts a request and returns a `marshmallow.Schema`.
        :param str locations: Where on the request to load values.
        :param bool as_kwargs: Whether to insert arguments as keyword arguments.
        :param callable validate: Validation function that receives the dictionary
            of parsed arguments. If the function returns ``False``, the parser
            will raise a :exc:`ValidationError`.
        :param int error_status_code: Status code passed to error handler functions when
            a `ValidationError` is raised.
        :param dict error_headers: Headers passed to error handler functions when a
            a `ValidationError` is raised.
        """
        location = location or self.location
        request_obj = req
        # Optimization: If argmap is passed as a dictionary, we only need
        # to generate a Schema once
        if isinstance(argmap, Mapping):
            argmap = dict2schema(argmap, schema_class=self.schema_class)()

        def decorator(func):
            req_ = request_obj

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                req_obj = req_

                if not req_obj:
                    req_obj = self.get_request_from_view_args(func, args, kwargs)

                # NOTE: At this point, argmap may be a Schema, or a callable
                parsed_args = self.parse(
                    argmap,
                    req=req_obj,
                    location=location,
                    validate=validate,
                    error_status_code=error_status_code,
                    error_headers=error_headers,
                )
                args, kwargs = self._update_args_kwargs(
                    args, kwargs, parsed_args, as_kwargs
                )
                return func(*args, **kwargs)

            wrapper.__wrapped__ = func
            return wrapper

        return decorator

    def use_kwargs(self, *args, **kwargs) -> typing.Callable:
        """Decorator that injects parsed arguments into a view function or method
        as keyword arguments.

        This is a shortcut to :meth:`use_args` with ``as_kwargs=True``.

        Example usage with Flask: ::

            @app.route('/echo', methods=['get', 'post'])
            @parser.use_kwargs({'name': fields.Str()})
            def greet(name):
                return 'Hello ' + name

        Receives the same ``args`` and ``kwargs`` as :meth:`use_args`.
        """
        kwargs["as_kwargs"] = True
        return self.use_args(*args, **kwargs)

    def location_loader(self, name):
        """Decorator that registers a function for loading a request location.
        The wrapped function receives a schema and a request.

        The schema will usually not be relevant, but it's important in some
        cases -- most notably in order to correctly load multidict values into
        list fields. Without the schema, there would be no way to know whether
        to simply `.get()` or `.getall()` from a multidict for a given value.

        Example: ::

            from webargs import core
            parser = core.Parser()

            @parser.location_loader("name")
            def load_data(request, schema):
                return request.data

        :param str name: The name of the location to register.
        """

        def decorator(func):
            self.__location_map__[name] = func
            return func

        return decorator

    def error_handler(self, func):
        """Decorator that registers a custom error handling function. The
        function should receive the raised error, request object,
        `marshmallow.Schema` instance used to parse the request, error status code,
        and headers to use for the error response. Overrides
        the parser's ``handle_error`` method.

        Example: ::

            from webargs import flaskparser

            parser = flaskparser.FlaskParser()


            class CustomError(Exception):
                pass


            @parser.error_handler
            def handle_error(error, req, schema, *, status_code, headers):
                raise CustomError(error.messages)

        :param callable func: The error callback to register.
        """
        self.error_callback = func
        return func

    def _handle_invalid_json_error(self, error, req, *args, **kwargs):
        """Internal hook for overriding treatment of JSONDecodeErrors.

        Invoked by default `load_json` implementation.

        External parsers can just implement their own behavior for load_json ,
        so this is not part of the public parser API.
        """
        raise error

    def load_json(self, req, schema):
        """Load JSON from a request object or return `missing` if no value can
        be found.
        """
        # NOTE: although this implementation is real/concrete and used by
        # several of the parsers in webargs, it relies on the internal hooks
        # `_handle_invalid_json_error` and `_raw_load_json`
        # these methods are not part of the public API and are used to simplify
        # code sharing amongst the built-in webargs parsers
        try:
            return self._raw_load_json(req)
        except json.JSONDecodeError as exc:
            if exc.doc == "":
                return missing
            return self._handle_invalid_json_error(exc, req)
        except UnicodeDecodeError as exc:
            return self._handle_invalid_json_error(exc, req)

    def load_json_or_form(self, req, schema):
        """Load data from a request, accepting either JSON or form-encoded
        data.

        The data will first be loaded as JSON, and, if that fails, it will be
        loaded as a form post.
        """
        data = self.load_json(req, schema)
        if data is not missing:
            return data
        return self.load_form(req, schema)

    # Abstract Methods

    def _raw_load_json(self, req):
        """Internal hook method for implementing load_json()

        Get a request body for feeding in to `load_json`, and parse it either
        using core.parse_json() or similar utilities which raise
        JSONDecodeErrors.
        Ensure consistent behavior when encountering decoding errors.

        The default implementation here simply returns `missing`, and the default
        implementation of `load_json` above will pass that value through.
        However, by implementing a "mostly concrete" version of load_json with
        this as a hook for getting data, we consolidate the logic for handling
        those JSONDecodeErrors.
        """
        return missing

    def load_querystring(self, req, schema):
        """Load the query string of a request object or return `missing` if no
        value can be found.
        """
        return missing

    def load_form(self, req, schema):
        """Load the form data of a request object or return `missing` if no
        value can be found.
        """
        return missing

    def load_headers(self, req, schema):
        """Load the headers or return `missing` if no value can be found.
        """
        return missing

    def load_cookies(self, req, schema):
        """Load the cookies from the request or return `missing` if no value
        can be found.
        """
        return missing

    def load_files(self, req, schema):
        """Load files from the request or return `missing` if no values can be
        found.
        """
        return missing

    def handle_error(self, error, req, schema, *, error_status_code, error_headers):
        """Called if an error occurs while parsing args. By default, just logs and
        raises ``error``.
        """
        logger.error(error)
        raise error
