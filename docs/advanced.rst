Advanced Usage
==============

This section includes guides for advanced usage patterns.

Custom Location Handlers
------------------------

To add your own custom location handler, write a function that receives a request, and a :class:`Schema <marshmallow.Schema>`, then decorate that function with :func:`Parser.location_loader <webargs.core.Parser.location_loader>`.


.. code-block:: python

    from webargs import fields
    from webargs.flaskparser import parser


    @parser.location_loader("data")
    def load_data(request, schema):
        return request.data


    # Now 'data' can be specified as a location
    @parser.use_args({"per_page": fields.Int()}, location="data")
    def posts(args):
        return "displaying {} posts".format(args["per_page"])


.. NOTE::

    The schema is passed so that it can be used to wrap multidict types and
    unpack List fields correctly. If you are writing a loader for a multidict
    type, consider looking at
    :class:`MultiDictProxy <webargs.multidictproxy.MultiDictProxy>` for an
    example of how to do this.

"meta" Locations
~~~~~~~~~~~~~~~~

You can define your own locations which mix data from several existing
locations.

The `json_or_form` location does this -- first trying to load data as JSON and
then falling back to a form body -- and its implementation is quite simple:


.. code-block:: python

    def load_json_or_form(self, req, schema):
        """Load data from a request, accepting either JSON or form-encoded
        data.

        The data will first be loaded as JSON, and, if that fails, it will be
        loaded as a form post.
        """
        data = self.load_json(req, schema)
        if data is not missing:
            return data
        return self.load_form(req, schema)


You can imagine your own locations with custom behaviors like this.
For example, to mix query parameters and form body data, you might write the
following:

.. code-block:: python

   from webargs import fields
   from webargs.multidictproxy import MultiDictProxy
   from webargs.flaskparser import parser


   @parser.location_loader("query_and_form")
   def load_data(request, schema):
       # relies on the Flask (werkzeug) MultiDict type's implementation of
       # these methods, but when you're extending webargs, you may know things
       # about your framework of choice
       newdata = request.args.copy()
       newdata.update(request.form)
       return MultiDictProxy(newdata, schema)


   # Now 'query_and_form' means you can send these values in either location,
   # and they will be *mixed* together into a new dict to pass to your schema
   @parser.use_args({"favorite_food": fields.String()}, location="query_and_form")
   def set_favorite_food(args):
       ...  # do stuff
       return "your favorite food is now set to {}".format(args["favorite_food"])

marshmallow Integration
-----------------------

When you need more flexibility in defining input schemas, you can pass a marshmallow `Schema <marshmallow.Schema>` instead of a dictionary to `Parser.parse <webargs.core.Parser.parse>`, `Parser.use_args <webargs.core.Parser.use_args>`, and `Parser.use_kwargs <webargs.core.Parser.use_kwargs>`.


.. code-block:: python

    from marshmallow import Schema, fields
    from webargs.flaskparser import use_args


    class UserSchema(Schema):
        id = fields.Int(dump_only=True)  # read-only (won't be parsed by webargs)
        username = fields.Str(required=True)
        password = fields.Str(load_only=True)  # write-only
        first_name = fields.Str(missing="")
        last_name = fields.Str(missing="")
        date_registered = fields.DateTime(dump_only=True)


    @use_args(UserSchema())
    def profile_view(args):
        username = args["username"]
        # ...


    @use_kwargs(UserSchema())
    def profile_update(username, password, first_name, last_name):
        update_profile(username, password, first_name, last_name)
        # ...


    # You can add additional parameters
    @use_kwargs({"posts_per_page": fields.Int(missing=10)}, location="query")
    @use_args(UserSchema())
    def profile_posts(args, posts_per_page):
        username = args["username"]
        # ...

.. _advanced_setting_unknown:

Setting `unknown`
-----------------

webargs supports several ways of setting and passing the `unknown` parameter
for `handling unknown fields <https://marshmallow.readthedocs.io/en/stable/quickstart.html#handling-unknown-fields>`_.

