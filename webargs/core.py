# -*- coding: utf-8 -*-
import functools


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


class Arg(object):
    """A request argument.

    :param default: Default value for the argument. Used if the value is not found
        on the request.
    :param type type\_: Value type. Will try to convert the passed in value to this
        type. If ``None``, no type conversion will be performed.
    :param callable validate: Callable (function or object with ``__call__`` method
        defined) used for custom validation. Returns whether or not the
        value is valid.
    :param callable use: Callable used for converting or pre-processing the value.
        Example: ``use=lambda s: s.lower()``
    :param str error: Custom error message to use if validation fails.
    """
    def __init__(self, type_=None, default=None, required=False,
                 validate=None, use=None, error=None):
        self.type = type_
        self.default = default
        self.required = required
        self.validate = _callable(validate)
        self.use = _callable(use)
        self.error = error

    def validated(self, value):
        """Convert and validate the given value according to the ``type_``,
        ``use``, and ``validate`` attributes.

        :returns: The validated, converted value
        :raises: ValidationError if validation fails
        """
        ret = value
        if self.type:
            # First try to convert to self.type
            try:
                ret = self.type(value)
            except ValueError as error:
                raise ValidationError(self.error or error)
        # Then call `use`
        if self.use:
            ret = self.use(ret)
        # Then call validation function
        if self.validate and not self.validate(ret):
            msg = 'Validator {0}({1}) is not True'.format(
                self.validate.__name__, ret
            )
            raise ValidationError(self.error or msg)
        return ret

DEFAULT_TARGETS = ('querystring', 'form', 'json',)


class Parser(object):
    """Base parser class that provides high-level implementation for parsing
    a request.

    Descendant classes must provide lower-level implementations for parsing
    different targets, e.g. ``parse_json``, ``parse_querystring``, etc.
    """

    #: Maps target => method name
    TARGET_MAP = {
        'json': 'parse_json',
        'querystring': 'parse_querystring',
        'form': 'parse_form',
        'headers': 'parse_headers',
        'cookies': 'parse_cookies',
    }

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

    def parse_arg(self, name, argobj, req, targets=DEFAULT_TARGETS):
        """Parse a single argument.

        :param str name: The name of the value.
        :param Arg argobj: The ``Arg`` object.
        :param req: The request object to parse.
        :param tuple targets: The targets ('json', 'querystring', etc.) where
            to search for the value.
        :return: The argument value.
        """
        value = None
        for target in self._validated_targets(targets):
            method_name = self.TARGET_MAP.get(target, None)
            if method_name:
                method = getattr(self, method_name)
                value = method(req, name)
            # Found the value; validate and return it
            if value is not None:
                return argobj.validated(value)
        if value is None:
            if argobj.default:
                value = argobj.default
            else:
                value = self.fallback(req, name)
            if value is None and argobj.required:
                raise ValidationError('Required parameter {0!r} not found.'.format(name))
        return value

    def parse(self, argmap, req, targets=DEFAULT_TARGETS):
        """Main request parsing method.

        :param dict argmap: Dictionary of argname:Arg object pairs.
        :param req: The request object to parse.
        :param tuple targets: Where on the request to search for values.
            Can include one or more of ``('json', 'querystring', 'form',
            'headers', 'cookies')``.
        :return: A dictionary of parsed arguments
        """
        try:
            return dict([(argname, self.parse_arg(argname, argobj, req, targets=targets))
                    for argname, argobj in argmap.items()])
        except Exception as error:
            self.handle_error(error)

    def use_args(self, argmap, req=None, targets=DEFAULT_TARGETS):
        """Decorator that injects parsed arguments into a view function or method.

        Example usage with Flask: ::

            @app.route('/echo', methods=['get', 'post'])
            @parser.use_args({'name': Arg(type_=str)})
            def greet(args):
                return 'Hello ' + args['name']

        :param dict argmap: Dictionary of argument_name:Arg object pairs.
        :param tuple targets: Where on the request to search for values.
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                parsed_args = self.parse(argmap, req=req, targets=targets)
                return func(parsed_args, *args, **kwargs)
            return wrapper
        return decorator

    # Abstract Methods

    def parse_json(self, req, name):
        """Pulls a JSON value from a request object or returns ``None`` if the
        value cannot be found.
        """
        return None

    def parse_querystring(self, req, name):
        """Pulls a value from the query string of a request object or returns ``None`` if
        the value cannot be found.
        """
        return None

    def parse_form(self, req, name):
        """Pulls a value from the form data of a request object or returns
        ``None`` if the value cannot be found.
        """
        return None

    def parse_headers(self, req, name):
        """Pulls a value from the headers or returns ``None`` if the value
        cannot be found.
        """
        return None

    def parse_cookies(self, req, name):
        """Pulls a cookie value from the request or returns ``None`` if the value
        cannot be found.
        """
        return None

    def handle_error(self, error):
        """Called if an error occurs while parsing args.
        """
        raise error

    def fallback(self, req, name):
        """Called if all other parsing functions (parse_json, parse_form...) return
        ``None``.
        """
        return None
