"""Asynchronous request parser."""
from __future__ import annotations

import asyncio
import functools
import inspect
import typing

from marshmallow import Schema, ValidationError
import marshmallow as ma

from webargs import core

AsyncErrorHandler = typing.Callable[..., typing.Awaitable[typing.NoReturn]]


class AsyncParser(core.Parser):
    """Asynchronous variant of `webargs.core.Parser`, where parsing methods may be
    either coroutines or regular methods.
    """

    # TODO: Lots of duplication from core.Parser here. Rethink.
    async def parse(
        self,
        argmap: core.ArgMap,
        req: core.Request | None = None,
        *,
        location: str | None = None,
        unknown: str | None = core._UNKNOWN_DEFAULT_PARAM,
        validate: core.ValidateArg = None,
        error_status_code: int | None = None,
        error_headers: typing.Mapping[str, str] | None = None,
    ) -> typing.Mapping | None:
        """Coroutine variant of `webargs.core.Parser`.

        Receives the same arguments as `webargs.core.Parser.parse`.
        """
        req = req if req is not None else self.get_default_request()
        location = location or self.location
        unknown = (
            unknown
            if unknown != core._UNKNOWN_DEFAULT_PARAM
            else (
                self.unknown
                if self.unknown != core._UNKNOWN_DEFAULT_PARAM
                else self.DEFAULT_UNKNOWN_BY_LOCATION.get(location)
            )
        )
        load_kwargs: dict[str, typing.Any] = {"unknown": unknown} if unknown else {}
        if req is None:
            raise ValueError("Must pass req object")
        data = None
        validators = core._ensure_list_of_callables(validate)
        schema = self._get_schema(argmap, req)
        try:
            location_data = await self._load_location_data(
                schema=schema, req=req, location=location
            )
            data = schema.load(location_data, **load_kwargs)
            self._validate_arguments(data, validators)
        except ma.exceptions.ValidationError as error:
            await self._async_on_validation_error(
                error,
                req,
                schema,
                location,
                error_status_code=error_status_code,
                error_headers=error_headers,
            )
        return data

    async def _load_location_data(self, schema, req, location):
        """Return a dictionary-like object for the location on the given request.

        Needs to have the schema in hand in order to correctly handle loading
        lists from multidict objects and `many=True` schemas.
        """
        loader_func = self._get_loader(location)
        if asyncio.iscoroutinefunction(loader_func):
            data = await loader_func(req, schema)
        else:
            data = loader_func(req, schema)

        # when the desired location is empty (no data), provide an empty
        # dict as the default so that optional arguments in a location
        # (e.g. optional JSON body) work smoothly
        if data is core.missing:
            data = {}
        return data

    async def _async_on_validation_error(
        self,
        error: ValidationError,
        req: core.Request,
        schema: Schema,
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
        error_handler = self.error_callback or self.handle_error
        # an async error handler was registered, await it
        if inspect.iscoroutinefunction(error_handler):
            async_error_handler = typing.cast(AsyncErrorHandler, error_handler)
            await async_error_handler(
                error,
                req,
                schema,
                error_status_code=error_status_code,
                error_headers=error_headers,
            )
            # workaround for mypy not understanding `await Awaitable[NoReturn]`
            # see: https://github.com/python/mypy/issues/8974
            raise NotImplementedError("unreachable")
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

    def use_args(
        self,
        argmap: core.ArgMap,
        req: core.Request | None = None,
        *,
        location: str = None,
        unknown=core._UNKNOWN_DEFAULT_PARAM,
        as_kwargs: bool = False,
        validate: core.ValidateArg = None,
        error_status_code: int | None = None,
        error_headers: typing.Mapping[str, str] | None = None,
    ) -> typing.Callable[..., typing.Callable]:
        """Decorator that injects parsed arguments into a view function or method.

        Receives the same arguments as `webargs.core.Parser.use_args`.
        """
        location = location or self.location
        request_obj = req
        # Optimization: If argmap is passed as a dictionary, we only need
        # to generate a Schema once
        if isinstance(argmap, dict):
            argmap = self.schema_class.from_dict(argmap)()

        def decorator(func: typing.Callable) -> typing.Callable:
            req_ = request_obj

            if inspect.iscoroutinefunction(func):

                @functools.wraps(func)
                async def wrapper(*args, **kwargs):
                    req_obj = req_

                    if not req_obj:
                        req_obj = self.get_request_from_view_args(func, args, kwargs)
                    # NOTE: At this point, argmap may be a Schema, callable, or dict
                    parsed_args = await self.parse(
                        argmap,
                        req=req_obj,
                        location=location,
                        unknown=unknown,
                        validate=validate,
                        error_status_code=error_status_code,
                        error_headers=error_headers,
                    )
                    args, kwargs = self._update_args_kwargs(
                        args, kwargs, parsed_args, as_kwargs
                    )
                    return await func(*args, **kwargs)

            else:

                @functools.wraps(func)  # type: ignore
                def wrapper(*args, **kwargs):
                    req_obj = req_

                    if not req_obj:
                        req_obj = self.get_request_from_view_args(func, args, kwargs)
                    # NOTE: At this point, argmap may be a Schema, callable, or dict
                    parsed_args = yield from self.parse(  # type: ignore
                        argmap,
                        req=req_obj,
                        location=location,
                        unknown=unknown,
                        validate=validate,
                        error_status_code=error_status_code,
                        error_headers=error_headers,
                    )
                    args, kwargs = self._update_args_kwargs(
                        args, kwargs, parsed_args, as_kwargs
                    )
                    return func(*args, **kwargs)

            return wrapper

        return decorator