You can pass `unknown=...` as a parameter to any of
`Parser.parse <webargs.core.Parser.parse>`,
`Parser.use_args <webargs.core.Parser.use_args>`, and
`Parser.use_kwargs <webargs.core.Parser.use_kwargs>`.


.. note::

    The `unknown` value is passed to the schema's `load()` call. It therefore
    only applies to the top layer when nesting is used. To control `unknown` at
    multiple layers of a nested schema, you must use other mechanisms, like
    the `unknown` argument to `fields.Nested`.

Default `unknown`
+++++++++++++++++

By default, webargs will pass `unknown=marshmallow.EXCLUDE` except when the
location is `json`, `form`, `json_or_form`, or `path`. In those cases, it uses
`unknown=marshmallow.RAISE` instead.

You can change these defaults by overriding `DEFAULT_UNKNOWN_BY_LOCATION`.
This is a mapping of locations to values to pass.

For example,

.. code-block:: python

    from flask import Flask
    from marshmallow import EXCLUDE, fields
    from webargs.flaskparser import FlaskParser

    app = Flask(__name__)


    class Parser(FlaskParser):
        DEFAULT_UNKNOWN_BY_LOCATION = {"query": EXCLUDE}


    parser = Parser()


    # location is "query", which is listed in DEFAULT_UNKNOWN_BY_LOCATION,
    # so EXCLUDE will be used
    @app.route("/", methods=["GET"])
    @parser.use_args({"foo": fields.Int()}, location="query")
    def get(args):
        return f"foo x 2 = {args['foo'] * 2}"


    # location is "json", which is not in DEFAULT_UNKNOWN_BY_LOCATION,
    # so no value will be passed for `unknown`
    @app.route("/", methods=["POST"])
    @parser.use_args({"foo": fields.Int(), "bar": fields.Int()}, location="json")
    def post(args):
        return f"foo x bar = {args['foo'] * args['bar']}"


You can also define a default at parser instantiation, which will take
precedence over these defaults, as in

.. code-block:: python

    from marshmallow import INCLUDE

    parser = Parser(unknown=INCLUDE)

    # because `unknown` is set on the parser, `DEFAULT_UNKNOWN_BY_LOCATION` has
    # effect and `INCLUDE` will always be used
    @app.route("/", methods=["POST"])
    @parser.use_args({"foo": fields.Int(), "bar": fields.Int()}, location="json")
    def post(args):
        unexpected_args = [k for k in args.keys() if k not in ("foo", "bar")]
        return f"foo x bar = {args['foo'] * args['bar']}; unexpected args={unexpected_args}"

Using Schema-Specfied `unknown`
+++++++++++++++++++++++++++++++

If you wish to use the value of `unknown` specified by a schema, simply pass
``unknown=None``. This will disable webargs' automatic passing of values for
``unknown``. For example,

.. code-block:: python

    from flask import Flask
    from marshmallow import Schema, fields, EXCLUDE, missing
    from webargs.flaskparser import use_args


    class RectangleSchema(Schema):
        length = fields.Float()
        width = fields.Float()

        class Meta:
            unknown = EXCLUDE


    app = Flask(__name__)

    # because unknown=None was passed, no value is passed during schema loading
    # as a result, the schema's behavior (EXCLUDE) is used
    @app.route("/", methods=["POST"])
    @use_args(RectangleSchema(), location="json", unknown=None)
    def get(args):
        return f"area = {args['length'] * args['width']}"


You can also set ``unknown=None`` when instantiating a parser to make this
behavior the default for a parser.


When to avoid `use_kwargs`
--------------------------

Any  `Schema <marshmallow.Schema>` passed to `use_kwargs <webargs.core.Parser.use_kwargs>` MUST deserialize to a dictionary of data.
If your schema has a `post_load <marshmallow.decorators.post_load>` method 
that returns a non-dictionary,
you should use `use_args <webargs.core.Parser.use_args>` instead.

