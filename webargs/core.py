# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import collections
import functools
import inspect
import logging
import warnings
try:
    import simplejson as json
except ImportError:
    import json

import marshmallow as ma
from marshmallow.compat import iteritems
from marshmallow.utils import missing, is_collection

logger = logging.getLogger(__name__)


__all__ = [
    'WebargsError',
    'ValidationError',
    'argmap2schema',
    'is_multiple',
    'Parser',
    'get_value',
    'missing',
    'parse_json',
]

DEFAULT_VALIDATION_STATUS = 422


class WebargsError(Exception):
    """Base class for all webargs-related errors."""
    pass


class ValidationError(WebargsError, ma.exceptions.ValidationError):
    """Raised when validation fails on user input. Same as
    `marshmallow.ValidationError`, with the addition of the ``status_code`` and
    ``headers`` arguments.
    """
    def __init__(self, message, status_code=DEFAULT_VALIDATION_STATUS, headers=None, **kwargs):
        self.status_code = status_code
        self.headers = headers
        ma.exceptions.ValidationError.__init__(
            self, message, status_code=status_code, headers=headers, **kwargs
        )

    def __repr__(self):
        return 'ValidationError({0!r}, status_code={1}, headers={2})'.format(
            self.args[0], self.status_code, self.headers
        )

def _callable_or_raise(obj):
    """Makes sure an object is callable if it is not ``None``. If not
    callable, a ValueError is raised.
    """
    if obj and not callable(obj):
        raise ValueError('{0!r} is not callable.'.format(obj))
    else:
        return obj

def get_field_names_for_argmap(argmap):
    if isinstance(argmap, ma.Schema):
        all_field_names = set([fname for fname, fobj in iteritems(argmap.fields)
            if not fobj.dump_only])
    else:
        all_field_names = set(argmap.keys())
    return all_field_names


def fill_in_missing_args(ret, argmap):
    # WARNING: We modify ret in-place
    all_field_names = get_field_names_for_argmap(argmap)
    missing_args = all_field_names - set(ret.keys())
    for key in missing_args:
        ret[key] = missing
    return ret

def argmap2schema(argmap, instance=False, **kwargs):
    """Generate a `marshmallow.Schema` class given a dictionary of argument
    names to `Fields <marshmallow.fields.Field>`.
    """
    class Meta(object):
        strict = True
    attrs = dict(argmap, Meta=Meta)
    cls = type(str(''), (ma.Schema,), attrs)
    return cls if not instance else cls(**kwargs)

def is_multiple(field):
    """Return whether or not `field` handles repeated/multi-value arguments."""
    return isinstance(field, ma.fields.List) and not hasattr(field, 'delimiter')


def get_mimetype(content_type):
    return content_type.split(';')[0].strip() if content_type else None

# Adapted from werkzeug: https://github.com/mitsuhiko/werkzeug/blob/master/werkzeug/wrappers.py
def is_json(mimetype):
    """Indicates if this mimetype is JSON or not.  By default a request
    is considered to include JSON data if the mimetype is
    ``application/json`` or ``application/*+json``.
    """
    if not mimetype:
        return False
    if ';' in mimetype:  # Allow Content-Type header to be passed
        mimetype = get_mimetype(mimetype)
    if mimetype == 'application/json':
        return True
    if mimetype.startswith('application/') and mimetype.endswith('+json'):
        return True
    return False

def get_value(data, name, field, allow_many_nested=False):
    """Get a value from a dictionary. Handles ``MultiDict`` types when
    ``multiple=True``. If the value is not found, return `missing`.

    :param object data: Mapping (e.g. :type:`dict`) or list-like instance to
        pull the value from.
    :param str name: Name of the key.
    :param bool multiple: Whether to handle multiple values.
    :param bool allow_many_nested: Whether to allow a list of nested objects
        (it is valid only for JSON format, so it is set to True in ``parse_json``
        methods).
    """
    missing_value = missing
    if allow_many_nested and isinstance(field, ma.fields.Nested) and field.many:
        if is_collection(data):
            return data

    if not hasattr(data, 'get'):
        return missing_value

    multiple = is_multiple(field)
    val = data.get(name, missing_value)
    if multiple and val is not missing:
        if hasattr(data, 'getlist'):
            return data.getlist(name)
        elif hasattr(data, 'getall'):
            return data.getall(name)
        elif isinstance(val, (list, tuple)):
            return val
        if val is None:
            return None
        else:
            return [val]
    return val

def parse_json(s):
    if isinstance(s, bytes):
        s = s.decode('utf-8')
    return json.loads(s)

def _ensure_list_of_callables(obj):
    if obj:
        if isinstance(obj, (list, tuple)):
            validators = obj
        elif callable(obj):
            validators = [obj]
        else:
            raise ValueError('{0!r} is not a callable or list of callables.'.format(obj))
    else:
        validators = []
    return validators

