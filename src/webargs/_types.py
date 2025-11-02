from __future__ import annotations

import typing

import marshmallow as ma

T = typing.TypeVar("T")

# an arg-map is one of the following
# - a schema
# - a schema class
# - a str->Field mapping
# - a `(Request) -> Schema` callable
ArgMapCallable: typing.TypeAlias = typing.Callable[[T], ma.Schema]
ArgMap: typing.TypeAlias = (
    ma.Schema
    | type[ma.Schema]
    | typing.Mapping[str, ma.fields.Field]
    | ArgMapCallable[T]
)

# a 'validate' value is a callable or collection ofcallables
ValidateArg: typing.TypeAlias = (
    None | typing.Callable | typing.Iterable[typing.Callable]
)
CallableList: typing.TypeAlias = list[typing.Callable[..., typing.Any]]

# error handlers are no-return callables
ErrorHandler: typing.TypeAlias = typing.Callable[..., typing.NoReturn]
AsyncErrorHandler: typing.TypeAlias = typing.Callable[
    ..., typing.Awaitable[typing.NoReturn]
]
