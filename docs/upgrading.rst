Upgrading to Newer Releases
===========================

This section documents migration paths to new releases.

Upgrading to 8.0
++++++++++++++++

In 8.0, the default values for ``unknown`` were changed.
When the location is set to ``json``, ``form``, or ``json_or_form``, the
default for ``unknown`` is now ``None``. Previously, the default was ``RAISE``.

Because ``RAISE`` is the default value for ``unknown`` on marshmallow schemas,
this change only affects usage in which the following conditions are met:

* A schema with ``unknown`` set to ``INCLUDE`` or ``EXCLUDE`` is passed to
  webargs ``use_args``, ``use_kwargs``, or ``parse``

* ``unknown`` is not passed explicitly to the webargs function

* ``location`` is not set (default of ``json``) or is set explicitly to
  ``json``, ``form``, or ``json_or__form``

For example

.. code-block:: python

    import marshmallow as ma


    class BodySchema(ma.Schema):
        foo = ma.fields.String()

        class Meta:
            unknown = ma.EXCLUDE


    @parser.use_args(BodySchema)
    def foo(data): ...


In this case, under webargs 7.0 the schema ``unknown`` setting of ``EXCLUDE``
would be ignored. Instead, ``unknown=RAISE`` would be used.

In webargs 8.0, the schema ``unknown`` is used.

To get the webargs 7.0 behavior (overriding the Schema ``unknown``), simply
pass ``unknown`` to ``use_args``, as in

.. code-block:: python

    @parser.use_args(BodySchema, unknown=ma.RAISE)
    def foo(data): ...

Upgrading to 7.0
++++++++++++++++

`unknown` is Now Settable by the Parser
---------------------------------------

As of 7.0, `Parsers` have multiple settings for controlling the value for
`unknown` which is passed to `schema.load` when parsing.

To set unknown behavior on a parser, see the advanced doc on this topic:
:ref:`advanced_setting_unknown`.

Importantly, by default, any schema setting for `unknown` will be overridden by
the `unknown` settings for the parser.

In order to use a schema's `unknown` value, set `unknown=None` on the parser.
In 6.x versions of webargs, schema values for `unknown` are used, so the
`unknown=None` setting is the best way to emulate this.

To get identical behavior:

.. code-block:: python

    # assuming you have a schema named MySchema


    # webargs 6.x
    @parser.use_args(MySchema)
    def foo(args): ...


    # webargs 7.x
    # as a parameter to use_args or parse
    @parser.use_args(MySchema, unknown=None)
    def foo(args): ...


    # webargs 7.x
    # as a parser setting
    # example with flaskparser, but any parser class works
    parser = FlaskParser(unknown=None)


    @parser.use_args(MySchema)
    def foo(args): ...

Upgrading to 6.0
++++++++++++++++

Multiple Locations Are No Longer Supported In A Single Call
-----------------------------------------------------------

The default location is JSON/body.

Under webargs 5.x, code often did not have to specify a location.

Because webargs would parse data from multiple locations automatically, users
did not need to specify where a parameter, call it `q`, was passed.
`q` could be in a query parameter or in a JSON or form-post body.

Now, webargs requires that users specify only one location for data loading per
`use_args` call, and `"json"` is the default. If `q` is intended to be a query
parameter, the developer must be explicit and rewrite like so:

.. code-block:: python

    # webargs 5.x
    @parser.use_args({"q": ma.fields.String()})
    def foo(args):
        return some_function(user_query=args.get("q"))


    # webargs 6.x
    @parser.use_args({"q": ma.fields.String()}, location="query")
    def foo(args):
        return some_function(user_query=args.get("q"))

This also means that another usage from 5.x is not supported. Code with
multiple locations in a single `use_args`, `use_kwargs`, or `parse` call
must be rewritten in multiple separate `use_args` or `use_kwargs` invocations,
like so:

