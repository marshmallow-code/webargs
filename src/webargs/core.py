from __future__ import annotations

import asyncio
import functools
import json
import logging
import typing

import marshmallow as ma
from marshmallow import ValidationError
from marshmallow.utils import missing

from webargs.multidictproxy import MultiDictProxy

logger = logging.getLogger(__name__)


__all__ = [
    "ValidationError",
    "Parser",
    "missing",
    "parse_json",
]


Request = typing.TypeVar("Request")
ArgMap = typing.Union[
    ma.Schema,
    typing.Type[ma.Schema],
    typing.Mapping[str, typing.Union[ma.fields.Field, typing.Type[ma.fields.Field]]],
    typing.Callable[[Request], ma.Schema],
]

ValidateArg = typing.Union[None, typing.Callable, typing.Iterable[typing.Callable]]
CallableList = typing.List[typing.Callable]
ErrorHandler = typing.Callable[..., typing.NoReturn]
# generic type var with no particular meaning
T = typing.TypeVar("T")
# type var for callables, to make type-preserving decorators
C = typing.TypeVar("C", bound=typing.Callable)
# type var for multidict proxy classes
MultiDictProxyT = typing.TypeVar("MultiDictProxyT", bound=MultiDictProxy)
# type var for a callable which is an error handler
# used to ensure that the error_handler decorator is type preserving
ErrorHandlerT = typing.TypeVar("ErrorHandlerT", bound=ErrorHandler)

AsyncErrorHandler = typing.Callable[..., typing.Awaitable[typing.NoReturn]]


# a value used as the default for arguments, so that when `None` is passed, it
# can be distinguished from the default value
_UNKNOWN_DEFAULT_PARAM = "_default"

DEFAULT_VALIDATION_STATUS: int = 422


def _record_arg_name(f: typing.Callable[..., typing.Any], argname: str | None) -> None:
    if argname is None:
        return
    if not hasattr(f, "__webargs_argnames__"):
        f.__webargs_argnames__ = ()  # type: ignore[attr-defined]
    f.__webargs_argnames__ += (argname,)  # type: ignore[attr-defined]


def _iscallable(x: typing.Any) -> bool:
    # workaround for
    #   https://github.com/python/mypy/issues/9778
    return callable(x)


def _callable_or_raise(obj: T | None) -> T | None:
    """Makes sure an object is callable if it is not ``None``. If not
    callable, a ValueError is raised.
    """
    if obj and not _iscallable(obj):
        raise ValueError(f"{obj!r} is not callable.")
    return obj


def get_mimetype(content_type: str) -> str:
    return content_type.split(";")[0].strip()


# Adapted from werkzeug:
# https://github.com/mitsuhiko/werkzeug/blob/master/werkzeug/wrappers.py
def is_json(mimetype: str | None) -> bool:
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


def parse_json(s: typing.AnyStr, *, encoding: str = "utf-8") -> typing.Any:
    if isinstance(s, str):
        decoded = s
    else:
        try:
            decoded = s.decode(encoding)
        except UnicodeDecodeError as exc:
            raise json.JSONDecodeError(
                f"Bytes decoding error : {exc.reason}",
                doc=str(exc.object),
                pos=exc.start,
            ) from exc
    return json.loads(decoded)


def _ensure_list_of_callables(obj: typing.Any) -> CallableList:
    if obj:
        if isinstance(obj, (list, tuple)):
            validators = typing.cast(CallableList, list(obj))
        elif callable(obj):
            validators = [obj]
        else:
            raise ValueError(f"{obj!r} is not a callable or list of callables.")
    else:
        validators = []
    return validators


