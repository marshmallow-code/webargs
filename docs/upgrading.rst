Upgrading to Newer Releases
===========================

This section documents migration paths to new releases.

Upgrading to 6.0
++++++++++++++++

In webargs 6, the way that data is loaded from various locations and passed to
your schemas changed significantly. This may require you to change several
different parts of your webargs usage.

Multiple locations are no longer supported in a single call
-----------------------------------------------------------

And only JSON data is parsed by default.

Under webargs 5.x, you may have written code which did not specify a location.

Because webargs would parse data from multiple locations automatically, you did
not need to specify where a parameter, call it `q`, was passed.
`q` could be in a query parameter or in a JSON or form-post body.

Now, webargs requires that you specify only one location for data loading per
`use_args` call, and `"json"` is the default. If `q` is intended to be a query
parameter, you must be explicit and rewrite like so:

.. code-block:: python

    # webargs 5.x
    @parser.use_args({"q": ma.fields.String()})
    def foo(q):
        return some_function(user_query=q)


    # webargs 6.x
    @parser.use_args({"q": ma.fields.String()}, location="query")
    def foo(q):
        return some_function(user_query=q)

This also means that another usage from 5.x is not supported. If you had code
with multiple locations in a single `use_args`, `use_kwargs`, or `parse` call,
you must write it in multiple separate `use_args` invocations, like so:

.. code-block:: python

    # webargs 5.x
    @parser.use_args(
        {
            "q1": ma.fields.Int(location="query"),
            "q2": ma.fields.Int(location="query"),
            "h1": ma.fields.Int(location="headers"),
        },
        locations=("query", "headers"),
    )
    def foo(q1, q2, h1):
        ...


    # webargs 6.x
    @parser.use_args({"q1": ma.fields.Int(), "q2": ma.fields.Int()}, location="query")
    @parser.use_args({"h1": ma.fields.Int()}, location="headers")
    def foo(q1, q2, h1):
        ...


Fields no longer support location=...
-------------------------------------

Because a single `parser.use_args`, `parser.use_kwargs`, or `parser.parse` call
cannot specify multiple locations, it is not necessary for a field to be able
to specify its location. Rewrite code like so:

.. code-block:: python

    # webargs 5.x
    @parser.use_args({"q": ma.fields.String(location="query")})
    def foo(q):
        return some_function(user_query=q)


    # webargs 6.x
    @parser.use_args({"q": ma.fields.String()}, location="query")
    def foo(q):
        return some_function(user_query=q)

location_handler has been replaced with location_loader
-------------------------------------------------------

This is not just a name change. The expected signature of a `location_loader`
is slightly different from the signature for a `location_handler`.

Where previously your code took the incoming request data and details of a
single field being loaded, it now takes the request and the schema as a pair.
It does not return a specific field's data, but data for the whole location.
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

Data is not filtered before being passed to your schema, and it may be proxified
--------------------------------------------------------------------------------

In webargs 5.x, the schema you gave was used to pull data out of the request
object. That data was compiled into a dictionary which was then passed to your
schema.

One of the major changes in webargs 6.x allows the use of `unknown` parameter
on schemas. This lets a schema decide what to do with fields not specified in
the schema. In order to achieve this, webargs now passes the full data from
the location you selected to your schema.

However, many types of request data are so-called "multidicts" -- dictionary-like
types which can return one or multiple values as you prefer. To handle
`marshmallow.fields.List` and `webargs.fields.DelimitedList` fields correctly,
passing list data, webargs must combine schema information with the raw request
data. This is done in the
:class:`MultiDictProxy <webargs.multidictproxy.MultiDictProxy>` type, which
will often be passed to your schemas.

Therefore, you should specify `unknown=marshmallow.EXCLUDE` on your schemas if
you want to filter out unknown fields. Like so:

.. code-block:: python

    # webargs 5.x
    # this can assume that "q" is the only parameter passed, and all other
    # parameters will be ignored
    @parser.use_kwargs({"q": ma.fields.String()}, locations=("query",))
    def foo(q):
        ...


    # webargs 6.x, Solution 1: declare a schema with Meta.unknown set
    class QuerySchema(ma.Schema):
        q = ma.fields.String()

        class Meta:
            unknown = ma.EXCLUDE


    @parser.use_kwargs(QuerySchema, location="query")
    def foo(q):
        ...


    # webargs 6.x, Solution 2: instantiate a schema with unknown set
    class QuerySchema(ma.Schema):
        q = ma.fields.String()


    @parser.use_kwargs(QuerySchema(unknown=ma.EXCLUDE), location="query")
    def foo(q):
        ...


