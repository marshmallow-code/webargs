.. _advanced:

Advanced Usage
==============

This section includes guides for advanced usage patterns.

Custom Location Handlers
------------------------

To add your own custom location handler, write a function that receives a request, an argument name, and a :class:`Field <marshmallow.fields.Field>`, then decorate that function with :func:`Parser.location_handler <webargs.core.Parser.location_handler>`.


.. code-block:: python

    from webargs import fields
    from webargs.flaskparser import parser

    @parser.location_handler('data')
    def parse_data(request, name, field):
        return request.data.get(name)

    # Now 'data' can be specified as a location
    @parser.use_args({'per_page': fields.Int()}, locations=('data', ))
    def posts(args):
        return 'displaying {} posts'.format(args['per_page'])


Marshmallow Integration
-----------------------

When you need more flexibility in defining input schemas, you can pass a marshmallow `Schema <marshmallow.Schema>` instead of a dictionary to `Parser.parse <webargs.core.Parser.parse>`, `Parser.use_args <webargs.core.Parser.use_args>`, and `Parser.use_kwargs <webargs.core.Parser.use_kwargs>`.


.. code-block:: python

    from marshmallow import Schema, fields
    from webargs.flaskparser import use_args

    class UserSchema(Schema):
        id = fields.Int(dump_only=True)  # read-only (won't be parsed by webargs)
        username = fields.Str(required=True)
        password = fields.Str(load_only=True)  # write-only
        first_name = fields.Str(missing='')
        last_name = fields.Str(missing='')
        date_registered = fields.DateTime(dump_only=True)

        class Meta:
            strict = True


    @use_args(UserSchema())
    def profile_view(args):
        # ...

    @use_kwargs(UserSchema())
    def profile_update(username, password, first_name, last_name):
        # ...

    # You can add additional paramters
    @use_kwargs({'posts_per_page': fields.Int(missing=10, location='query')})
    @use_args(UserSchema())
    def profile_posts(args, posts_per_page):
        # ...

.. note::
    You should always set ``strict=True`` (either as a ``class Meta`` option or in the Schema's constructor) when passing a schema to webargs. This will ensure that the parser's error handler is invoked when expected.


Schema Factories
----------------

If you need to parametrize a schema based on a given request, you can use a "Schema factory": a callable that receives the current `request` and returns a `marshmallow.Schema` instance.

Consider the following use cases:

- Filtering via a query parameter by passing ``only`` to the Schema.
- Handle partial updates for PATCH requests using marshmallow's `partial loading <https://marshmallow.readthedocs.org/en/latest/quickstart.html#partial-loading>`_ API.

.. code-block:: python

    from marshmallow import Schema, fields
    from webargs.flaskparser import use_args

    class UserSchema(Schema):
        id = fields.Int(dump_only=True)
        username = fields.Str(required=True)
        password = fields.Str(load_only=True)
        first_name = fields.Str(missing='')
        last_name = fields.Str(missing='')
        date_registered = fields.DateTime(dump_only=True)

        class Meta:
            strict = True

    def make_user_schema(request):
        # Filter based on 'fields' query parameter
        only = request.args.get('fields', None)
        # Respect partial updates for PATCH requests
        partial = request.method == 'PUT'
        # Add current request to the schema's context
        return UserSchema(only=only, partial=partial, context={'request': request})

    # Pass the factory to .parse, .use_args, or .use_kwargs
    @use_args(make_user_schema):
    def profile_view(args):
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
            only = request.args.get('fields', None)
            # Respect partial updates for PATCH requests
            partial = request.method == 'PUT'
            # Add current request to the schema's context
            # and ensure we're always using strict mode
            return schema_cls(
                only=only, partial=partial, strict=True,
                context={'request': request}, **schema_kwargs
            )
        return use_args(factory, **kwargs)


Now we can attach input schemas to our view functions like so:

.. code-block:: python

    @use_args_with(UserSchema)
    def profile_view(args):
        # ...


.. _custom-parsers:

Custom Parsers
--------------

To add your own parser, extend :class:`Parser <webargs.core.Parser>` and implement the `parse_*` method(s) you need to override. For example, here is a custom Flask parser that handles nested query string arguments.


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

        def parse_querystring(self, req, name, field):
            return core.get_value(_structure_dict(req.args), name, field)


    def _structure_dict(dict_):
        def structure_dict_pair(r, key, value):
            m = re.match(r'(\w+)\.(.*)', key)
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

Next Steps
----------

- See the :ref:`Framework Support <frameworks>` page for framework-specific guides.
- For example applications, check out the `examples <https://github.com/sloria/webargs/tree/dev/examples>`_ directory.
