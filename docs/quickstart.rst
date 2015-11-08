.. _quickstart:

Quickstart
==========

Basic Usage
-----------

Arguments are specified as a dictionary of name -> :class:`Field <marshmallow.fields.Field>` pairs.

.. code-block:: python

    from webargs import fields, validate

    user_args = {

        # Required arguments
        'username': fields.Str(required=True),

        # Validation
        'password': fields.Str(validate=lambda p: len(p) >= 6),

        # OR use marshmallow's built-in validators
        'password': fields.Str(validate=validate.Length(min=6)),

        # Default value when argument is missing
        'display_per_page': fields.Int(missing=10),

        # Repeated parameter, e.g. "/?nickname=Fred&nickname=Freddie"
        'nickname': fields.List(fields.Str()),

        # When you know where an argument should be parsed from
        'active': fields.Bool(location='query')

        # When value is keyed on a variable-unsafe name
        # or you want to rename a key
        'content_type': fields.Str(load_from='Content-Type',
                                   location='headers')
    }

.. note::

    See the `marshmallow.fields` documentation for a full reference on available field types.

To parse request arguments, use the :meth:`parse <webargs.core.Parser.parse>` method of a :class:`Parser <webargs.core.Parser>` object.

.. code-block:: python

    from flask import request
    from webargs.flaskparser import parser

    @app.route('/register', methods=['POST'])
    def register():
        args = parser.parse(user_args, request)
        return register_user(args['username'], args['password'],
            fullname=args['fullname'], per_page=args['display_per_page'])


Decorator API
-------------

As an alternative to `Parser.parse`, you can decorate your view with :meth:`use_args <webargs.core.Parser.use_args>` or :meth:`use_kwargs <webargs.core.Parser.use_kwargs>`. The parsed arguments dictionary will be injected as a parameter of your view function or as keyword arguments, respectively.

.. code-block:: python

    from webargs.flaskparser import use_args, use_kwargs

    @app.route('/register', methods=['POST'])
    @use_args(user_args)  # Injects args dictionary
    def register(args):
        return register_user(args['username'], args['password'],
            fullname=args['fullname'], per_page=args['display_per_page'])

    @app.route('/settings', methods=['POST'])
    @use_kwargs(user_args)  # Injects keyword arguments
    def user_settings(username, password, fullname, display_per_page, nickname):
        return render_template('settings.html', username=username, nickname=nickname)


.. note::

    When using `use_kwargs`, any missing values for non-required fields will take the special value `missing <marshmallow.missing>`.

    .. code-block:: python

        from webargs import fields, missing

        @use_kwargs({'name': fields.Str(), 'nickname': fields.Str(required=False)})
        def myview(name, nickname):
            if nickname is missing:
                # ...

Request "Locations"
-------------------

By default, webargs will search for arguments from the URL query string (e.g. ``"/?name=foo"``), form data, and JSON data (in that order). You can explicitly specify which locations to search, like so:

.. code-block:: python

    @app.route('/register')
    @use_args(user_args, locations=('json', 'form'))
    def register(args):
        return 'registration page'

Available locations include:

- ``'querystring'`` (same as ``'query'``)
- ``'json'``
- ``'form'``
- ``'headers'``
- ``'cookies'``
- ``'files'``

Validation
----------

Each :class:`Field <marshmallow.fields.Field>` object can be validated individually by passing the ``validate`` argument.

.. code-block:: python

    from webargs import fields

    args = {
        'age': fields.Int(validate=lambda val: val > 0)
    }

The validator may return either a `boolean` or raise a :exc:`ValidationError <webargs.core.ValidationError>`.

.. code-block:: python

    from webargs import fields, ValidationError

    def must_exist_in_db(val):
        if not User.query.get(val):
            # Optionally pass a status_code
            raise ValidationError('User does not exist')

    args = {
        'id': fields.Int(validate=must_exist_in_db)
    }

.. note::

    You may also pass a list of validators to the ``validate`` parameter.

The full arguments dictionary can also be validated by passing ``validate`` to :meth:`Parser.parse <webargs.core.Parser.parse>`, :meth:`Parser.use_args <webargs.core.Parser.use_args>`, :meth:`Parser.use_kwargs <webargs.core.Parser.use_kwargs>`.


.. code-block:: python

    from webargs import fields
    from webargs.flaskparser import parser

    args = {
        'age': fields.Int(),
        'years_employed': fields.Int(),
    }

    # ...
    result = parser.parse(args,
                          validate=lambda args: args['years_employed'] < args['age'])


Custom Error Handlers
---------------------

Each parser has a default error handling method. To override the error handling callback, write a function that receives an error and handles it, then decorate that function with :func:`Parser.error_handler <webargs.core.Parser.error_handler>`.

.. code-block:: python

    from webargs import core
    parser = core.Parser()

    class CustomError(Exception):
        pass

    @parser.error_handler
    def handle_error(error):
        raise CustomError(error.messages)

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

.. _quickstart-custom-parsers:

Custom Parsers
--------------

To add your own parser, extend :class:`Parser <webargs.core.Parser>` and implement the `parse_*` method(s) you need to override. For example, here is a custom Flask parser that handles nested query string arguments.


.. code-block:: python

    import re

    from webargs import core
    from webargs.flaskparser import FlaskParser

    class NestedQueryFlaskParser(FlaskParser):
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

Nesting Fields
--------------

:class:`Field <marshmallow.fields.Field>` dictionaries can be nested within each other. This can be useful for validating nested data.

.. code-block:: python

    from webargs import fields

    args = {
        'name': fields.Nested({
            'first': fields.Str(required=True),
            'last': fields.Str(required=True),
        })
    }

.. note::

    By default, webargs only parses nested fields using the ``json`` request location. You can, however, :ref:`implement your own parser <quickstart-custom-parsers>` to add nested field functionality to the other locations.

Advanced: Marshmallow Integration
---------------------------------

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


Advanced: Schema Factories
--------------------------

If you need to parametrize a schema based on a given request, you can use a "Schema factory": a callable that receives the current `request` and returns a `marshmallow.Schema` instance.

Consider the following use cases:

- Handle partial updates for PATCH requests using marshmallow's `partial loading <https://marshmallow.readthedocs.org/en/latest/quickstart.html#partial-loading>`_ API.
- Filtering via a query parameter by passing ``only`` to the Schema.

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


Next Steps
----------

- See the :ref:`Framework Support <frameworks>` page for framework-specific guides.
- For example applications, check out the `examples <https://github.com/sloria/webargs/tree/dev/examples>`_ directory.
