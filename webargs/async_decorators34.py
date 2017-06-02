import collections
import functools

from webargs import core


def _use_args(self, argmap, req=None, locations=None, as_kwargs=False, validate=None):
    """Decorator that injects parsed arguments into a view function or method.

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