This also allows you to write code which passes the unknown parameters through,
like so:

.. code-block:: python

    # webargs 6.x only! cannot be done in 5.x
    class QuerySchema(ma.Schema):
        q = ma.fields.String()


    # will pass *all* query params through as "kwargs"
    @parser.use_kwargs(QuerySchema(unknown=ma.INCLUDE), location="query")
    def foo(q, **kwargs):
        ...


Finally, this change passes a proxy object where you once saw a dict. This
means that if your schema has a `pre_load` hook which interacts with the data,
it may need modifications. For example, a `flask` query string will be parsed
into an `ImmutableMultiDict` type, which will break pre-load hooks which modify
the data in-place. You may need to apply rewrites like so:

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
    def foo(q):
        ...


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
    def foo(q):
        ...


DelimitedList now only takes a string input
-------------------------------------------

Combining `List` and string parsing functionality in a single type had some
messy corner cases. For the most part, this should not require rewrites. But if
you need to allow both usages in your API, you can do a rewrite like so:

.. code-block:: python

    # webargs 5.x
    # this allows ...?x=1&x=2&x=3
    # as well as ...?x=1,2,3
    @use_kwargs({"x": webargs.fields.DelimitedList(ma.fields.Int)}, locations=("query",))
    def foo(x):
        ...


    # webargs 6.x
    # this accepts x=1,2,3 but NOT x=1&x=2&x=3
    @use_kwargs({"x": webargs.fields.DelimitedList(ma.fields.Int)}, location="query")
    def foo(x):
        ...


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
    def foo(x):
        ...


ValidationError messages are namespaced under the location
----------------------------------------------------------

If you were parsing ValidationError messages, you will notice a change in the
messages produced by webargs.
What would previously have come back with messages like `{"foo":["Not a valid integer."]}`
will now have messages nested one layer deeper, like
`{"json":{"foo":["Not a valid integer."]}}`.

To rewrite code which was handling these errors, you will need to be prepared
to traverse messages by one additional level. For example:

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


Some functions take keyword-only arguments now
----------------------------------------------

The signature of several methods has changed to have keyword-only arguments.
For the most part, this should not require any changes, but here's a list of
the changes.

`parser.error_handler` methods:

.. code-block:: python

    # webargs 5.x
    def handle_error(error, req, schema, status_code, headers):
        ...


    # webargs 6.x
    def handle_error(error, req, schema, *, status_code, headers):
        ...

`parser.__init__` methods:

.. code-block:: python

    # webargs 5.x
    def __init__(self, location=None, error_handler=None, schema_class=None):
        ...


    # webargs 6.x
    def __init__(self, location=None, *, error_handler=None, schema_class=None):
        ...

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
    ):
        ...


    # webargs 6.x
    def parse(
        self,
        argmap,
        req=None,
        *,
        location=None,
        validate=None,
        error_status_code=None,
        error_headers=None
    ):
        ...


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
    ):
        ...


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
        error_headers=None
    ):
        ...


    # use_kwargs is just an alias for use_args with as_kwargs=True

and finally, the `dict2schema` function:

.. code-block:: python

    # webargs 5.x
    def dict2schema(dct, schema_class=ma.Schema):
        ...


    # webargs 6.x
    def dict2schema(dct, *, schema_class=ma.Schema):
        ...


PyramidParser now appends arguments (used to prepend)
-----------------------------------------------------

`PyramidParser.use_args` was not conformant with the other parsers in webargs.
While all other parsers added new arguments to the end of the argument list of
a decorated view function, the Pyramid implementation added them to the front
of the argument list. This has been corrected, but as a result pyramid views
with `use_args` will need to be rewritten like so:

.. code-block:: python

    from webargs.pyramidparser import use_args

    # webargs 5.x
    @use_args({"q": ma.fields.String()}, locations=("query",))
    def viewfunc(q, request):
        ...


    # webargs 6.x
    @use_args({"q": ma.fields.String()}, location="query")
    def viewfunc(request, q):
        ...