.. code-block:: python

    # webargs 5.x
    @parser.use_kwargs(
        {
            "q1": ma.fields.Int(location="query"),
            "q2": ma.fields.Int(location="query"),
            "h1": ma.fields.Int(location="headers"),
        },
        locations=("query", "headers"),
    )
    def foo(q1, q2, h1): ...


    # webargs 6.x
    @parser.use_kwargs({"q1": ma.fields.Int(), "q2": ma.fields.Int()}, location="query")
    @parser.use_kwargs({"h1": ma.fields.Int()}, location="headers")
    def foo(q1, q2, h1): ...


Fields No Longer Support location=...
-------------------------------------

Because a single `parser.use_args`, `parser.use_kwargs`, or `parser.parse` call
cannot specify multiple locations, it is not necessary for a field to be able
to specify its location. Rewrite code like so:

.. code-block:: python

    # webargs 5.x
    @parser.use_args({"q": ma.fields.String(location="query")})
    def foo(args):
        return some_function(user_query=args.get("q"))


    # webargs 6.x
    @parser.use_args({"q": ma.fields.String()}, location="query")
    def foo(args):
        return some_function(user_query=args.get("q"))

location_handler Has Been Replaced With location_loader
-------------------------------------------------------

This is not just a name change. The expected signature of a `location_loader`
is slightly different from the signature for a `location_handler`.

Where previously a `location_handler` code took the incoming request data and
details of a single field being loaded, a `location_loader` takes the request
and the schema as a pair. It does not return a specific field's data, but data
for the whole location.

Rewrite code like this:

.. code-block:: python

    # webargs 5.x
    @parser.location_handler("data")
    def load_data(request, name, field):
        return request.data.get(name)


    # webargs 6.x
    @parser.location_loader("data")
    def load_data(request, schema):
        return request.data

Data Is Not Filtered Before Being Passed To Schemas, And It May Be Proxified
----------------------------------------------------------------------------

In webargs 5.x, the deserialization schema was used to pull data out of the
request object. That data was compiled into a dictionary which was then passed
to the schema.

One of the major changes in webargs 6.x allows the use of `unknown` parameter
on schemas. This lets a schema decide what to do with fields not specified in
the schema. In order to achieve this, webargs now passes the full data from
the specified location to the schema.

Therefore, users should specify `unknown=marshmallow.EXCLUDE` on their schemas in
order to filter out unknown fields. Like so:

.. code-block:: python

    # webargs 5.x
    # this can assume that "q" is the only parameter passed, and all other
    # parameters will be ignored
    @parser.use_kwargs({"q": ma.fields.String()}, locations=("query",))
    def foo(q): ...


    # webargs 6.x, Solution 1: declare a schema with Meta.unknown set
    class QuerySchema(ma.Schema):
        q = ma.fields.String()

        class Meta:
            unknown = ma.EXCLUDE


    @parser.use_kwargs(QuerySchema, location="query")
    def foo(q): ...


    # webargs 6.x, Solution 2: instantiate a schema with unknown set
    class QuerySchema(ma.Schema):
        q = ma.fields.String()


    @parser.use_kwargs(QuerySchema(unknown=ma.EXCLUDE), location="query")
    def foo(q): ...


This also allows usage which passes the unknown parameters through, like so:

.. code-block:: python

    # webargs 6.x only! cannot be done in 5.x
    class QuerySchema(ma.Schema):
        q = ma.fields.String()


    # will pass *all* query params through as "kwargs"
    @parser.use_kwargs(QuerySchema(unknown=ma.INCLUDE), location="query")
    def foo(q, **kwargs): ...


However, many types of request data are so-called "multidicts" -- dictionary-like
types which can return one or multiple values. To handle `marshmallow.fields.List`
and `webargs.fields.DelimitedList` fields correctly, passing list data, webargs
must combine schema information with the raw request data. This is done in the
:class:`MultiDictProxy <webargs.multidictproxy.MultiDictProxy>` type, which
will often be passed to schemas.

