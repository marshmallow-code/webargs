"""Asynchronous request parser."""
from __future__ import annotations

import typing

from webargs import core


class AsyncParser(core.Parser[core.Request]):
    """Asynchronous variant of `webargs.core.Parser`.

    The ``parse`` method is redefined to be ``async``.
    """

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
    ) -> typing.Any:
        """Coroutine variant of `webargs.core.Parser`.

        Receives the same arguments as `webargs.core.Parser.parse`.
        """
        data = await self.async_parse(
            argmap,
            req,
            location=location,
            unknown=unknown,
            validate=validate,
            error_status_code=error_status_code,
            error_headers=error_headers,
        )
        return data
