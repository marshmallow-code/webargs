from __future__ import annotations

import sys
import typing

import marshmallow as ma

if sys.version_info < (3, 10):
    from typing_extensions import TypeAlias
else:
    from typing import TypeAlias


T = typing.TypeVar("T")

# an arg-map is one of the following
# - a schema
# - a schema class
# - a str->Field mapping
# - a `(Request) -> Schema` callable
ArgMapCallable: TypeAlias = typing.Callable[[T], ma.Schema]
ArgMap: TypeAlias = typing.Union[
    ma.Schema, type[ma.Schema], typing.Mapping[str, ma.fields.Field], ArgMapCallable[T]
]

# a 'validate' value is a callable or collection ofcallables
ValidateArg: TypeAlias = typing.Union[
    None, typing.Callable, typing.Iterable[typing.Callable]
]
CallableList: TypeAlias = list[typing.Callable[..., typing.Any]]

# error handlers are no-return callables
ErrorHandler: TypeAlias = typing.Callable[..., typing.NoReturn]
AsyncErrorHandler: TypeAlias = typing.Callable[..., typing.Awaitable[typing.NoReturn]]