This means that if a schema has a `pre_load` hook which interacts with the data,
it may need modifications. For example, a `flask` query string will be parsed
into an `ImmutableMultiDict` type, which will break pre-load hooks which modify
the data in-place. Such usages need rewrites like so:

.. code-block:: python

    # webargs 5.x
    # flask query params is just an example -- applies to several types
    from webargs.flaskparser import use_kwargs


    class QuerySchema(ma.Schema):
        q = ma.fields.String()

        @ma.pre_load
        def convert_nil_to_none(self, obj, **kwargs):
            if obj.get("q") == "nil":
                obj["q"] = None
            return obj


    @use_kwargs(QuerySchema, locations=("query",))
    def foo(q): ...


    # webargs 6.x
    class QuerySchema(ma.Schema):
        q = ma.fields.String()

        # unlike under 5.x, we cannot modify 'obj' in-place because writing
        # to the MultiDictProxy will try to write to the underlying
        # ImmutableMultiDict, which is not allowed
        @ma.pre_load
        def convert_nil_to_none(self, obj, **kwargs):
            # creating a dict from a MultiDictProxy works well because it
            # "unwraps" lists and delimited lists correctly
            data = dict(obj)
            if data.get("q") == "nil":
                data["q"] = None
            return data


    @parser.use_kwargs(QuerySchema, location="query")
    def foo(q): ...


DelimitedList Now Only Takes A String Input
-------------------------------------------

Combining `List` and string parsing functionality in a single type had some
messy corner cases. For the most part, this should not require rewrites. But
for APIs which need to allow both usages, rewrites are possible like so:

.. code-block:: python

    # webargs 5.x
    # this allows ...?x=1&x=2&x=3
    # as well as ...?x=1,2,3
    @use_kwargs({"x": webargs.fields.DelimitedList(ma.fields.Int)}, locations=("query",))
    def foo(x): ...


    # webargs 6.x
    # this accepts x=1,2,3 but NOT x=1&x=2&x=3
    @use_kwargs({"x": webargs.fields.DelimitedList(ma.fields.Int)}, location="query")
    def foo(x): ...


    # webargs 6.x
    # this accepts x=1,2,3 ; x=1&x=2&x=3 ; x=1,2&x=3
    # to do this, it needs a post_load hook which will flatten out the list data
    class UnpackingDelimitedListSchema(ma.Schema):
        x = ma.fields.List(webargs.fields.DelimitedList(ma.fields.Int))

        @ma.post_load
        def flatten_lists(self, data, **kwargs):
            new_x = []
            for x in data["x"]:
                new_x.extend(x)
            data["x"] = new_x
            return data


    @parser.use_kwargs(UnpackingDelimitedListSchema, location="query")
    def foo(x): ...


ValidationError Messages Are Namespaced Under The Location
----------------------------------------------------------

Code parsing ValidationError messages will notice a change in the messages
produced by webargs.
What would previously have come back with messages like `{"foo":["Not a valid integer."]}`
will now have messages nested one layer deeper, like
`{"json":{"foo":["Not a valid integer."]}}`.

To rewrite code which was handling these errors, the handler will need to be
prepared to traverse messages by one additional level. For example:

.. code-block:: python

    import logging

    log = logging.getLogger(__name__)


    # webargs 5.x
    # logs debug messages like
    #   bad value for 'foo': ["Not a valid integer."]
    #   bad value for 'bar': ["Not a valid boolean."]
    def log_invalid_parameters(validation_error):
        for field, messages in validation_error.messages.items():
            log.debug("bad value for '{}': {}".format(field, messages))


    # webargs 6.x
    # logs debug messages like
    #   bad value for 'foo' [query]: ["Not a valid integer."]
    #   bad value for 'bar' [json]: ["Not a valid boolean."]
    def log_invalid_parameters(validation_error):
        for location, fielddata in validation_error.messages.items():
            for field, messages in fielddata.items():
                log.debug("bad value for '{}' [{}]: {}".format(field, location, messages))


Custom Error Handler Argument Names Changed
-------------------------------------------

