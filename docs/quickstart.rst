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


Error Handling
--------------

Each parser has a default error handling method. To override the error handling callback, write a function that receives an error and handles it, then decorate that function with :func:`Parser.error_handler <webargs.core.Parser.error_handler>`.

.. code-block:: python

    from webargs import core
    parser = core.Parser()

    class CustomError(Exception):
        pass

    @parser.error_handler
    def handle_error(error):
        raise CustomError(error.messages)

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

    By default, webargs only parses nested fields using the ``json`` request location. You can, however, :ref:`implement your own parser <custom-parsers>` to add nested field functionality to the other locations.

Next Steps
----------

- Go on to :ref:`Advanced Usage <advanced>` to learn how to add custom location handlers, use marshmallow Schemas, and more.
- See the :ref:`Framework Support <frameworks>` page for framework-specific guides.
- For example applications, check out the `examples <https://github.com/sloria/webargs/tree/dev/examples>`_ directory.
