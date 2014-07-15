# -*- coding: utf-8 -*-
import sys
import functools
import inspect

PY2 = sys.version_info[0] == 2

if not PY2:
    iteritems = lambda d: iter(d.items())
else:
    iteritems = lambda d: d.iteritems()


class WebargsError(Exception):
    """Base class for all webargs-related errors."""
    pass


class ValidationError(WebargsError):
    """Raised in case of an argument validation error."""
    def __init__(self, underlying_exception):
        super(ValidationError, self).__init__(str(underlying_exception))


def _callable(obj):
    """Makes sure an object is callable if it is not ``None``. If not
    callable, a ValueError is raised.
    """
    if obj and not callable(obj):
        raise ValueError('{0!r} is not callable.'.format(obj))
    else:
        return obj


def get_value(d, name, multiple, method='get'):
    func = getattr(d, method)
    val = func(name)
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

    :param default: Default value for the argument. Used if the value is not found
        on the request.
    :param type type\_: Value type. Will try to convert the passed in value to this
        type. If ``None``, no type conversion will be performed.
    :param callable validate: Callable (function or object with ``__call__`` method
        defined) used for custom validation. Returns whether or not the
        value is valid.
    :param callable use: Preprocessing function used for converting or
        pre-processing the value. Defaults to noop.
        Example: ``use=lambda s: s.lower()``
    :param bool multiple: Return a list of values for the argument. Useful for
        querystrings or forms that pass multiple values to the same parameter,
        e.g. ``/?name=foo&name=bar``
    :param str error: Custom error message to use if validation fails.
    :param bool allow_missing: If the argument's value is ``None``, don't
        include it in the returned arguments dictionary.

    .. versionchanged:: 0.5.0
        The ``use`` callable is called before type conversion.
    """
    def __init__(self, type_=None, default=None, required=False,
                 validate=None, use=None, multiple=False, error=None,
                 allow_missing=False, target=None):
        self.type = type_ or noop  # default to no type conversion
        if multiple and default is None:
            self.default = []
        else:
            self.default = default
        self.required = required
        self.validate = _callable(validate) or (lambda x: True)
        self.use = _callable(use) or noop
        self.error = error
        self.multiple = multiple
        if required and allow_missing:
            raise ValueError('"required" and "allow_missing" cannot both be True.')
        self.allow_missing = allow_missing
        self.target = target

    def _validate(self, value):
        """Perform conversion and validation on ``value``."""
        ret = value
        # First convert the value
        try:
            ret = self.type(self.use(value))
        except ValueError as error:
            raise ValidationError(self.error or error)
        # Then call validation function
        if not self.validate(ret):
            msg = 'Validator {0}({1}) is not True'.format(
                self.validate.__name__, ret
            )
            raise ValidationError(self.error or msg)
        return ret

    def validated(self, value):
        """Convert and validate the given value according to the ``type_``,
        ``use``, and ``validate`` attributes.

        :returns: The validated, converted value
        :raises: ValidationError if validation fails
        """
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
    """
    DEFAULT_TARGETS = ('querystring', 'form', 'json',)

    #: Maps target => method name
    TARGET_MAP = {
        'json': 'parse_json',
        'querystring': 'parse_querystring',
        'form': 'parse_form',
        'headers': 'parse_headers',
        'cookies': 'parse_cookies',
        'files': 'parse_files',
    }

    def __init__(self, targets=None, error_handler=None):
        self.targets = targets or self.DEFAULT_TARGETS
        self.error_callback = _callable(error_handler)

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
            value = function(req, name, argobj)
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
        :return: The argument value.
        """
        value = None
        if argobj.target:
            value = self._get_value(name, argobj, req=req, target=argobj.target)
            if value is not None:
                return argobj.validated(value)

        for target in self._validated_targets(targets or self.targets):
            value = self._get_value(name, argobj, req=req, target=target)
            if argobj.multiple and not (isinstance(value, list) and len(value)):
                continue
            # Found the value; validate and return it
            if value is not None:
                return argobj.validated(value)
        if value is None:
            if argobj.default is not None:
                value = argobj.default
            else:
                value = self.fallback(req, name, argobj)
            if not value and argobj.required:
                raise ValidationError('Required parameter {0!r} not found.'.format(name))
        return value

    def parse(self, argmap, req, targets=None):
        """Main request parsing method.

        :param dict argmap: Dictionary of argname:Arg object pairs.
        :param req: The request object to parse.
        :param tuple targets: Where on the request to search for values.
            Can include one or more of ``('json', 'querystring', 'form',
            'headers', 'cookies', 'files')``.
        :return: A dictionary of parsed arguments
        """
        try:
            parsed = {}
            for argname, argobj in iteritems(argmap):
                parsed_value = self.parse_arg(argname, argobj, req,
                    targets=targets or self.targets)
                # Skip missing values
                if parsed_value is None and argobj.allow_missing:
                    continue
                else:
                    parsed[argname] = parsed_value
            return parsed
        except Exception as error:
            if self.error_callback:
                self.error_callback(error)
            else:
                self.handle_error(error)

    def use_args(self, argmap, req=None, targets=None, as_kwargs=False):
        """Decorator that injects parsed arguments into a view function or method.

        Example usage with Flask: ::

            @app.route('/echo', methods=['get', 'post'])
            @parser.use_args({'name': Arg(type_=str)})
            def greet(args):
                return 'Hello ' + args['name']

        :param dict argmap: Dictionary of argument_name:Arg object pairs.
        :param tuple targets: Where on the request to search for values.
        :param bool as_kwargs: Whether to insert arguments as keyword arguments.
        """
        targets = targets or self.DEFAULT_TARGETS
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                parsed_args = self.parse(argmap, req=req, targets=targets)
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
        """Decorator that injects parsed arguments into a view function or method as keyword arguments.

        This is a shortcut to :py:func:`use_args` with as_kwargs=True

        Example usage with Flask: ::

            @app.route('/echo', methods=['get', 'post'])
            @parser.use_kwargs({'name': Arg(type_=str)})
            def greet(name):
                return 'Hello ' + name
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
        """Pulls a JSON value from a request object or returns ``None`` if the
        value cannot be found.
        """
        return None

    def parse_querystring(self, req, name, arg):
        """Pulls a value from the query string of a request object or returns ``None`` if
        the value cannot be found.
        """
        return None

    def parse_form(self, req, name, arg):
        """Pulls a value from the form data of a request object or returns
        ``None`` if the value cannot be found.
        """
        return None

    def parse_headers(self, req, name, arg):
        """Pulls a value from the headers or returns ``None`` if the value
        cannot be found.
        """
        return None

    def parse_cookies(self, req, name, arg):
        """Pulls a cookie value from the request or returns ``None`` if the value
        cannot be found.
        """
        return None

    def parse_files(self, req, name, arg):
        """Pull a file from the request or return ``None`` if the value file
        cannot be found.
        """
        return None

    def handle_error(self, error):
        """Called if an error occurs while parsing args.
        """
        raise error

    def fallback(self, req, name, arg):
        """Called if all other parsing functions (parse_json, parse_form...) return
        ``None``.
        """
        return None