If you define a custom error handler via `@parser.error_handler` the function
arguments are now keyword-only and `status_code` and `headers` have been renamed
`error_status_code` and `error_headers`.

.. code-block:: python

    # webargs 5.x
    @parser.error_handler
    def custom_handle_error(error, req, schema, status_code, headers): ...


    # webargs 6.x
    @parser.error_handler
    def custom_handle_error(error, req, schema, *, error_status_code, error_headers): ...


Some Functions Take Keyword-Only Arguments Now
----------------------------------------------

The signature of several methods has changed to have keyword-only arguments.
For the most part, this should not require any changes, but here's a list of
the changes.

`parser.error_handler` methods:

.. code-block:: python

    # webargs 5.x
    def handle_error(error, req, schema, status_code, headers): ...


    # webargs 6.x
    def handle_error(error, req, schema, *, error_status_code, error_headers): ...

`parser.__init__` methods:

.. code-block:: python

    # webargs 5.x
    def __init__(self, location=None, error_handler=None, schema_class=None): ...


    # webargs 6.x
    def __init__(self, location=None, *, error_handler=None, schema_class=None): ...

`parser.parse`, `parser.use_args`, and `parser.use_kwargs` methods:


.. code-block:: python

    # webargs 5.x
    def parse(
        self,
        argmap,
        req=None,
        location=None,
        validate=None,
        error_status_code=None,
        error_headers=None,
    ): ...


    # webargs 6.x
    def parse(
        self,
        argmap,
        req=None,
        *,
        location=None,
        validate=None,
        error_status_code=None,
        error_headers=None,
    ): ...


    # webargs 5.x
    def use_args(
        self,
        argmap,
        req=None,
        location=None,
        as_kwargs=False,
        validate=None,
        error_status_code=None,
        error_headers=None,
    ): ...


    # webargs 6.x
    def use_args(
        self,
        argmap,
        req=None,
        *,
        location=None,
        as_kwargs=False,
        validate=None,
        error_status_code=None,
        error_headers=None,
    ): ...


    # use_kwargs is just an alias for use_args with as_kwargs=True

and finally, the `dict2schema` function:

.. code-block:: python

    # webargs 5.x
    def dict2schema(dct, schema_class=ma.Schema): ...


    # webargs 6.x
    def dict2schema(dct, *, schema_class=ma.Schema): ...


PyramidParser Now Appends Arguments (Used To Prepend)
-----------------------------------------------------

`PyramidParser.use_args` was not conformant with the other parsers in webargs.
While all other parsers added new arguments to the end of the argument list of
a decorated view function, the Pyramid implementation added them to the front
of the argument list.

This has been corrected, but as a result pyramid views with `use_args` may need
to be rewritten. The `request` object is always passed first in both versions,
so the issue is only apparent with view functions taking other positional
arguments.

For example, imagine code with a decorator for passing user information,
`pass_userinfo`, like so:

.. code-block:: python

    # a decorator which gets information about the authenticated user
    def pass_userinfo(f):
        def decorator(request, *args, **kwargs):
            return f(request, get_userinfo(), *args, **kwargs)

        return decorator

You will see a behavioral change if `pass_userinfo` is called on a function
decorated with `use_args`. The difference between the two versions will be like
so:

.. code-block:: python

    from webargs.pyramidparser import use_args


    # webargs 5.x
    # pass_userinfo is called first, webargs sees positional arguments of
    #   (userinfo,)
    # and changes it to
    #   (request, args, userinfo)
    @pass_userinfo
    @use_args({"q": ma.fields.String()}, locations=("query",))
    def viewfunc(request, args, userinfo):
        q = args.get("q")
        ...


    # webargs 6.x
    # pass_userinfo is called first, webargs sees positional arguments of
    #   (userinfo,)
    # and changes it to
    #   (request, userinfo, args)
    @pass_userinfo
    @use_args({"q": ma.fields.String()}, location="query")
    def viewfunc(request, userinfo, args):
        q = args.get("q")
        ...
