"""Asynchronous request parser. Compatible with Python>=3.5."""
import asyncio
import functools
import inspect
import typing
from collections.abc import Mapping

from marshmallow import Schema, ValidationError
from marshmallow.fields import Field
import marshmallow as ma

from webargs import core

Request = typing.TypeVar("Request")
ArgMap = typing.Union[Schema, typing.Mapping[str, Field]]
Validate = typing.Union[typing.Callable, typing.Iterable[typing.Callable]]


class AsyncParser(core.Parser):
    """Asynchronous variant of `webargs.core.Parser`, where parsing methods may be
    either coroutines or regular methods.
    """

    # TODO: Lots of duplication from core.Parser here. Rethink.
    async def parse(
        self,
        argmap: ArgMap,
        req: Request = None,
        *,
        location: str = None,
        validate: Validate = None,
        error_status_code: typing.Union[int, None] = None,
        error_headers: typing.Union[typing.Mapping[str, str], None] = None
    ) -> typing.Union[typing.Mapping, None]:
        """Coroutine variant of `webargs.core.Parser`.

        Receives the same arguments as `webargs.core.Parser.parse`.
        """
        req = req if req is not None else self.get_default_request()
        location = location or self.location
        if req is None:
            raise ValueError("Must pass req object")
        data = None
        validators = core._ensure_list_of_callables(validate)
        schema = self._get_schema(argmap, req)
        try:
            location_data = await self._load_location_data(
                schema=schema, req=req, location=location
            )
            result = schema.load(location_data)
            data = result.data if core.MARSHMALLOW_VERSION_INFO[0] < 3 else result
            self._validate_arguments(data, validators)
        except ma.exceptions.ValidationError as error:
            await self._on_validation_error(
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

    async def _on_validation_error(
        self,
        error: ValidationError,
        req: Request,
        schema: Schema,
        location: str,
        *,
        error_status_code: typing.Union[int, None],
        error_headers: typing.Union[typing.Mapping[str, str], None]
    ) -> None:
        # rewrite messages to be namespaced under the location which created
        # them
        # e.g. {"json":{"foo":["Not a valid integer."]}}
        #      instead of
        #      {"foo":["Not a valid integer."]}
        error.messages = {location: error.messages}
        error_handler = self.error_callback or self.handle_error
        await error_handler(
            error,
            req,
            schema,
            error_status_code=error_status_code,
            error_headers=error_headers,
        )

    def use_args(
        self,
        argmap: ArgMap,
        req: typing.Optional[Request] = None,
        *,
        location: str = None,
        as_kwargs: bool = False,
        validate: Validate = None,
        error_status_code: typing.Optional[int] = None,
        error_headers: typing.Union[typing.Mapping[str, str], None] = None
    ) -> typing.Callable[..., typing.Callable]:
        """Decorator that injects parsed arguments into a view function or method.

        Receives the same arguments as `webargs.core.Parser.use_args`.
        """
        location = location or self.location
        request_obj = req
        # Optimization: If argmap is passed as a dictionary, we only need
        # to generate a Schema once
        if isinstance(argmap, Mapping):
            argmap = core.dict2schema(argmap, schema_class=self.schema_class)()

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
