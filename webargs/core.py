# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sys
import functools
import inspect
import logging

PY2 = sys.version_info[0] == 2

if not PY2:
    iteritems = lambda d: iter(d.items())
    unicode = str
    text_type = str
else:
    iteritems = lambda d: d.iteritems()
    unicode = unicode
    text_type = unicode

logger = logging.getLogger(__name__)

class WebargsError(Exception):
    """Base class for all webargs-related errors."""
    pass


class ValidationError(WebargsError):
    """Raised in case of an argument validation error.

    :param error: Either a string message or an underlying :exc:`Exception`
        object.
    :param int status_code: HTTP status code.
    :param data: Additional keyword arguments to store in the ``data`` attribute.

    .. versionchanged:: 0.8.0

        Store status_code and additonal data.
    """
    def __init__(self, error, status_code=400, **data):
        self.message = unicode(error)
        self.status_code = status_code
        self.data = data
        super(ValidationError, self).__init__(self.message)

    def __repr__(self):
        return 'ValidationError({0!r}, status_code={1})'.format(
            self.message, self.status_code
        )


def _callable_or_raise(obj):
    """Makes sure an object is callable if it is not ``None``. If not
    callable, a ValueError is raised.
    """
    if obj and not callable(obj):
        raise ValueError('{0!r} is not callable.'.format(obj))
    else:
        return obj

def _ensure_list_of_callables(validate):
    if validate:
        if isinstance(validate, (list, tuple)):
            validators = validate
        elif callable(validate):
            validators = [validate]
        else:
            raise ValueError('validate must be a callable or list of callables.')
    else:
        validators = []
    return validators


class _Missing(object):
    """Represents a value that is missing from the set of passed in request
    arguments.
    """

    def __bool__(self):
        return False

    __nonzero__ = __bool__  # py2 compatibility

    def __repr__(self):
        return '<webargs.core.missing>'


#: Singleton object that represents a value that cannot be found on a request.
Missing = _Missing()


def get_value(d, name, multiple):
    """Get a value from a dictionary. Handles ``MultiDict`` types when
    ``multiple=True``. If the value is not found, return `missing`.

    :param dict d: Dictionary to pull the value from.
    :param str name: Name of the key.
    :param bool multiple: Whether to handle multiple values.
    """
    val = d.get(name, Missing)
    if multiple:
        if hasattr(d, 'getlist'):
            return d.getlist(name)
        elif hasattr(d, 'getall'):
            return d.getall(name)
        else:
            return [val]
    return val


def noop(x):
    return x


class Arg(object):
    """A request argument.

    :param type type\_: Value type. Will try to convert the passed in value to this
        type. If ``None``, no type conversion will be performed.
    :param default: Default value for the argument. Used if the value is not found
        on the request. May be a callable.
    :param bool required: If ``True``, the :meth:`Parser.handle_error` method will be
        invoked if this argument is missing from the request.
    :param callable validate: Callable (function or object with ``__call__`` method
        defined) or list of callables. used for custom validation. A validator may return
        a boolean or raise a :exc:`ValidationError`.
    :param callable use: Function used for converting or pre-processing the value.
        Defaults to noop. Example: ``use=lambda s: s.lower()``
    :param bool multiple: Return a list of values for the argument. Useful for
        querystrings or forms that pass multiple values to the same parameter,
        e.g. ``/?name=foo&name=bar``
    :param str error: Custom error message to use if validation fails.
    :param bool allow_missing: If the argument is not found on the request,
        don't include it in the parsed arguments dictionary.
    :param str target: Where to pull the value off the request, e.g. ``'json'``.
    :param str source: Key at which value is located, if different from key in
        argmap
    :param metadata: Extra arguments to be stored as metadata.

    .. versionchanged:: 0.5.0
        The ``use`` callable is called before type conversion.
    """
    def __init__(self, type_=None, default=None, required=False,
                 validate=None, use=None, multiple=False, error=None,
                 allow_missing=False, target=None, source=None, **metadata):
        self.type = type_ or noop  # default to no type conversion
        if multiple and default is None:
            self.default = []
        else:
            self.default = default
        self.required = required
        self.validators = _ensure_list_of_callables(validate)
        self.use = _callable_or_raise(use) or noop
        self.error = error
        self.multiple = multiple
        if required and allow_missing:
            raise ValueError('"required" and "allow_missing" cannot both be True.')
        self.allow_missing = allow_missing
        self.target = target
        self.source = source
        self.metadata = metadata

    def __repr__(self):
        return ('<webargs.core.Arg(type_={self.type}, default={self.default!r}, '
                'required={self.required})>').format(self=self)

    def _validate(self, value):
        """Perform conversion and validation on ``value``."""
        ret = value
        # First convert the value
        try:
            ret = self.type(self.use(value))
        except ValueError as error:
            raise ValidationError(self.error or error)
        # Then call validation functions
        for validator in self.validators:
            if validator(ret) is False:
                msg = u'Validator {0}({1}) is not True'.format(
                    validator.__name__, ret
                )
                raise ValidationError(self.error or msg)
        return ret

    def validated(self, value):
        """Convert and validate the given value according to the ``type_``,
        ``use``, and ``validate`` attributes.

        :returns: The validated, converted value
        :raises: ValidationError if validation fails
        """
        # Prevent "missing" placeholder from getting converted
        if value is Missing:
            return value
        if self.multiple and isinstance(value, list):
            return [self._validate(each) for each in value]
        else:
            return self._validate(value)