.. code-block:: python

    from marshmallow import Schema, fields, post_load
    from webargs.flaskparser import use_args


    class Rectangle:
        def __init__(self, length, width):
            self.length = length
            self.width = width


    class RectangleSchema(Schema):
        length = fields.Float()
        width = fields.Float()

        @post_load
        def make_object(self, data, **kwargs):
            return Rectangle(**data)


    @use_args(RectangleSchema)
    def post(rect: Rectangle):
        return f"Area: {rect.length * rect.width}"

Packages such as  `marshmallow-sqlalchemy <https://github.com/marshmallow-code/marshmallow-sqlalchemy>`_ and `marshmallow-dataclass <https://github.com/lovasoa/marshmallow_dataclass>`_ generate schemas that deserialize to non-dictionary objects.
Therefore, `use_args <webargs.core.Parser.use_args>` should be used with those schemas.


Schema Factories
----------------

If you need to parametrize a schema based on a given request, you can use a "Schema factory": a callable that receives the current `request` and returns a `marshmallow.Schema` instance.

Consider the following use cases:

- Filtering via a query parameter by passing ``only`` to the Schema.
- Handle partial updates for PATCH requests using marshmallow's `partial loading <https://marshmallow.readthedocs.io/en/latest/quickstart.html#partial-loading>`_ API.

.. code-block:: python

    from flask import Flask
    from marshmallow import Schema, fields
    from webargs.flaskparser import use_args

    app = Flask(__name__)


    class UserSchema(Schema):
        id = fields.Int(dump_only=True)
        username = fields.Str(required=True)
        password = fields.Str(load_only=True)
        first_name = fields.Str(missing="")
        last_name = fields.Str(missing="")
        date_registered = fields.DateTime(dump_only=True)


    def make_user_schema(request):
        # Filter based on 'fields' query parameter
        fields = request.args.get("fields", None)
        only = fields.split(",") if fields else None
        # Respect partial updates for PATCH requests
        partial = request.method == "PATCH"
        # Add current request to the schema's context
        return UserSchema(only=only, partial=partial, context={"request": request})


    # Pass the factory to .parse, .use_args, or .use_kwargs
    @app.route("/profile/", methods=["GET", "POST", "PATCH"])
    @use_args(make_user_schema)
    def profile_view(args):
        username = args.get("username")
        # ...



Reducing Boilerplate
++++++++++++++++++++

We can reduce boilerplate and improve [re]usability with a simple helper function:

.. code-block:: python

    from webargs.flaskparser import use_args


    def use_args_with(schema_cls, schema_kwargs=None, **kwargs):
        schema_kwargs = schema_kwargs or {}

        def factory(request):
            # Filter based on 'fields' query parameter
            only = request.args.get("fields", None)
            # Respect partial updates for PATCH requests
            partial = request.method == "PATCH"
            return schema_cls(
                only=only, partial=partial, context={"request": request}, **schema_kwargs
            )

        return use_args(factory, **kwargs)


Now we can attach input schemas to our view functions like so:

.. code-block:: python

    @use_args_with(UserSchema)
    def profile_view(args):
        # ...
        get_profile(**args)


Custom Fields
-------------

See the "Custom Fields" section of the marshmallow docs for a detailed guide on defining custom fields which you can pass to webargs parsers: https://marshmallow.readthedocs.io/en/latest/custom_fields.html.

Using ``Method`` and ``Function`` Fields with webargs
+++++++++++++++++++++++++++++++++++++++++++++++++++++

Using the :class:`Method <marshmallow.fields.Method>` and :class:`Function <marshmallow.fields.Function>` fields requires that you pass the ``deserialize`` parameter.


.. code-block:: python

    @use_args({"cube": fields.Function(deserialize=lambda x: int(x) ** 3)})
    def math_view(args):
        cube = args["cube"]
        # ...