class Parser(typing.Generic[Request]):
    """Base parser class that provides high-level implementation for parsing
    a request.

    Descendant classes must provide lower-level implementations for reading
    data from  different locations, e.g. ``load_json``, ``load_querystring``,
    etc.

    :param str location: Default location to use for data
    :param str unknown: A default value to pass for ``unknown`` when calling the
        schema's ``load`` method. Defaults to ``marshmallow.EXCLUDE`` for non-body
        locations and ``marshmallow.RAISE`` for request bodies. Pass ``None`` to use the
        schema's setting instead.
    :param callable error_handler: Custom error handler function.
    """

    #: Default location to check for data
    DEFAULT_LOCATION: str = "json"
    #: Default value to use for 'unknown' on schema load
    #  on a per-location basis
    DEFAULT_UNKNOWN_BY_LOCATION: dict[str, str | None] = {
        "json": None,
        "form": None,
        "json_or_form": None,
        "querystring": ma.EXCLUDE,
        "query": ma.EXCLUDE,
        "headers": ma.EXCLUDE,
        "cookies": ma.EXCLUDE,
        "files": ma.EXCLUDE,
    }
    #: The marshmallow Schema class to use when creating new schemas
    DEFAULT_SCHEMA_CLASS: type[ma.Schema] = ma.Schema
    #: Default status code to return for validation errors
    DEFAULT_VALIDATION_STATUS: int = DEFAULT_VALIDATION_STATUS
    #: Default error message for validation errors
    DEFAULT_VALIDATION_MESSAGE: str = "Invalid value."
    #: field types which should always be treated as if they set `is_multiple=True`
    KNOWN_MULTI_FIELDS: list[type] = [ma.fields.List, ma.fields.Tuple]
    #: set use_args to use a positional argument (rather than a keyword argument)
    #  defaults to True, but will become False in a future major version
    USE_ARGS_POSITIONAL: bool = True

    #: Maps location => method name
    __location_map__: dict[str, str | typing.Callable] = {
        "json": "load_json",
        "querystring": "load_querystring",
        "query": "load_querystring",
        "form": "load_form",
        "headers": "load_headers",
        "cookies": "load_cookies",
        "files": "load_files",
        "json_or_form": "load_json_or_form",
    }

    def __init__(
        self,
        location: str | None = None,
        *,
        unknown: str | None = _UNKNOWN_DEFAULT_PARAM,
        error_handler: ErrorHandler | None = None,
        schema_class: type[ma.Schema] | None = None,
    ) -> None:
        self.location = location or self.DEFAULT_LOCATION
        self.error_callback: ErrorHandler | None = _callable_or_raise(error_handler)
        self.schema_class = schema_class or self.DEFAULT_SCHEMA_CLASS
        self.unknown = unknown

    def _makeproxy(
        self,
        multidict: typing.Any,
        schema: ma.Schema,
        *,
        cls: type[MultiDictProxyT] | type[MultiDictProxy] = MultiDictProxy,
    ) -> MultiDictProxyT | MultiDictProxy:
        """Create a multidict proxy object with options from the current parser"""
        return cls(multidict, schema, known_multi_fields=tuple(self.KNOWN_MULTI_FIELDS))

    def _get_loader(self, location: str) -> typing.Callable:
        """Get the loader function for the given location.

        :raises: ValueError if a given location is invalid.
        """
        valid_locations = set(self.__location_map__.keys())
        if location not in valid_locations:
            raise ValueError(f"Invalid location argument: {location}")

        # Parsing function to call
        # May be a method name (str) or a function
        func = self.__location_map__[location]
        if isinstance(func, str):
            return getattr(self, func)
        return func

    def _load_location_data(
        self, *, schema: ma.Schema, req: Request, location: str
    ) -> typing.Any:
        """Return a dictionary-like object for the location on the given request.

        Needs to have the schema in hand in order to correctly handle loading
        lists from multidict objects and `many=True` schemas.
        """
        loader_func = self._get_loader(location)
        return loader_func(req, schema)

    async def _async_load_location_data(
        self, schema: ma.Schema, req: Request, location: str
    ) -> typing.Any:
        # an async variant of the _load_location_data method
        # the loader function itself may or may not be async
        loader_func = self._get_loader(location)
        if asyncio.iscoroutinefunction(loader_func):
            data = await loader_func(req, schema)
        else:
            data = loader_func(req, schema)
        return data

    def _on_validation_error(
        self,
        error: ValidationError,
        req: Request,
        schema: ma.Schema,
        location: str,
        *,
        error_status_code: int | None,
        error_headers: typing.Mapping[str, str] | None,
    ) -> typing.NoReturn:
        # rewrite messages to be namespaced under the location which created
        # them
        # e.g. {"json":{"foo":["Not a valid integer."]}}
        #      instead of
        #      {"foo":["Not a valid integer."]}
        error.messages = {location: error.messages}
        error_handler: ErrorHandler = self.error_callback or self.handle_error
        error_handler(
            error,
            req,
            schema,
            error_status_code=error_status_code,
            error_headers=error_headers,
        )

    async def _async_on_validation_error(
        self,
        error: ValidationError,
        req: Request,
        schema: ma.Schema,
        location: str,
        *,
        error_status_code: int | None,
        error_headers: typing.Mapping[str, str] | None,
    ) -> typing.NoReturn:
        # an async-aware variant of the _on_validation_error method
        error.messages = {location: error.messages}
        error_handler = self.error_callback or self.handle_error
        # an async error handler was registered, await it
        if asyncio.iscoroutinefunction(error_handler):
            async_error_handler = typing.cast(AsyncErrorHandler, error_handler)
            await async_error_handler(
                error,
                req,
                schema,
                error_status_code=error_status_code,
                error_headers=error_headers,
            )
        # the error handler was synchronous (e.g. Parser.handle_error) so it
        # will raise an error
        else:
            error_handler(
                error,
                req,
                schema,
                error_status_code=error_status_code,
                error_headers=error_headers,
            )

    def _validate_arguments(self, data: typing.Any, validators: CallableList) -> None:
        # although `data` is typically a Mapping, nothing forbids a `schema.load`
        # from returning an arbitrary object subject to validators
        for validator in validators:
            if validator(data) is False:
                msg = self.DEFAULT_VALIDATION_MESSAGE
                raise ValidationError(msg, data=data)

    def _get_schema(self, argmap: ArgMap, req: Request) -> ma.Schema:
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
        elif isinstance(argmap, typing.Mapping):
            if not isinstance(argmap, dict):
                argmap = dict(argmap)
            schema = self.schema_class.from_dict(argmap)()
        else:
            raise TypeError(f"argmap was of unexpected type {type(argmap)}")
        return schema

    def _prepare_for_parse(
        self,
        argmap: ArgMap,
        req: Request | None = None,
        location: str | None = None,
        unknown: str | None = _UNKNOWN_DEFAULT_PARAM,
        validate: ValidateArg = None,
    ) -> tuple[None, Request, str, CallableList, ma.Schema]:
        # validate parse() arguments and handle defaults
        # (shared between sync and async variants)
        req = req if req is not None else self.get_default_request()
        if req is None:
            raise ValueError("Must pass req object")
        location = location or self.location
        validators = _ensure_list_of_callables(validate)
        schema = self._get_schema(argmap, req)
        return (None, req, location, validators, schema)

    def _process_location_data(
        self,
        location_data: typing.Any,
        schema: ma.Schema,
        req: Request,
        location: str,
        unknown: str | None,
        validators: CallableList,
    ) -> typing.Any:
        # after the data has been fetched from a registered location,
        # this is how it is processed
        # (shared between sync and async variants)

        # when the desired location is empty (no data), provide an empty
        # dict as the default so that optional arguments in a location
        # (e.g. optional JSON body) work smoothly
        if location_data is missing:
            location_data = {}

        # precedence order: explicit, instance setting, default per location
        unknown = (
            unknown
            if unknown != _UNKNOWN_DEFAULT_PARAM
            else (
                self.unknown
                if self.unknown != _UNKNOWN_DEFAULT_PARAM
                else self.DEFAULT_UNKNOWN_BY_LOCATION.get(location)
            )
        )
        load_kwargs: dict[str, typing.Any] = {"unknown": unknown} if unknown else {}
        preprocessed_data = self.pre_load(
            location_data, schema=schema, req=req, location=location
        )
        data = schema.load(preprocessed_data, **load_kwargs)
        self._validate_arguments(data, validators)
        return data

    def parse(
        self,
        argmap: ArgMap,
        req: Request | None = None,
        *,
        location: str | None = None,
        unknown: str | None = _UNKNOWN_DEFAULT_PARAM,
        validate: ValidateArg = None,
        error_status_code: int | None = None,
        error_headers: typing.Mapping[str, str] | None = None,
    ) -> typing.Any:
        """Main request parsing method.

        :param argmap: Either a `marshmallow.Schema`, a `dict`
            of argname -> `marshmallow.fields.Field` pairs, or a callable
            which accepts a request and returns a `marshmallow.Schema`.
        :param req: The request object to parse.
        :param str location: Where on the request to load values.
            Can be any of the values in :py:attr:`~__location_map__`. By
            default, that means one of ``('json', 'query', 'querystring',
            'form', 'headers', 'cookies', 'files', 'json_or_form')``.
        :param str unknown: A value to pass for ``unknown`` when calling the
            schema's ``load`` method. Defaults to ``marshmallow.EXCLUDE`` for non-body
            locations and ``marshmallow.RAISE`` for request bodies. Pass ``None`` to use
            the schema's setting instead.
        :param callable validate: Validation function or list of validation functions
            that receives the dictionary of parsed arguments. Validator either returns a
            boolean or raises a :exc:`ValidationError`.
        :param int error_status_code: Status code passed to error handler functions when
            a `ValidationError` is raised.
        :param dict error_headers: Headers passed to error handler functions when a
            a `ValidationError` is raised.

         :return: A dictionary of parsed arguments
        """
        data, req, location, validators, schema = self._prepare_for_parse(
            argmap, req, location, unknown, validate
        )
        try:
            location_data = self._load_location_data(
                schema=schema, req=req, location=location
            )
            data = self._process_location_data(
                location_data, schema, req, location, unknown, validators
            )
        except ma.exceptions.ValidationError as error:
            self._on_validation_error(
                error,
                req,
                schema,
                location,
                error_status_code=error_status_code,
                error_headers=error_headers,
            )
            raise ValueError(
                "_on_validation_error hook did not raise an exception"
            ) from error
        return data

    async def async_parse(
        self,
        argmap: ArgMap,
        req: Request | None = None,
        *,
        location: str | None = None,
        unknown: str | None = _UNKNOWN_DEFAULT_PARAM,
        validate: ValidateArg = None,
        error_status_code: int | None = None,
        error_headers: typing.Mapping[str, str] | None = None,
    ) -> typing.Any:
        """Coroutine variant of `webargs.core.Parser.parse`.

        Receives the same arguments as `webargs.core.Parser.parse`.
        """
        data, req, location, validators, schema = self._prepare_for_parse(
            argmap, req, location, unknown, validate
        )
        try:
            location_data = await self._async_load_location_data(
                schema=schema, req=req, location=location
            )
            data = self._process_location_data(
                location_data, schema, req, location, unknown, validators
            )
        except ma.exceptions.ValidationError as error:
            await self._async_on_validation_error(
                error,
                req,
                schema,
                location,
                error_status_code=error_status_code,
                error_headers=error_headers,
            )
            raise ValueError(
                "_on_validation_error hook did not raise an exception"
            ) from error
        return data

    def get_default_request(self) -> Request | None:
        """Optional override. Provides a hook for frameworks that use thread-local
        request objects.
        """
        return None

    def get_request_from_view_args(
        self,
        view: typing.Callable,
        args: tuple,
        kwargs: typing.Mapping[str, typing.Any],
    ) -> Request | None:
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
    def _update_args_kwargs(
        args: tuple,
        kwargs: dict[str, typing.Any],
        parsed_args: dict[str, typing.Any],
        as_kwargs: bool,
        arg_name: str | None,
    ) -> tuple[tuple, dict[str, typing.Any]]:
        """Update args or kwargs with parsed_args depending on as_kwargs"""
        if as_kwargs:
            # expand parsed_args into kwargs
            kwargs.update(parsed_args)
        else:
            if arg_name:
                # add parsed_args as a specific kwarg
                kwargs[arg_name] = parsed_args
            else:
                # Add parsed_args after other positional arguments
                args += (parsed_args,)
        return args, kwargs

    def use_args(
        self,
        argmap: ArgMap,
        req: Request | None = None,
        *,
        location: str | None = None,
        unknown: str | None = _UNKNOWN_DEFAULT_PARAM,
        as_kwargs: bool = False,
        arg_name: str | None = None,
        validate: ValidateArg = None,
        error_status_code: int | None = None,
        error_headers: typing.Mapping[str, str] | None = None,
    ) -> typing.Callable[..., typing.Callable]:
        """Decorator that injects parsed arguments into a view function or method.

        Example usage with Flask: ::

            @app.route('/echo', methods=['get', 'post'])
            @parser.use_args({'name': fields.Str()}, location="querystring")
            def greet(querystring_args):
                return 'Hello ' + querystring_args['name']

        :param argmap: Either a `marshmallow.Schema`, a `dict`
            of argname -> `marshmallow.fields.Field` pairs, or a callable
            which accepts a request and returns a `marshmallow.Schema`.
        :param str location: Where on the request to load values.
        :param str unknown: A value to pass for ``unknown`` when calling the
            schema's ``load`` method.
        :param bool as_kwargs: Whether to insert arguments as keyword arguments.
        :param str arg_name: Keyword argument name to use for arguments. Mutually
            exclusive with as_kwargs.
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

        if arg_name is not None and as_kwargs:
            raise ValueError("arg_name and as_kwargs are mutually exclusive")
        if arg_name is None and not self.USE_ARGS_POSITIONAL:
            arg_name = f"{location}_args"

        # Optimization: If argmap is passed as a dictionary, we only need
        # to generate a Schema once
        if isinstance(argmap, typing.Mapping):
            if not isinstance(argmap, dict):
                argmap = dict(argmap)
            argmap = self.schema_class.from_dict(argmap)()

        def decorator(func: typing.Callable) -> typing.Callable:
            req_ = request_obj

            # check at decoration time that a unique name is being used
            # (no arg_name conflicts)
            if arg_name is not None and not as_kwargs:
                existing_arg_names = getattr(func, "__webargs_argnames__", ())
                if arg_name in existing_arg_names:
                    raise ValueError(
                        f"Attempted to pass `arg_name='{arg_name}'` via use_args() but "
                        "that name was already used. If this came from stacked webargs "
                        "decorators, try setting `arg_name` to distinguish usages."
                    )

            if asyncio.iscoroutinefunction(func):

                @functools.wraps(func)
                async def wrapper(
                    *args: typing.Any, **kwargs: typing.Any
                ) -> typing.Any:
                    req_obj = req_

                    if not req_obj:
                        req_obj = self.get_request_from_view_args(func, args, kwargs)
                    # NOTE: At this point, argmap may be a Schema, callable, or dict
                    parsed_args = await self.async_parse(
                        argmap,
                        req=req_obj,
                        location=location,
                        unknown=unknown,
                        validate=validate,
                        error_status_code=error_status_code,
                        error_headers=error_headers,
                    )
                    args, kwargs = self._update_args_kwargs(
                        args, kwargs, parsed_args, as_kwargs, arg_name
                    )
                    return await func(*args, **kwargs)

            else:

                @functools.wraps(func)
                def wrapper(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
                    req_obj = req_

                    if not req_obj:
                        req_obj = self.get_request_from_view_args(func, args, kwargs)
                    # NOTE: At this point, argmap may be a Schema, callable, or dict
                    parsed_args = self.parse(
                        argmap,
                        req=req_obj,
                        location=location,
                        unknown=unknown,
                        validate=validate,
                        error_status_code=error_status_code,
                        error_headers=error_headers,
                    )
                    args, kwargs = self._update_args_kwargs(
                        args, kwargs, parsed_args, as_kwargs, arg_name
                    )
                    return func(*args, **kwargs)

            wrapper.__wrapped__ = func  # type: ignore
            _record_arg_name(wrapper, arg_name)
            return wrapper

        return decorator

    def use_kwargs(
        self,
        argmap: ArgMap,
        req: Request | None = None,
        *,
        location: str | None = None,
        unknown: str | None = _UNKNOWN_DEFAULT_PARAM,
        validate: ValidateArg = None,
        error_status_code: int | None = None,
        error_headers: typing.Mapping[str, str] | None = None,
    ) -> typing.Callable[..., typing.Callable]:
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
        return self.use_args(
            argmap,
            req=req,
            as_kwargs=True,
            location=location,
            unknown=unknown,
            validate=validate,
            error_status_code=error_status_code,
            error_headers=error_headers,
        )

    def location_loader(self, name: str) -> typing.Callable[[C], C]:
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

        def decorator(func: C) -> C:
            self.__location_map__[name] = func
            return func

        return decorator

    def error_handler(self, func: ErrorHandlerT) -> ErrorHandlerT:
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
            def handle_error(error, req, schema, *, error_status_code, error_headers):
                raise CustomError(error.messages)

        :param callable func: The error callback to register.
        """
        self.error_callback = func
        return func

    def pre_load(
        self,
        location_data: typing.Mapping,
        *,
        schema: ma.Schema,
        req: Request,
        location: str,
    ) -> typing.Mapping:
        """A method of the parser which can transform data after location
        loading is done. By default it does nothing, but users can subclass
        parsers and override this method.
        """
        return location_data

    def _handle_invalid_json_error(
        self,
        error: json.JSONDecodeError | UnicodeDecodeError,
        req: Request,
        *args: typing.Any,
        **kwargs: typing.Any,
    ) -> typing.NoReturn:
        """Internal hook for overriding treatment of JSONDecodeErrors.

        Invoked by default `load_json` implementation.

        External parsers can just implement their own behavior for load_json ,
        so this is not part of the public parser API.
        """
        raise error

    def load_json(self, req: Request, schema: ma.Schema) -> typing.Any:
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

    def load_json_or_form(self, req: Request, schema: ma.Schema) -> typing.Any:
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

    def _raw_load_json(self, req: Request) -> typing.Any:
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

    def load_querystring(self, req: Request, schema: ma.Schema) -> typing.Any:
        """Load the query string of a request object or return `missing` if no
        value can be found.
        """
        return missing

    def load_form(self, req: Request, schema: ma.Schema) -> typing.Any:
        """Load the form data of a request object or return `missing` if no
        value can be found.
        """
        return missing

    def load_headers(self, req: Request, schema: ma.Schema) -> typing.Any:
        """Load the headers or return `missing` if no value can be found."""
        return missing

    def load_cookies(self, req: Request, schema: ma.Schema) -> typing.Any:
        """Load the cookies from the request or return `missing` if no value
        can be found.
        """
        return missing

    def load_files(self, req: Request, schema: ma.Schema) -> typing.Any:
        """Load files from the request or return `missing` if no values can be
        found.
        """
        return missing

    def handle_error(
        self,
        error: ValidationError,
        req: Request,
        schema: ma.Schema,
        *,
        error_status_code: int,
        error_headers: typing.Mapping[str, str],
    ) -> typing.NoReturn:
        """Called if an error occurs while parsing args. By default, just logs and
        raises ``error``.
        """
        logger.error(error)
        raise error
