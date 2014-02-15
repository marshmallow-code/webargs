# -*- coding: utf-8 -*-
"""Django request argument parsing.

Example usage: ::

    from django.views.generic import View
    from django.http import HttpResponse
    from webargs import Arg
    from webargs.djangoparser import use_args

    hello_args = {
        'name': Arg(str, default='World')
    }

    class MyView(View):

        @use_args(hello_args)
        def get(self, args, request):
            return HttpResponse('Hello ' + args['name'])
"""
import json
import functools

from webargs import core


class DjangoParser(core.Parser):
    """Django request argument parser."""

    def parse_querystring(self, req, name):
        """Pull the querystring value from the request."""
        return req.GET.get(name, None)

    def parse_form(self, req, name):
        """Pull the form value from the request."""
        return req.POST.get(name, None)

    def parse_json(self, req, name):
        """Pull a json value from the request body."""
        try:
            reqdata = json.loads(req.body.decode('utf-8'))
            return reqdata.get(name, None)
        except (AttributeError, ValueError):
            return None

    def parse_cookies(self, req, name):
        """Pull the value from the cookiejar."""
        return req.COOKIES.get(name, None)

    def parse_headers(self, req, name):
        raise NotImplementedError('Header parsing not supported by {0}'
            .format(self.__class__.__name__))

    def use_args(self, argmap, req=None, targets=core.DEFAULT_TARGETS):
        """Decorator that injects parsed arguments into a view function or method.

        Example: ::

            @parser.use_args({'name': 'World'})
            def myview(request, args):
                return HttpResponse('Hello ' + args['name'])

        :param dict argmap: Dictionary of argument_name:Arg object pairs.
        :param tuple targets: Where on the request to search for values.
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(obj, *args, **kwargs):
                # The first argument is either `self` or `request`
                try:  # get self.request
                    request = obj.request
                except AttributeError:  # first arg is request
                    request = obj
                parsed_args = self.parse(argmap, req=request, targets=targets)
                return func(obj, parsed_args, *args, **kwargs)
            return wrapper
        return decorator

use_args = DjangoParser().use_args