.. _custom-loaders:

Custom Parsers
--------------

To add your own parser, extend :class:`Parser <webargs.core.Parser>` and implement the `load_*` method(s) you need to override. For example, here is a custom Flask parser that handles nested query string arguments.


.. code-block:: python

    import re

    from webargs import core
    from webargs.flaskparser import FlaskParser


    class NestedQueryFlaskParser(FlaskParser):
        """Parses nested query args

        This parser handles nested query args. It expects nested levels
        delimited by a period and then deserializes the query args into a
        nested dict.

        For example, the URL query params `?name.first=John&name.last=Boone`
        will yield the following dict:

            {
                'name': {
                    'first': 'John',
                    'last': 'Boone',
                }
            }
        """

        def load_querystring(self, req, schema):
            return _structure_dict(req.args)


    def _structure_dict(dict_):
        def structure_dict_pair(r, key, value):
            m = re.match(r"(\w+)\.(.*)", key)
            if m:
                if r.get(m.group(1)) is None:
                    r[m.group(1)] = {}
                structure_dict_pair(r[m.group(1)], m.group(2), value)
            else:
                r[key] = value

        r = {}
        for k, v in dict_.items():
            structure_dict_pair(r, k, v)
        return r

Returning HTTP 400 Responses
----------------------------

If you'd prefer validation errors to return status code ``400`` instead
of ``422``, you can override ``DEFAULT_VALIDATION_STATUS`` on a :class:`Parser <webargs.core.Parser>`.

Sublcass the parser for your framework to do so. For example, using Falcon:

.. code-block:: python

    from webargs.falconparser import FalconParser


    class Parser(FalconParser):
        DEFAULT_VALIDATION_STATUS = 400


    parser = Parser()
    use_args = parser.use_args
    use_kwargs = parser.use_kwargs

Bulk-type Arguments
-------------------

In order to parse a JSON array of objects, pass ``many=True`` to your input ``Schema`` .

For example, you might implement JSON PATCH according to `RFC 6902 <https://tools.ietf.org/html/rfc6902>`_ like so:


.. code-block:: python

    from webargs import fields
    from webargs.flaskparser import use_args
    from marshmallow import Schema, validate


    class PatchSchema(Schema):
        op = fields.Str(
            required=True,
            validate=validate.OneOf(["add", "remove", "replace", "move", "copy"]),
        )
        path = fields.Str(required=True)
        value = fields.Str(required=True)


    @app.route("/profile/", methods=["patch"])
    @use_args(PatchSchema(many=True))
    def patch_blog(args):
        """Implements JSON Patch for the user profile

        Example JSON body:

        [
            {"op": "replace", "path": "/email", "value": "mynewemail@test.org"}
        ]
        """
        # ...

Mixing Locations
----------------

Arguments for different locations can be specified by passing ``location`` to each `use_args <webargs.core.Parser.use_args>` call:

.. code-block:: python

    # "json" is the default, used explicitly below
    @app.route("/stacked", methods=["POST"])
    @use_args({"page": fields.Int(), "q": fields.Str()}, location="query")
    @use_args({"name": fields.Str()}, location="json")
    def viewfunc(query_parsed, json_parsed):
        page = query_parsed["page"]
        name = json_parsed["name"]
        # ...

To reduce boilerplate, you could create shortcuts, like so:

.. code-block:: python

    import functools

    query = functools.partial(use_args, location="query")
    body = functools.partial(use_args, location="json")


    @query({"page": fields.Int(), "q": fields.Int()})
    @body({"name": fields.Str()})
    def viewfunc(query_parsed, json_parsed):
        page = query_parsed["page"]
        name = json_parsed["name"]
        # ...

Next Steps
----------

- See the :doc:`Framework Support <framework_support>` page for framework-specific guides.
- For example applications, check out the `examples <https://github.com/marshmallow-code/webargs/tree/dev/examples>`_ directory.