class Parser(object):
    """Base parser class that provides high-level implementation for parsing
    a request.

    Descendant classes must provide lower-level implementations for parsing
    different locations, e.g. ``parse_json``, ``parse_querystring``, etc.

    :param tuple locations: Default locations to parse.
    :param callable error_handler: Custom error handler function.
    """

    DEFAULT_LOCATIONS = ('querystring', 'form', 'json',)
    DEFAULT_VALIDATION_STATUS = DEFAULT_VALIDATION_STATUS
    DEFAULT_VALIDATION_MESSAGE = 'Invalid value.'

    #: Maps location => method name
    __location_map__ = {
        'json': 'parse_json',
        'querystring': 'parse_querystring',
        'query': 'parse_querystring',
        'form': 'parse_form',
        'headers': 'parse_headers',
        'cookies': 'parse_cookies',
        'files': 'parse_files',
    }

    def __init__(self, locations=None, error_handler=None):
        self.locations = locations or self.DEFAULT_LOCATIONS
        self.error_callback = _callable_or_raise(error_handler)
        #: A short-lived cache to store results from processing request bodies.
        self._cache = {}

    def _validated_locations(self, locations):
        """Ensure that the given locations argument is valid.

        :raises: ValueError if a given locations includes an invalid location.
        """
        # The set difference between the given locations and the available locations
        # will be the set of invalid locations
        valid_locations = set(self.__location_map__.keys())
        given = set(locations)
        invalid_locations = given - valid_locations
        if len(invalid_locations):
            msg = "Invalid locations arguments: {0}".format(list(invalid_locations))
            raise ValueError(msg)
        return locations

    def _get_value(self, name, argobj, req, location):
        # Parsing function to call
        # May be a method name (str) or a function
        func = self.__location_map__.get(location)
        if func:
            if inspect.isfunction(func):
                function = func
            else:
                function = getattr(self, func)
            value = function(req, name, argobj)
        else:
            raise ValueError('Invalid location: "{0}"'.format(location))
        return value

    def parse_arg(self, name, field, req, locations=None):
        """Parse a single argument from a request.

        .. note::
            This method does not perform validation on the argument.

        :param str name: The name of the value.
        :param marshmallow.fields.Field field: The marshmallow `Field` for the request
            parameter.
        :param req: The request object to parse.
        :param tuple locations: The locations ('json', 'querystring', etc.) where
            to search for the value.
        :return: The unvalidated argument value or `missing` if the value cannot be found
            on the request.
        """
        location = field.metadata.get('location')
        if location:
            locations_to_check = self._validated_locations([location])
        else:
            locations_to_check = self._validated_locations(locations or self.locations)

        for location in locations_to_check:
            value = self._get_value(name, field, req=req, location=location)
            # Found the value; validate and return it
            if value is not missing:
                return value
        return missing

    def _parse_request(self, schema, req, locations):
        """Return a parsed arguments dictionary for the current request."""
        if schema.many:
            assert 'json' in locations, "schema.many=True is only supported for JSON location"
            # The ad hoc Nested field is more like a workaround or a helper, and it servers its
            # purpose fine. However, if somebody has a desire to re-design the support of
            # bulk-type arguments, go ahead.
            parsed = self.parse_arg(
                name='json',
                field=ma.fields.Nested(schema, many=True),
                req=req,
                locations=locations
            )
            if parsed is missing:
                parsed = []
        else:
            argdict = schema.fields
            parsed = {}
            for argname, field_obj in iteritems(argdict):
                parsed_value = self.parse_arg(argname, field_obj, req, locations)
                # If load_from is specified on the field, try to parse from that key
                if parsed_value is missing and field_obj.load_from:
                    parsed_value = self.parse_arg(field_obj.load_from, field_obj, req, locations)
                    argname = field_obj.load_from
                parsed[argname] = parsed_value
        return parsed

    def load(self, data, argmap):
        if isinstance(argmap, ma.Schema):
            schema = argmap
        else:
            schema = argmap2schema(argmap)()
        if not schema.strict:
            warnings.warn("It is highly recommended that you set strict=True on your schema "
                "so that the parser's error handler will be invoked when expected.", UserWarning)
        return schema.load(data)

    def _on_validation_error(self, error):
        if (isinstance(error, ma.exceptions.ValidationError) and not
                isinstance(error, ValidationError)):
            # Raise a webargs error instead
            error = ValidationError(
                error.messages,
                field_names=error.field_names,
                fields=error.fields,
                data=error.data,
                **getattr(error, 'kwargs', {})
            )
        if self.error_callback:
            self.error_callback(error)
        else:
            self.handle_error(error)

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
        elif callable(argmap):
            schema = argmap(req)
        else:
            schema = argmap2schema(argmap)()
        return schema

    def parse(self, argmap, req=None, locations=None, validate=None, force_all=False):
        """Main request parsing method.

        :param argmap: Either a `marshmallow.Schema`, a `dict`
            of argname -> `marshmallow.fields.Field` pairs, or a callable
            which accepts a request and returns a `marshmallow.Schema`.
        :param req: The request object to parse.
        :param tuple locations: Where on the request to search for values.
            Can include one or more of ``('json', 'querystring', 'form',
            'headers', 'cookies', 'files')``.
        :param callable validate: Validation function or list of validation functions
            that receives the dictionary of parsed arguments. Validator either returns a
            boolean or raises a :exc:`ValidationError`.

         :return: A dictionary of parsed arguments
        """
        req = req if req is not None else self.get_default_request()
        assert req is not None, 'Must pass req object'
        ret = None
        validators = _ensure_list_of_callables(validate)
        schema = self._get_schema(argmap, req)
        try:
            parsed = self._parse_request(schema=schema, req=req, locations=locations)
            result = self.load(parsed, schema)
            self._validate_arguments(result.data, validators)
        except ma.exceptions.ValidationError as error:
            self._on_validation_error(error)
        else:
            ret = result.data
        finally:
            self.clear_cache()
        if force_all:
            fill_in_missing_args(ret, schema)
        return ret

    def clear_cache(self):
        """Invalidate the parser's cache."""
        self._cache = {}
        return None

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

    def use_args(self, argmap, req=None, locations=None, as_kwargs=False, validate=None):
        """Decorator that injects parsed arguments into a view function or method.

        Example usage with Flask: ::

            @app.route('/echo', methods=['get', 'post'])
            @parser.use_args({'name': fields.Str()})
            def greet(args):
                return 'Hello ' + args['name']

        :param argmap: Either a `marshmallow.Schema`, a `dict`
            of argname -> `marshmallow.fields.Field` pairs, or a callable
            which accepts a request and returns a `marshmallow.Schema`.
        :param tuple locations: Where on the request to search for values.
        :param bool as_kwargs: Whether to insert arguments as keyword arguments.
        :param callable validate: Validation function that receives the dictionary
            of parsed arguments. If the function returns ``False``, the parser
            will raise a :exc:`ValidationError`.
        """
        locations = locations or self.locations
        request_obj = req
        # Optimization: If argmap is passed as a dictionary, we only need
        # to generate a Schema once
        if isinstance(argmap, collections.Mapping):
            argmap = argmap2schema(argmap)()

        def decorator(func):
            req_ = request_obj

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                req_obj = req_

                # if as_kwargs is passed, must include all args
                force_all = as_kwargs

                if not req_obj:
                    req_obj = self.get_request_from_view_args(func, args, kwargs)
                # NOTE: At this point, argmap may be a Schema, or a callable
                parsed_args = self.parse(argmap, req=req_obj,
                                         locations=locations, validate=validate,
                                         force_all=force_all)
                if as_kwargs:
                    kwargs.update(parsed_args)
                    return func(*args, **kwargs)
                else:
                    # Add parsed_args after other positional arguments
                    new_args = args + (parsed_args, )
                    return func(*new_args, **kwargs)
            wrapper.__wrapped__ = func
            return wrapper
        return decorator

    def use_kwargs(self, *args, **kwargs):
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
        kwargs['as_kwargs'] = True
        return self.use_args(*args, **kwargs)

    def location_handler(self, name):
        """Decorator that registers a function for parsing a request location.
        The wrapped function receives a request, the name of the argument, and
        the corresponding `Field <marshmallow.fields.Field>` object.

        Example: ::

            from webargs import core
            parser = core.Parser()

            @parser.location_handler('name')
            def parse_data(request, name, field):
                return request.data.get(name)

        :param str name: The name of the location to register.
        """
        def decorator(func):
            self.__location_map__[name] = func
            return func
        return decorator

    def error_handler(self, func):
        """Decorator that registers a custom error handling function. The
        function should received the raised error. Overrides
        the parser's ``handle_error`` method.

        Example: ::

            from webargs import core
            parser = core.Parser()

            class CustomError(Exception):
                pass

            @parser.error_handler
            def handle_error(error):
                raise CustomError(error)

        :param callable func: The error callback to register.
        """
        self.error_callback = func
        return func

    # Abstract Methods

    def parse_json(self, req, name, arg):
        """Pull a JSON value from a request object or return `missing` if the
        value cannot be found.
        """
        return missing

    def parse_querystring(self, req, name, arg):
        """Pull a value from the query string of a request object or return `missing` if
        the value cannot be found.
        """
        return missing

    def parse_form(self, req, name, arg):
        """Pull a value from the form data of a request object or return
        `missing` if the value cannot be found.
        """
        return missing

    def parse_headers(self, req, name, arg):
        """Pull a value from the headers or return `missing` if the value
        cannot be found.
        """
        return missing

    def parse_cookies(self, req, name, arg):
        """Pull a cookie value from the request or return `missing` if the value
        cannot be found.
        """
        return missing

    def parse_files(self, req, name, arg):
        """Pull a file from the request or return `missing` if the value file
        cannot be found.
        """
        return missing

    def handle_error(self, error):
        """Called if an error occurs while parsing args. By default, just logs and
        raises ``error``.
        """
        logger.error(error)
        raise error
