Quickstart
==========

Basic Usage
-----------

Arguments are specified as a dictionary of name -> :class:`Field <marshmallow.fields.Field>` pairs.

.. code-block:: python

    from webargs import fields, validate

    user_args = {
        # Required arguments
        "username": fields.Str(required=True),
        # Validation
        "password": fields.Str(validate=lambda p: len(p) >= 6),
        # OR use marshmallow's built-in validators
        "password": fields.Str(validate=validate.Length(min=6)),
        # Default value when argument is missing
        "display_per_page": fields.Int(load_default=10),
        # Repeated parameter, e.g. "/?nickname=Fred&nickname=Freddie"
        "nickname": fields.List(fields.Str()),
        # Delimited list, e.g. "/?languages=python,javascript"
        "languages": fields.DelimitedList(fields.Str()),
        # When value is keyed on a variable-unsafe name
        # or you want to rename a key
        "user_type": fields.Str(data_key="user-type"),
    }

.. note::

    See the `marshmallow.fields` documentation for a full reference on available field types.

To parse request arguments, use the :meth:`parse <webargs.core.Parser.parse>` method of a :class:`Parser <webargs.core.Parser>` object.

.. code-block:: python

    from flask import request
    from webargs.flaskparser import parser


    @app.route("/register", methods=["POST"])
    def register():
        args = parser.parse(user_args, request)
        return register_user(
            args["username"],
            args["password"],
            fullname=args["fullname"],
            per_page=args["display_per_page"],
        )


Decorator API
-------------

As an alternative to `Parser.parse`, you can decorate your view with :meth:`use_args <webargs.core.Parser.use_args>` or :meth:`use_kwargs <webargs.core.Parser.use_kwargs>`. The parsed arguments dictionary will be injected as a parameter of your view function or as keyword arguments, respectively.

.. code-block:: python

    from webargs.flaskparser import use_args, use_kwargs


    @app.route("/register", methods=["POST"])
    @use_args(user_args)  # Injects args dictionary
    def register(args):
        return register_user(
            args["username"],
            args["password"],
            fullname=args["fullname"],
            per_page=args["display_per_page"],
        )


    @app.route("/settings", methods=["POST"])
    @use_kwargs(user_args)  # Injects keyword arguments
    def user_settings(username, password, fullname, display_per_page, nickname):
        return render_template("settings.html", username=username, nickname=nickname)


.. note::

    When using `use_kwargs`, any missing values will be omitted from the arguments.
    Use ``**kwargs`` to handle optional arguments.

    .. code-block:: python

        from webargs import fields, missing


        @use_kwargs({"name": fields.Str(required=True), "nickname": fields.Str(required=False)})
        def myview(name, **kwargs):
            if "nickname" not in kwargs:
                # ...
                pass

Request "Locations"
-------------------

By default, webargs will search for arguments from the request body as JSON. You can specify a different location from which to load data like so:

.. code-block:: python

    @app.route("/register")
    @use_args(user_args, location="form")
    def register(args):
        return "registration page"

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

    args = {"age": fields.Int(validate=lambda val: val > 0)}

The validator may return either a `boolean` or raise a :exc:`ValidationError <webargs.core.ValidationError>`.

.. code-block:: python

    from webargs import fields, ValidationError


    def must_exist_in_db(val):
        if not User.query.get(val):
            # Optionally pass a status_code
            raise ValidationError("User does not exist")


    args = {"id": fields.Int(validate=must_exist_in_db)}

.. note::

    If a validator returns ``None``, validation will pass. A validator must return ``False`` or raise a `ValidationError <webargs.core.ValidationError>`
    for validation to fail.


There are a number of built-in validators from `marshmallow.validate <marshmallow.validate>`
(re-exported as `webargs.validate`).

.. code-block:: python

    from webargs import fields, validate

    args = {
        "name": fields.Str(required=True, validate=[validate.Length(min=1, max=9999)]),
        "age": fields.Int(validate=[validate.Range(min=1, max=999)]),
    }

The full arguments dictionary can also be validated by passing ``validate`` to :meth:`Parser.parse <webargs.core.Parser.parse>`, :meth:`Parser.use_args <webargs.core.Parser.use_args>`, :meth:`Parser.use_kwargs <webargs.core.Parser.use_kwargs>`.


.. code-block:: python

    from webargs import fields
    from webargs.flaskparser import parser

    argmap = {"age": fields.Int(), "years_employed": fields.Int()}

    # ...
    result = parser.parse(
        argmap, validate=lambda args: args["years_employed"] < args["age"]
    )


Error Handling
--------------

Each parser has a default error handling method. To override the error handling callback, write a function that
receives an error, the request, the `marshmallow.Schema` instance, status code, and headers.
Then decorate that function with :func:`Parser.error_handler <webargs.core.Parser.error_handler>`.

.. code-block:: python

    from webargs.flaskparser import parser


    class CustomError(Exception):
        pass


    @parser.error_handler
    def handle_error(error, req, schema, *, error_status_code, error_headers):
        raise CustomError(error.messages)

Parsing Lists in Query Strings
------------------------------

Use `fields.DelimitedList <webargs.fields.DelimitedList>` to parse comma-separated
lists in query parameters, e.g. ``/?permissions=read,write``

.. code-block:: python

    from webargs import fields

    args = {"permissions": fields.DelimitedList(fields.Str())}

If you expect repeated query parameters, e.g. ``/?repo=webargs&repo=marshmallow``, use
`fields.List <marshmallow.fields.List>` instead.

.. code-block:: python

    from webargs import fields

    args = {"repo": fields.List(fields.Str())}

Nesting Fields
--------------

:class:`Field <marshmallow.fields.Field>` dictionaries can be nested within each other. This can be useful for validating nested data.

.. code-block:: python

    from webargs import fields

    args = {
        "name": fields.Nested(
            {"first": fields.Str(required=True), "last": fields.Str(required=True)}
        )
    }

.. note::

    Of the default supported locations in webargs, only the ``json`` request location supports nested datastructures. You can, however, :ref:`implement your own data loader <custom-loaders>` to add nested field functionality to the other locations.

Next Steps
----------

- Go on to :doc:`Advanced Usage <advanced>` to learn how to add custom location handlers, use marshmallow Schemas, and more.
- See the :doc:`Framework Support <framework_support>` page for framework-specific guides.
- For example applications, check out the `examples <https://github.com/marshmallow-code/webargs/tree/dev/examples>`_ directory.
