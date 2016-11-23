# -*- coding: utf-8 -*-
"""Asynchronous request parser. Compatible with Python>=3.4."""
import asyncio
import collections
import inspect
import functools

import marshmallow as ma
from marshmallow.compat import iteritems
from marshmallow.utils import missing

from webargs import core

class AsyncParser(core.Parser):
    """Asynchronous variant of `webargs.core.Parser`, where parsing methods may be
    either coroutines or regular methods.
    """

    @asyncio.coroutine
    def _parse_request(self, schema, req, locations):
        if schema.many:
            assert 'json' in locations, "schema.many=True is only supported for JSON location"
            # The ad hoc Nested field is more like a workaround or a helper, and it servers its
            # purpose fine. However, if somebody has a desire to re-design the support of
            # bulk-type arguments, go ahead.
            parsed = yield from self.parse_arg(
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
                parsed_value = yield from self.parse_arg(argname, field_obj, req, locations)
                # If load_from is specified on the field, try to parse from that key
                if parsed_value is missing and field_obj.load_from:
                    parsed_value = yield from self.parse_arg(field_obj.load_from,
                                                             field_obj, req, locations)
                    argname = field_obj.load_from
                parsed[argname] = parsed_value
        return parsed

    # TODO: Lots of duplication from core.Parser here. Rethink.
    @asyncio.coroutine
    def parse(self, argmap, req=None, locations=None, validate=None, force_all=False):
        """Coroutine variant of `webargs.core.Parser`.

        Receives the same arguments as `webargs.core.Parser.parse`.
        """
        req = req if req is not None else self.get_default_request()
        assert req is not None, 'Must pass req object'
        ret = None
        validators = core._ensure_list_of_callables(validate)
        schema = self._get_schema(argmap, req)
        try:
            parsed = yield from self._parse_request(schema=schema, req=req, locations=locations)
            result = self.load(parsed, schema)
            self._validate_arguments(result.data, validators)
        except ma.exceptions.ValidationError as error:
            self._on_validation_error(error)
        else:
            ret = result.data
        finally:
            self.clear_cache()
        if force_all:
            core.fill_in_missing_args(ret, argmap)
        return ret

    def use_args(self, argmap, req=None, locations=None, as_kwargs=False, validate=None):
        """Decorator that injects parsed arguments into a view function or method.

        .. warning::
            This will not work with `async def` coroutines. Either use a generator-based
            coroutine decorated with `asyncio.coroutine` or use the
            `parse <webargs.async.AsyncParser.parse>` method.

        Receives the same arguments as `webargs.core.Parser.use_args`.
        """
        locations = locations or self.locations
        request_obj = req
        # Optimization: If argmap is passed as a dictionary, we only need
        # to generate a Schema once
        if isinstance(argmap, collections.Mapping):
            argmap = core.argmap2schema(argmap)()

        def decorator(func):
            req_ = request_obj

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                req_obj = req_

                # if as_kwargs is passed, must include all args
                force_all = as_kwargs

                if not req_obj:
                    req_obj = self.get_request_from_view_args(func, args, kwargs)
                # NOTE: At this point, argmap may be a Schema, callable, or dict
                parsed_args = yield from self.parse(argmap,
                                                    req=req_obj, locations=locations,
                                                    validate=validate, force_all=force_all)
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
        """Decorator that injects parsed arguments into a view function or method.

        .. warning::
            This will not work with `async def` coroutines. Either use a generator-based
            coroutine decorated with `asyncio.coroutine` or use the
            `parse <webargs.async.AsyncParser.parse>` method.

        Receives the same arguments as `webargs.core.Parser.use_kwargs`.

        """
        return super().use_kwargs(*args, **kwargs)

    @asyncio.coroutine
    def parse_arg(self, name, field, req, locations=None):
        location = field.metadata.get('location')
        if location:
            locations_to_check = self._validated_locations([location])
        else:
            locations_to_check = self._validated_locations(locations or self.locations)

        for location in locations_to_check:
            value = yield from self._get_value(name, field, req=req, location=location)
            # Found the value; validate and return it
            if value is not core.missing:
                return value
        return core.missing

    @asyncio.coroutine
    def _get_value(self, name, argobj, req, location):
        # Parsing function to call
        # May be a method name (str) or a function
        func = self.__location_map__.get(location)
        if func:
            if inspect.isfunction(func):
                function = func
            else:
                function = getattr(self, func)
            if asyncio.iscoroutinefunction(function):
                value = yield from function(req, name, argobj)
            else:
                value = function(req, name, argobj)
        else:
            raise ValueError('Invalid location: "{0}"'.format(location))
        return value