class Parser(object):
    """Base parser class that provides high-level implementation for parsing
    a request.

    Descendant classes must provide lower-level implementations for parsing
    different targets, e.g. ``parse_json``, ``parse_querystring``, etc.

    :param tuple targets: Default targets to parse.
    :param callable error_handler: Custom error handler function.
    :param str error: Custom error message to use if validation fails.
    """
    DEFAULT_TARGETS = ('querystring', 'form', 'json',)

    #: Maps target => method name
    TARGET_MAP = {
        'json': 'parse_json',
        'querystring': 'parse_querystring',
        'query': 'parse_querystring',
        'form': 'parse_form',
        'headers': 'parse_headers',
        'cookies': 'parse_cookies',
        'files': 'parse_files',
    }

    def __init__(self, targets=None, error_handler=None, error=None):
        self.targets = targets or self.DEFAULT_TARGETS
        self.error_callback = _callable_or_raise(error_handler)
        self.error = error

    def _validated_targets(self, targets):
        """Ensure that the given targets argument is valid.

        :raises: ValueError if a given targets includes an invalid target.
        """
        # The set difference between the given targets and the available targets
        # will be the set of invalid targets
        valid_targets = set(self.TARGET_MAP.keys())
        given = set(targets)
        invalid_targets = given - valid_targets
        if len(invalid_targets):
            msg = "Invalid targets arguments: {0}".format(list(invalid_targets))
            raise ValueError(msg)
        return targets

    def _get_value(self, name, argobj, req, target):
        # Parsing function to call
        # May be a method name (str) or a function
        func = self.TARGET_MAP.get(target)
        if func:
            if inspect.isfunction(func):
                function = func
            else:
                function = getattr(self, func)
            value = function(req, argobj.source or name, argobj)
        else:
            value = None
        return value

    def parse_arg(self, name, argobj, req, targets=None):
        """Parse a single argument.

        :param str name: The name of the value.
        :param Arg argobj: The ``Arg`` object.
        :param req: The request object to parse.
        :param tuple targets: The targets ('json', 'querystring', etc.) where
            to search for the value.
        :return: The argument value or `Missing` if the value cannot be found
            on the request.

        :raises: ValidationError if a validation function returns `False` or
            if a required argument is missing.
        """
        value = None
        if argobj.target:
            targets_to_check = self._validated_targets([argobj.target])
        else:
            targets_to_check = self._validated_targets(targets or self.targets)

        for target in targets_to_check:
            value = self._get_value(name, argobj, req=req, target=target)
            if argobj.multiple and not (isinstance(value, list) and len(value)):
                continue
            # Found the value; validate and return it
            if value is not Missing:
                return argobj.validated(value)
        if value is Missing:
            if argobj.default is not None:
                if callable(argobj.default):
                    value = argobj.default()
                else:
                    value = argobj.default
            if argobj.required:
                raise ValidationError('Required parameter {0!r} not found.'.format(name))
        return value

    def parse(self, argmap, req, targets=None, validate=None, force_all=False):
        """Main request parsing method.

        :param dict argmap: Dictionary of argname:Arg object pairs.
        :param req: The request object to parse.
        :param tuple targets: Where on the request to search for values.
            Can include one or more of ``('json', 'querystring', 'form',
            'headers', 'cookies', 'files')``.
        :param callable validate: Validation function or list of validation functions
            that receives the dictionary of parsed arguments. Validator either returns a
            boolean or raises a :exc:`ValidationError`.

         :return: A dictionary of parsed arguments
        """
        validators = _ensure_list_of_callables(validate)
        try:
            parsed = {}
            for argname, argobj in iteritems(argmap):
                parsed_value = self.parse_arg(argname, argobj, req,
                    targets=targets or self.targets)
                # Skip missing values
                can_skip = (not force_all and
                            parsed_value is Missing or (argobj.multiple
                                                    and not len(parsed_value)))
                if argobj.allow_missing and can_skip:
                    continue
                else:
                    if parsed_value is Missing:
                        parsed_value = self.fallback(req, argname, argobj)
                    parsed[argname] = parsed_value
            for validator in validators:
                if validator(parsed) is False:
                    msg = u'Validator {0}({1}) is not True'.format(
                        validator.__name__, parsed
                    )
                    raise ValidationError(self.error or msg)
            return parsed
        except Exception as error:
            if self.error_callback:
                self.error_callback(error)
            else:
                self.handle_error(error)

    def use_args(self, argmap, req=None, targets=None, as_kwargs=False, validate=None):
        """Decorator that injects parsed arguments into a view function or method.

        Example usage with Flask: ::

            @app.route('/echo', methods=['get', 'post'])
            @parser.use_args({'name': Arg(str)})
            def greet(args):
                return 'Hello ' + args['name']

        :param dict argmap: Dictionary of argument_name:Arg object pairs.
        :param tuple targets: Where on the request to search for values.
        :param bool as_kwargs: Whether to insert arguments as keyword arguments.
        :param callable validate: Validation function that receives the dictionary
            of parsed arguments. If the function returns ``False``, the parser
            will raise a :exc:`ValidationError`.
        """
        targets = targets or self.DEFAULT_TARGETS

        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # if as_kwargs is passed, must include all args
                force_all = as_kwargs
                parsed_args = self.parse(argmap, req=req, targets=targets,
                                         validate=validate, force_all=force_all)
                if as_kwargs:
                    kwargs.update(parsed_args)
                    return func(*args, **kwargs)
                else:
                    # Wrapped function is a method, so inject parsed_args
                    # after 'self'
                    if args and args[0]:
                        return func(args[0], parsed_args, *args[1:], **kwargs)
                    return func(parsed_args, *args, **kwargs)
            return wrapper
        return decorator

    def use_kwargs(self, *args, **kwargs):
        """Decorator that injects parsed arguments into a view function or method
        as keyword arguments.

        This is a shortcut to :meth:`use_args` with ``as_kwargs=True``.

        Example usage with Flask: ::

            @app.route('/echo', methods=['get', 'post'])
            @parser.use_kwargs({'name': Arg(str)})
            def greet(name):
                return 'Hello ' + name

        Receives the same ``args`` and ``kwargs`` as :meth:`use_args`.
        """
        kwargs['as_kwargs'] = True
        return self.use_args(*args, **kwargs)

    def target_handler(self, name):
        """Decorator that registers a function that parses a request target.
        The wrapped function receives a request, the name of the argument, and
        the :class:`Arg <webargs.core.Arg>` object.

        Example: ::

            from webargs import core
            parser = core.Parser()

            @parser.target_handler('name')
            def parse_data(request, name, arg):
                return request.data.get(name)

        :param str name: The name of the target to register.
        """
        def decorator(func):
            self.TARGET_MAP[name] = func
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
        """Pull a JSON value from a request object or return `Missing` if the
        value cannot be found.
        """
        return Missing

    def parse_querystring(self, req, name, arg):
        """Pull a value from the query string of a request object or return `Missing` if
        the value cannot be found.
        """
        return Missing

    def parse_form(self, req, name, arg):
        """Pull a value from the form data of a request object or return
        `Missing` if the value cannot be found.
        """
        return Missing

    def parse_headers(self, req, name, arg):
        """Pull a value from the headers or return `Missing` if the value
        cannot be found.
        """
        return Missing

    def parse_cookies(self, req, name, arg):
        """Pull a cookie value from the request or return `Missing` if the value
        cannot be found.
        """
        return Missing

    def parse_files(self, req, name, arg):
        """Pull a file from the request or return `Missing` if the value file
        cannot be found.
        """
        return Missing

    def handle_error(self, error):
        """Called if an error occurs while parsing args. By default, just logs and
        raises ``error``.
        """
        logger.error(error)
        raise error

    def fallback(self, req, name, arg):
        """Called if all other parsing functions (parse_json, parse_form...) return
        `Missing`.
        """
        return None
