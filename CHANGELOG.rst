Changelog
---------

8.1.0 (2022-01-12)
******************

Bug fixes:

* Fix publishing type hints per `PEP-561 <https://www.python.org/dev/peps/pep-0561/>`_.
  (:pr:`650`).
* Add DelimitedTuple to fields.__all__ (:pr:`678`).
* Narrow type of ``argmap`` from ``Mapping`` to ``Dict`` (:pr:`682`).

Other changes:

* Test against Python 3.10 (:pr:`647`).
* Drop support for Python 3.6 (:pr:`673`).
* Address distutils deprecation warning in Python 3.10 (:pr:`652`).
  Thanks :user:`kkirsche` for the PR.
* Use postponed evaluation of annotations (:pr:`663`).
  Thanks :user:`Isira-Seneviratne` for the PR.
* Pin mypy version in tox (:pr:`674`).
* Improve type annotations for ``__version_info__`` (:pr:`680`).

8.0.1 (2021-08-12)
******************

Bug fixes:

* Fix "``DelimitedList`` deserializes empty string as ``['']``" (:issue:`623`).
  Thanks :user:`TTWSchell` for reporting and for the PR.

Other changes:

* New documentation theme with `furo`. Thanks to :user:`pradyunsg` for writing
  furo!
* Webargs has a new logo. Thanks to :user:`michaelizergit`! (:issue:`312`)
* Don't build universal wheels. We don't support Python 2 anymore.
  (:pr:`632`)
* Make the build reproducible (:pr:`631`).


8.0.0 (2021-04-08)
******************

Features:

* Add `Parser.pre_load` as a method for allowing users to modify data before
  schema loading, but without redefining location loaders. See advanced docs on
  `Parser pre_load` for usage information. (:pr:`583`)

* *Backwards-incompatible*: ``unknown`` defaults to `None` for body locations
  (`json`, `form` and `json_or_form`) (:issue:`580`).

* Detection of fields as "multi-value" for unpacking lists from multi-dict
  types is now extensible with the ``is_multiple`` attribute. If a field sets
  ``is_multiple = True`` it will be detected as a multi-value field. If
  ``is_multiple`` is not set or is set to ``None``, webargs will check if the
  field is an instance of ``List`` or ``Tuple``. (:issue:`563`)

* A new attribute on ``Parser`` objects, ``Parser.KNOWN_MULTI_FIELDS`` can be
  used to set fields which should be detected as ``is_multiple=True`` even when
  the attribute is not set (:pr:`592`).

See docs on "Multi-Field Detection" for more details.

Bug fixes:

* ``Tuple`` field now behaves as a "multiple" field (:pr:`585`).

7.0.1 (2020-12-14)
******************

Bug fixes:

* Fix `DelimitedList` and `DelimitedTuple` to pass additional keyword arguments
  through their `_serialize` methods to the child fields and fix type checking
  on these classes. (:issue:`569`)
  Thanks to :user:`decaz` for reporting.

7.0.0 (2020-12-10)
******************

Changes:

* *Backwards-incompatible*: Drop support for webapp2 (:pr:`565`).

* Add type annotations to `Parser` class, `DelimitedList`, and
  `DelimitedTuple`. (:issue:`566`)

7.0.0b2 (2020-12-01)
********************

Features:

* `DjangoParser` now supports the `headers` location. (:issue:`540`)

* `FalconParser` now supports a new `media` location, which uses
  Falcon's `media` decoding. (:issue:`253`)

`media` behaves very similarly to the `json` location but also supports any
registered media handler. See the
`Falcon documentation on media types
<https://falcon.readthedocs.io/en/stable/api/media.html>`_ for more details.

Changes:

* `FalconParser` defaults to the `media` location instead of `json`. (:issue:`253`)
* Test against Python 3.9 (:pr:`552`).
* *Backwards-incompatible*: Drop support for Python 3.5 (:pr:`553`).

7.0.0b1 (2020-09-11)
********************

Refactoring:

* *Backwards-incompatible*: Remove support for marshmallow2 (:issue:`539`)

* *Backwards-incompatible*: Remove `dict2schema`

  Users desiring the `dict2schema` functionality may now rely upon
  `marshmallow.Schema.from_dict`. Rewrite any code using `dict2schema` like so:

.. code-block:: python

    import marshmallow as ma

    # webargs 6.x and older
    from webargs import dict2schema

    myschema = dict2schema({"q1", ma.fields.Int()})

    # webargs 7.x
    myschema = ma.Schema.from_dict({"q1", ma.fields.Int()})

Features:

* Add ``unknown`` as a parameter to ``Parser.parse``, ``Parser.use_args``,
  ``Parser.use_kwargs``, and parser instantiation. When set, it will be passed
  to ``Schema.load``. When not set, the value passed will depend on the parser's
  settings. If set to ``None``, the schema's default behavior will be used (i.e.
  no value is passed to ``Schema.load``) and parser settings will be ignored.

This allows usages like

.. code-block:: python

    import marshmallow as ma


    @parser.use_kwargs(
        {"q1": ma.fields.Int(), "q2": ma.fields.Int()}, location="query", unknown=ma.EXCLUDE
    )
    def foo(q1, q2):
        ...

* Defaults for ``unknown`` may be customized on parser classes via
  ``Parser.DEFAULT_UNKNOWN_BY_LOCATION``, which maps location names to values
  to use.

Usages are varied, but include

.. code-block:: python

    import marshmallow as ma
    from webargs.flaskparser import FlaskParser

    # as well as...
    class MyParser(FlaskParser):
        DEFAULT_UNKNOWN_BY_LOCATION = {"query": ma.INCLUDE}


    parser = MyParser()

Setting the ``unknown`` value for a Parser instance has higher precedence. So

.. code-block:: python

    parser = MyParser(unknown=ma.RAISE)

will always pass ``RAISE``, even when the location is ``query``.

* By default, webargs will pass ``unknown=EXCLUDE`` for all locations except
  for request bodies (``json``, ``form``, and ``json_or_form``) and path
  parameters. Request bodies and path parameters will pass ``unknown=RAISE``.
  This behavior is defined by the default value for
  ``DEFAULT_UNKNOWN_BY_LOCATION``.

Changes:

* Registered `error_handler` callbacks are required to raise an exception.
  If a handler is invoked and no exception is raised, `webargs` will raise
  a `ValueError` (:issue:`527`)

6.1.1 (2020-09-08)
******************

Bug fixes:

* Failure to validate flask headers would produce error data which contained
  tuples as keys, and was therefore not JSON-serializable. (:issue:`500`)
  These errors will now extract the headername as the key correctly.
  Thanks to :user:`shughes-uk` for reporting.

6.1.0 (2020-04-05)
******************

Features:

* Add ``fields.DelimitedTuple`` when using marshmallow 3. This behaves as a
  combination of ``fields.DelimitedList`` and ``marshmallow.fields.Tuple``. It
  takes an iterable of fields, plus a delimiter (defaults to ``,``), and parses
  delimiter-separated strings into tuples. (:pr:`509`)

* Add ``__str__`` and ``__repr__`` to MultiDictProxy to make it easier to work
  with (:pr:`488`)

Support:

* Various docs updates (:pr:`482`, :pr:`486`, :pr:`489`, :pr:`498`, :pr:`508`).
  Thanks :user:`lefterisjp`, :user:`timgates42`, and :user:`ugultopu` for the PRs.


6.0.0 (2020-02-27)
******************

Features:

* ``FalconParser``: Pass request content length to ``req.stream.read`` to
  provide compatibility with ``falcon.testing`` (:pr:`477`).
  Thanks :user:`suola` for the PR.

* *Backwards-incompatible*: Factorize the ``use_args`` / ``use_kwargs`` branch
  in all parsers. When ``as_kwargs`` is ``False``, arguments are now
  consistently appended to the arguments list by the ``use_args`` decorator.
  Before this change, the ``PyramidParser`` would prepend the argument list on
  each call to ``use_args``. Pyramid view functions must reverse the order of
  their arguments. (:pr:`478`)

6.0.0b8 (2020-02-16)
********************

Refactoring:

* *Backwards-incompatible*: Use keyword-only arguments (:pr:`472`).

6.0.0b7 (2020-02-14)
********************

Features:

* *Backwards-incompatible*: webargs will rewrite the error messages in
  ValidationErrors to be namespaced under the location which raised the error.
  The `messages` field on errors will therefore be one layer deeper with a
  single top-level key.

6.0.0b6 (2020-01-31)
********************

Refactoring:

* Remove the cache attached to webargs parsers. Due to changes between webargs
  v5 and v6, the cache is no longer considered useful.

Other changes:

* Import ``Mapping`` from ``collections.abc`` in pyramidparser.py (:pr:`471`).
  Thanks :user:`tirkarthi` for the PR.

6.0.0b5 (2020-01-30)
********************

Refactoring:

* *Backwards-incompatible*: `DelimitedList` now requires that its input be a
  string and always serializes as a string. It can still serialize and deserialize
  using another field, e.g. `DelimitedList(Int())` is still valid and requires
  that the values in the list parse as ints.

6.0.0b4 (2020-01-28)
********************

Bug fixes:

* :cve:`CVE-2020-7965`: Don't attempt to parse JSON if request's content type is mismatched
  (bugfix from 5.5.3).

6.0.0b3 (2020-01-21)
********************

Features:

* *Backwards-incompatible*: Support Falcon 2.0. Drop support for Falcon 1.x
  (:pr:`459`). Thanks :user:`dodumosu` and :user:`Nateyo` for the PR.

6.0.0b2 (2020-01-07)
********************

Other changes:

* *Backwards-incompatible*: Drop support for Python 2 (:issue:`440`).
  Thanks :user:`hugovk` for the PR.

6.0.0b1 (2020-01-06)
********************

Features:

* *Backwards-incompatible*: Schemas will now load all data from a location, not
  only data specified by fields. As a result, schemas with validators which
  examine the full input data may change in behavior. The `unknown` parameter
  on schemas may be used to alter this. For example,
  `unknown=marshmallow.EXCLUDE` will produce a behavior similar to webargs v5.

Bug fixes:

* *Backwards-incompatible*: All parsers now require the Content-Type to be set
  correctly when processing JSON request bodies. This impacts ``DjangoParser``,
  ``FalconParser``, ``FlaskParser``, and ``PyramidParser``

Refactoring:

* *Backwards-incompatible*: Schema fields may not specify a location any
  longer, and `Parser.use_args` and `Parser.use_kwargs` now accept `location`
  (singular) instead of `locations` (plural). Instead of using a single field or
  schema with multiple `locations`, users are recommended to make multiple
  calls to `use_args` or `use_kwargs` with a distinct schema per location. For
  example, code should be rewritten like this:

.. code-block:: python

    # webargs 5.x and older
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

* The `location_handler` decorator has been removed and replaced with
  `location_loader`. `location_loader` serves the same purpose (letting you
  write custom hooks for loading data) but its expected method signature is
  different. See the docs on `location_loader` for proper usage.

Thanks :user:`sirosen` for the PR!

5.5.3 (2020-01-28)
******************

Bug fixes:

* :cve:`CVE-2020-7965`: Don't attempt to parse JSON if request's content type is mismatched.

5.5.2 (2019-10-06)
******************

Bug fixes:

* Handle ``UnicodeDecodeError`` when parsing JSON payloads (:issue:`427`).
  Thanks :user:`lindycoder` for the catch and patch.

5.5.1 (2019-09-15)
******************

Bug fixes:

* Remove usage of deprecated ``Field.fail`` when using marshmallow 3.

5.5.0 (2019-09-07)
******************

Support:

* Various docs updates (:pr:`414`, :pr:`421`).

Refactoring:

* Don't mutate ``globals()`` in ``webargs.fields`` (:pr:`411`).
* Use marshmallow 3's ``Schema.from_dict`` if available (:pr:`415`).

5.4.0 (2019-07-23)
******************

Changes:

* Use explicit type check for `fields.DelimitedList` when deciding to
  parse value with `getlist()` (`#406 (comment) <https://github.com/marshmallow-code/webargs/issues/406#issuecomment-514446228>`_ ).

Support:

* Add "Parsing Lists in Query Strings" section to docs (:issue:`406`).

5.3.2 (2019-06-19)
******************

Bug fixes:

* marshmallow 3.0.0rc7 compatibility (:pr:`395`).

5.3.1 (2019-05-05)
******************

Bug fixes:

* marshmallow 3.0.0rc6 compatibility (:pr:`384`).

5.3.0 (2019-04-08)
******************

Features:

* Add `"path"` location to ``AIOHTTPParser``, ``FlaskParser``, and
  ``PyramidParser`` (:pr:`379`). Thanks :user:`zhenhua32` for the PR.
* Add ``webargs.__version_info__``.

5.2.0 (2019-03-16)
******************

Features:

* Make the schema class used when generating a schema from a
  dict overridable (:issue:`375`). Thanks :user:`ThiefMaster`.

5.1.3 (2019-03-11)
******************

Bug fixes:

* :cve:`CVE-2019-9710`: Fix race condition between parallel requests when the cache is used
  (:issue:`371`). Thanks :user:`ThiefMaster` for reporting and fixing.

5.1.2 (2019-02-03)
******************

Bug fixes:

* Remove lingering usages of ``ValidationError.status_code``
  (:issue:`365`). Thanks :user:`decaz` for reporting.
* Avoid ``AttributeError`` on Python<3.5.4 (:issue:`366`).
* Fix incorrect type annotations for ``error_headers``.
* Fix outdated docs (:issue:`367`). Thanks :user:`alexandersoto` for reporting.

5.1.1.post0 (2019-01-30)
************************

* Include LICENSE in sdist (:issue:`364`).

5.1.1 (2019-01-28)
******************

Bug fixes:

* Fix installing ``simplejson`` on Python 2 by
  distributing a Python 2-only wheel (:issue:`363`).

5.1.0 (2019-01-11)
******************

Features:

* Error handlers for `AsyncParser` classes may be coroutine functions.
* Add type annotations to `AsyncParser` and `AIOHTTPParser`.

Bug fixes:

* Fix compatibility with Flask<1.0 (:issue:`355`).
  Thanks :user:`hoatle` for reporting.
* Address warning on Python 3.7 about importing from ``collections.abc``.

5.0.0 (2019-01-03)
******************

Features:

* *Backwards-incompatible*: A 400 HTTPError is raised when an
  invalid JSON payload is passed.  (:issue:`329`).
  Thanks :user:`zedrdave` for reporting.

Other changes:

* *Backwards-incompatible*: `webargs.argmap2schema` is removed. Use
  `webargs.dict2schema` instead.
* *Backwards-incompatible*: `webargs.ValidationError` is removed.
  Use `marshmallow.ValidationError` instead.


.. code-block:: python

    # <5.0.0
    from webargs import ValidationError


    def auth_validator(value):
        # ...
        raise ValidationError("Authentication failed", status_code=401)


    @use_args({"auth": fields.Field(validate=auth_validator)})
    def auth_view(args):
        return jsonify(args)


    # >=5.0.0
    from marshmallow import ValidationError


    def auth_validator(value):
        # ...
        raise ValidationError("Authentication failed")


    @use_args({"auth": fields.Field(validate=auth_validator)}, error_status_code=401)
    def auth_view(args):
        return jsonify(args)


* *Backwards-incompatible*: Missing arguments will no longer be filled
  in when using ``@use_kwargs`` (:issue:`342,307,252`). Use ``**kwargs``
  to account for non-required fields.

.. code-block:: python

    # <5.0.0
    @use_kwargs(
        {"first_name": fields.Str(required=True), "last_name": fields.Str(required=False)}
    )
    def myview(first_name, last_name):
        # last_name is webargs.missing if it's missing from the request
        return {"first_name": first_name}


    # >=5.0.0
    @use_kwargs(
        {"first_name": fields.Str(required=True), "last_name": fields.Str(required=False)}
    )
    def myview(first_name, **kwargs):
        # last_name will not be in kwargs if it's missing from the request
        return {"first_name": first_name}


* `simplejson <https://pypi.org/project/simplejson/>`_ is now a required
  dependency on Python 2 (:pr:`334`).
  This ensures consistency of behavior across Python 2 and 3.

4.4.1 (2018-01-03)
******************

Bug fixes:

* Remove usages of ``argmap2schema`` from ``fields.Nested``,
  ``AsyncParser``, and ``PyramidParser``.

4.4.0 (2019-01-03)
******************

* *Deprecation*: ``argmap2schema`` is deprecated in favor of
  ``dict2schema`` (:pr:`352`).

4.3.1 (2018-12-31)
******************

* Add ``force_all`` param to ``PyramidParser.use_args``.
* Add warning about missing arguments to ``AsyncParser``.

4.3.0 (2018-12-30)
******************

* *Deprecation*: Add warning about missing arguments getting added
  to parsed arguments dictionary (:issue:`342`). This behavior will be
  removed in version 5.0.0.

4.2.0 (2018-12-27)
******************

Features:

* Add ``force_all`` argument to ``use_args`` and ``use_kwargs``
  (:issue:`252`, :issue:`307`). Thanks :user:`piroux` for reporting.
* *Deprecation*: The ``status_code`` and ``headers`` arguments to ``ValidationError``
  are deprecated. Pass ``error_status_code`` and ``error_headers`` to
  `Parser.parse`, `Parser.use_args`, and `Parser.use_kwargs` instead.
  (:issue:`327`, :issue:`336`).
* Custom error handlers receive ``error_status_code`` and ``error_headers`` arguments.
  (:issue:`327`).

.. code-block:: python

    # <4.2.0
    @parser.error_handler
    def handle_error(error, req, schema):
        raise CustomError(error.messages)


    class MyParser(FlaskParser):
        def handle_error(self, error, req, schema):
            # ...
            raise CustomError(error.messages)


    # >=4.2.0
    @parser.error_handler
    def handle_error(error, req, schema, status_code, headers):
        raise CustomError(error.messages)


    # OR


    @parser.error_handler
    def handle_error(error, **kwargs):
        raise CustomError(error.messages)


    class MyParser(FlaskParser):
        def handle_error(self, error, req, schema, status_code, headers):
            # ...
            raise CustomError(error.messages)

        # OR

        def handle_error(self, error, req, **kwargs):
            # ...
            raise CustomError(error.messages)

Legacy error handlers will be supported until version 5.0.0.

4.1.3 (2018-12-02)
******************

Bug fixes:

* Fix bug in ``AIOHTTParser`` that prevented calling
  ``use_args`` on the same view function multiple times (:issue:`273`).
  Thanks to :user:`dnp1` for reporting and :user:`jangelo` for the fix.
* Fix compatibility with marshmallow 3.0.0rc1 (:pr:`330`).

4.1.2 (2018-11-03)
******************

Bug fixes:

* Fix serialization behavior of ``DelimitedList`` (:pr:`319`).
  Thanks :user:`lee3164` for the PR.

Other changes:

* Test against Python 3.7.

4.1.1 (2018-10-25)
******************

Bug fixes:

* Fix bug in ``AIOHTTPParser`` that caused a ``JSONDecode`` error
  when parsing empty payloads (:issue:`229`). Thanks :user:`explosic4`
  for reporting and thanks user :user:`kochab` for the PR.

4.1.0 (2018-09-17)
******************

Features:

* Add ``webargs.testing`` module, which exposes ``CommonTestCase``
  to third-party parser libraries (see comments in :pr:`287`).

4.0.0 (2018-07-15)
******************

Features:

* *Backwards-incompatible*: Custom error handlers receive the
  `marshmallow.Schema` instance as the third argument. Update any
  functions decorated with `Parser.error_handler` to take a ``schema``
  argument, like so:

.. code-block:: python

    # 3.x
    @parser.error_handler
    def handle_error(error, req):
        raise CustomError(error.messages)


    # 4.x
    @parser.error_handler
    def handle_error(error, req, schema):
        raise CustomError(error.messages)


See `marshmallow-code/marshmallow#840 (comment) <https://github.com/marshmallow-code/marshmallow/issues/840#issuecomment-403481686>`_
for more information about this change.

Bug fixes:

* *Backwards-incompatible*: Rename ``webargs.async`` to
  ``webargs.asyncparser`` to fix compatibility with Python 3.7
  (:issue:`240`). Thanks :user:`Reskov` for the catch and patch.


Other changes:

* *Backwards-incompatible*: Drop support for Python 3.4 (:pr:`243`). Python 2.7 and
  >=3.5 are supported.
* *Backwards-incompatible*: Drop support for marshmallow<2.15.0.
  marshmallow>=2.15.0 and >=3.0.0b12 are officially supported.
* Use `black <https://github.com/ambv/black>`_ with `pre-commit <https://pre-commit.com/>`_
  for code formatting (:pr:`244`).

3.0.2 (2018-07-05)
******************

Bug fixes:

* Fix compatibility with marshmallow 3.0.0b12 (:pr:`242`). Thanks :user:`lafrech`.

3.0.1 (2018-06-06)
******************

Bug fixes:

* Respect `Parser.DEFAULT_VALIDATION_STATUS` when a `status_code` is not
  explicitly passed to `ValidationError` (:issue:`180`). Thanks :user:`foresmac` for
  finding this.

Support:

* Add "Returning HTTP 400 Responses" section to docs (:issue:`180`).

3.0.0 (2018-05-06)
******************

Changes:

* *Backwards-incompatible*: Custom error handlers receive the request object as the second
  argument. Update any functions decorated with ``Parser.error_handler`` to take a `req` argument, like so:

.. code-block:: python

    # 2.x
    @parser.error_handler
    def handle_error(error):
        raise CustomError(error.messages)


    # 3.x
    @parser.error_handler
    def handle_error(error, req):
        raise CustomError(error.messages)

* *Backwards-incompatible*: Remove unused ``instance`` and ``kwargs`` arguments of ``argmap2schema``.
* *Backwards-incompatible*: Remove ``Parser.load`` method (``Parser`` now calls ``Schema.load`` directly).

These changes shouldn't affect most users. However, they might break custom parsers calling these methods. (:pr:`222`)

* Drop support for aiohttp<3.0.0.

2.1.0 (2018-04-01)
******************

Features:

* Respect ``data_key`` field argument (in marshmallow 3). Thanks
  :user:`lafrech`.

2.0.0 (2018-02-08)
******************

Changes:

* Drop support for aiohttp<2.0.0.
* Remove use of deprecated `Request.has_body` attribute in
  aiohttpparser (:issue:`186`). Thanks :user:`ariddell` for reporting.

1.10.0 (2018-02-08)
*******************

Features:

* Add support for marshmallow>=3.0.0b7 (:pr:`188`). Thanks
  :user:`lafrech`.

Deprecations:

* Support for aiohttp<2.0.0 is deprecated and will be removed in webargs 2.0.0.

1.9.0 (2018-02-03)
******************

Changes:

* ``HTTPExceptions`` raised with `webargs.flaskparser.abort` will always
  have the ``data`` attribute, even if no additional keywords arguments
  are passed (:pr:`184`). Thanks :user:`lafrech`.

Support:

* Fix examples in examples/ directory.

1.8.1 (2017-07-17)
******************

Bug fixes:

* Fix behavior of ``AIOHTTPParser.use_args`` when ``as_kwargs=True`` is passed with a ``Schema`` (:issue:`179`). Thanks :user:`Itayazolay`.

1.8.0 (2017-07-16)
******************

Features:

* ``AIOHTTPParser`` supports class-based views, i.e. ``aiohttp.web.View`` (:issue:`177`). Thanks :user:`daniel98321`.

1.7.0 (2017-06-03)
******************

Features:

* ``AIOHTTPParser.use_args`` and ``AIOHTTPParser.use_kwargs`` work with `async def` coroutines (:issue:`170`). Thanks :user:`zaro`.

1.6.3 (2017-05-18)
******************

Support:

* Fix Flask error handling docs in "Framework support" section (:issue:`168`). Thanks :user:`nebularazer`.

1.6.2 (2017-05-16)
******************

Bug fixes:

* Fix parsing multiple arguments in ``AIOHTTParser`` (:issue:`165`). Thanks :user:`ariddell` for reporting and thanks :user:`zaro` for reporting.

1.6.1 (2017-04-30)
******************

Bug fixes:

* Fix form parsing in aiohttp>=2.0.0. Thanks :user:`DmitriyS` for the PR.

1.6.0 (2017-03-14)
******************

Bug fixes:

* Fix compatibility with marshmallow 3.x.

Other changes:

* Drop support for Python 2.6 and 3.3.
* Support marshmallow>=2.7.0.

1.5.3 (2017-02-04)
******************

Bug fixes:

* Port fix from release 1.5.2 to `AsyncParser`. This fixes :issue:`146` for ``AIOHTTPParser``.
* Handle invalid types passed to ``DelimitedList`` (:issue:`149`). Thanks :user:`psconnect-dev` for reporting.

1.5.2 (2017-01-08)
******************

Bug fixes:

* Don't add ``marshmallow.missing`` to ``original_data`` when using ``marshmallow.validates_schema(pass_original=True)`` (:issue:`146`). Thanks :user:`lafrech` for reporting and for the fix.

Other changes:

* Test against Python 3.6.

1.5.1 (2016-11-27)
******************

Bug fixes:

* Fix handling missing nested args when ``many=True`` (:issue:`120`, :issue:`145`).  Thanks :user:`chavz` and :user:`Bangertm` for reporting.
* Fix behavior of ``load_from`` in ``AIOHTTPParser``.

1.5.0 (2016-11-22)
******************

Features:

* The ``use_args`` and ``use_kwargs`` decorators add a reference to the undecorated function via the ``__wrapped__`` attribute. This is useful for unit-testing purposes (:issue:`144`). Thanks :user:`EFF` for the PR.

Bug fixes:

* If ``load_from`` is specified on a field, first check the field name before checking ``load_from`` (:issue:`118`). Thanks :user:`jasonab` for reporting.

1.4.0 (2016-09-29)
******************

Bug fixes:

* Prevent error when rendering validation errors to JSON in Flask (e.g. when using Flask-RESTful) (:issue:`122`). Thanks :user:`frol` for the catch and patch. NOTE: Though this is a bugfix, this is a potentially breaking change for code that needs to access the original ``ValidationError`` object.

.. code-block:: python

    # Before
    @app.errorhandler(422)
    def handle_validation_error(err):
        return jsonify({"errors": err.messages}), 422


    # After
    @app.errorhandler(422)
    def handle_validation_error(err):
        # The marshmallow.ValidationError is available on err.exc
        return jsonify({"errors": err.exc.messages}), 422


1.3.4 (2016-06-11)
******************

Bug fixes:

* Fix bug in parsing form in Falcon>=1.0.

1.3.3 (2016-05-29)
******************

Bug fixes:

* Fix behavior for nullable List fields (:issue:`107`). Thanks :user:`shaicantor` for reporting.

1.3.2 (2016-04-14)
******************

Bug fixes:

* Fix passing a schema factory to ``use_kwargs`` (:issue:`103`). Thanks :user:`ksesong` for reporting.

1.3.1 (2016-04-13)
******************

Bug fixes:

* Fix memory leak when calling ``parser.parse`` with a ``dict`` in a view (:issue:`101`). Thanks :user:`frankslaughter` for reporting.
* aiohttpparser: Fix bug in handling bulk-type arguments.

Support:

* Massive refactor of tests (:issue:`98`).
* Docs: Fix incorrect use_args example in Tornado section (:issue:`100`). Thanks :user:`frankslaughter` for reporting.
* Docs: Add "Mixing Locations" section (:issue:`90`). Thanks :user:`tuukkamustonen`.

1.3.0 (2016-04-05)
******************

Features:

* Add bulk-type arguments support for JSON parsing by passing ``many=True`` to a ``Schema`` (:issue:`81`). Thanks :user:`frol`.

Bug fixes:

* Fix JSON parsing in Flask<=0.9.0. Thanks :user:`brettdh` for the PR.
* Fix behavior of ``status_code`` argument to ``ValidationError`` (:issue:`85`). This requires **marshmallow>=2.7.0**. Thanks :user:`ParthGandhi` for reporting.


Support:

* Docs: Add "Custom Fields" section with example of using a ``Function`` field (:issue:`94`). Thanks :user:`brettdh` for the suggestion.

1.2.0 (2016-01-04)
******************

Features:

* Add ``view_args`` request location to ``FlaskParser`` (:issue:`82`). Thanks :user:`oreza` for the suggestion.

Bug fixes:

* Use the value of ``load_from`` as the key for error messages when it is provided (:issue:`83`). Thanks :user:`immerrr` for the catch and patch.

1.1.1 (2015-11-14)
******************

Bug fixes:

* aiohttpparser: Fix bug that raised a ``JSONDecodeError`` raised when parsing non-JSON requests using default ``locations`` (:issue:`80`). Thanks :user:`leonidumanskiy` for reporting.
* Fix parsing JSON requests that have a vendor media type, e.g. ``application/vnd.api+json``.

1.1.0 (2015-11-08)
******************

Features:

* ``Parser.parse``, ``Parser.use_args`` and ``Parser.use_kwargs`` can take a Schema factory as the first argument (:issue:`73`). Thanks :user:`DamianHeard` for the suggestion and the PR.

Support:

* Docs: Add "Custom Parsers" section with example of parsing nested querystring arguments (:issue:`74`). Thanks :user:`dwieeb`.
* Docs: Add "Advanced Usage" page.

1.0.0 (2015-10-19)
******************

Features:

* Add ``AIOHTTPParser`` (:issue:`71`).
* Add ``webargs.async`` module with ``AsyncParser``.

Bug fixes:

* If an empty list is passed to a List argument, it will be parsed as an empty list rather than being excluded from the parsed arguments dict (:issue:`70`). Thanks :user:`mTatcher` for catching this.

Other changes:

* *Backwards-incompatible*: When decorating resource methods with ``FalconParser.use_args``, the parsed arguments dictionary will be positioned **after** the request and response arguments.
* *Backwards-incompatible*: When decorating views with ``DjangoParser.use_args``, the parsed arguments dictionary will be positioned **after** the request argument.
* *Backwards-incompatible*: ``Parser.get_request_from_view_args`` gets passed a view function as its first argument.
* *Backwards-incompatible*: Remove logging from default error handlers.

0.18.0 (2015-10-04)
*******************

Features:

* Add ``FalconParser`` (:issue:`63`).
* Add ``fields.DelimitedList`` (:issue:`66`). Thanks :user:`jmcarp`.
* ``TornadoParser`` will parse json with ``simplejson`` if it is installed.
* ``BottleParser`` caches parsed json per-request for improved performance.

No breaking changes. Yay!

0.17.0 (2015-09-29)
*******************

Features:

* ``TornadoParser`` returns unicode strings rather than bytestrings (:issue:`41`). Thanks :user:`thomasboyt` for the suggestion.
* Add ``Parser.get_default_request`` and ``Parser.get_request_from_view_args`` hooks to simplify ``Parser`` implementations.
* *Backwards-compatible*: ``webargs.core.get_value`` takes a ``Field`` as its last argument. Note: this is technically a breaking change, but this won't affect most users since ``get_value`` is only used internally by ``Parser`` classes.

Support:

* Add ``examples/annotations_example.py`` (demonstrates using Python 3 function annotations to define request arguments).
* Fix examples. Thanks :user:`hyunchel` for catching an error in the Flask error handling docs.


Bug fixes:

* Correctly pass ``validate`` and ``force_all`` params to ``PyramidParser.use_args``.

0.16.0 (2015-09-27)
*******************

The major change in this release is that webargs now depends on `marshmallow <https://marshmallow.readthedocs.io/en/latest/>`_ for defining arguments and validation.

Your code will need to be updated to use ``Fields`` rather than ``Args``.

.. code-block:: python

    # Old API
    from webargs import Arg

    args = {
        "name": Arg(str, required=True),
        "password": Arg(str, validate=lambda p: len(p) >= 6),
        "display_per_page": Arg(int, default=10),
        "nickname": Arg(multiple=True),
        "Content-Type": Arg(dest="content_type", location="headers"),
        "location": Arg({"city": Arg(str), "state": Arg(str)}),
        "meta": Arg(dict),
    }

    # New API
    from webargs import fields

    args = {
        "name": fields.Str(required=True),
        "password": fields.Str(validate=lambda p: len(p) >= 6),
        "display_per_page": fields.Int(missing=10),
        "nickname": fields.List(fields.Str()),
        "content_type": fields.Str(load_from="Content-Type"),
        "location": fields.Nested({"city": fields.Str(), "state": fields.Str()}),
        "meta": fields.Dict(),
    }

Features:

* Error messages for all arguments are "bundled" (:issue:`58`).

Changes:

* *Backwards-incompatible*: Replace ``Args`` with marshmallow fields (:issue:`61`).
* *Backwards-incompatible*: When using ``use_kwargs``, missing arguments will have the special value ``missing`` rather than ``None``.
* ``TornadoParser`` raises a custom ``HTTPError`` with a ``messages`` attribute when validation fails.

Bug fixes:

* Fix required validation of nested arguments (:issue:`39`, :issue:`51`). These are fixed by virtue of using marshmallow's ``Nested`` field. Thanks :user:`ewang` and :user:`chavz` for reporting.

Support:

* Updated docs.
* Add ``examples/schema_example.py``.
* Tested against Python 3.5.

0.15.0 (2015-08-22)
*******************

Changes:

* If a parsed argument is ``None``, the type conversion function is not called :issue:`54`. Thanks :user:`marcellarius`.

Bug fixes:

* Fix parsing nested ``Args`` when the argument is missing from the input (:issue:`52`). Thanks :user:`stas`.

0.14.0 (2015-06-28)
*******************

Features:

* Add parsing of ``matchdict`` to ``PyramidParser``. Thanks :user:`hartror`.

Bug fixes:

* Fix ``PyramidParser's`` ``use_kwargs`` method (:issue:`42`). Thanks :user:`hartror` for the catch and patch.
* Correctly use locations passed to Parser's constructor when using ``use_args`` (:issue:`44`). Thanks :user:`jacebrowning` for the catch and patch.
* Fix behavior of ``default`` and ``dest`` argument on nested ``Args`` (:issue:`40` and :issue:`46`). Thanks :user:`stas`.

Changes:

* A 422 response is returned to the client when a ``ValidationError`` is raised by a parser (:issue:`38`).

0.13.0 (2015-04-05)
*******************

Features:

* Support for webapp2 via the `webargs.webapp2parser` module. Thanks :user:`Trii`.
* Store argument name on ``RequiredArgMissingError``. Thanks :user:`stas`.
* Allow error messages for required validation to be overriden. Thanks again :user:`stas`.

Removals:

* Remove ``source`` parameter from ``Arg``.


0.12.0 (2015-03-22)
*******************

Features:

* Store argument name on ``ValidationError`` (:issue:`32`). Thanks :user:`alexmic` for the suggestion. Thanks :user:`stas` for the patch.
* Allow nesting of dict subtypes.

0.11.0 (2015-03-01)
*******************

Changes:

* Add ``dest`` parameter to ``Arg`` constructor which determines the key to be added to the parsed arguments dictionary (:issue:`32`).
* *Backwards-incompatible*: Rename ``targets`` parameter to ``locations`` in ``Parser`` constructor, ``Parser#parse_arg``, ``Parser#parse``, ``Parser#use_args``, and ``Parser#use_kwargs``.
* *Backwards-incompatible*: Rename ``Parser#target_handler`` to ``Parser#location_handler``.

Deprecation:

* The ``source`` parameter is deprecated in favor of the ``dest`` parameter.

Bug fixes:

* Fix ``validate`` parameter of ``DjangoParser#use_args``.

0.10.0 (2014-12-23)
*******************

* When parsing a nested ``Arg``, filter out extra arguments that are not part of the ``Arg's`` nested ``dict`` (:issue:`28`). Thanks Derrick Gilland for the suggestion.
* Fix bug in parsing ``Args`` with both type coercion and ``multiple=True`` (:issue:`30`). Thanks Steven Manuatu for reporting.
* Raise ``RequiredArgMissingError`` when a required argument is missing on a request.

0.9.1 (2014-12-11)
******************

* Fix behavior of ``multiple=True`` when nesting Args (:issue:`29`). Thanks Derrick Gilland for reporting.

0.9.0 (2014-12-08)
******************

* Pyramid support thanks to @philtay.
* User-friendly error messages when ``Arg`` type conversion/validation fails. Thanks Andriy Yurchuk.
* Allow ``use`` argument to be a list of functions.
* Allow ``Args`` to be nested within each other, e.g. for nested dict validation. Thanks @saritasa for the suggestion.
* *Backwards-incompatible*: Parser will only pass ``ValidationErrors`` to its error handler function, rather than catching all generic Exceptions.
* *Backwards-incompatible*: Rename ``Parser.TARGET_MAP`` to ``Parser.__target_map__``.
* Add a short-lived cache to the ``Parser`` class that can be used to store processed request data for reuse.
* Docs: Add example usage with Flask-RESTful.

0.8.1 (2014-10-28)
******************

* Fix bug in ``TornadoParser`` that raised an error when request body is not a string (e.g when it is a ``Future``). Thanks Josh Carp.

0.8.0 (2014-10-26)
******************

* Fix ``Parser.use_kwargs`` behavior when an ``Arg`` is allowed missing. The ``allow_missing`` attribute is ignored when ``use_kwargs`` is called.
* ``default`` may be a callable.
* Allow ``ValidationError`` to specify a HTTP status code for the error response.
* Improved error logging.
* Add ``'query'`` as a valid target name.
* Allow a list of validators to be passed to an ``Arg`` or ``Parser.parse``.
* A more useful ``__repr__`` for ``Arg``.
* Add examples and updated docs.

0.7.0 (2014-10-18)
******************

* Add ``source`` parameter to ``Arg`` constructor. Allows renaming of keys in the parsed arguments dictionary. Thanks Josh Carp.
* ``FlaskParser's`` ``handle_error`` method attaches the string representation of validation errors on ``err.data['message']``. The raised exception is stored on ``err.data['exc']``.
* Additional keyword arguments passed to ``Arg`` are stored as metadata.

0.6.2 (2014-10-05)
******************

* Fix bug in ``TornadoParser's`` ``handle_error`` method. Thanks Josh Carp.
* Add ``error`` parameter to ``Parser`` constructor that allows a custom error message to be used if schema-level validation fails.
* Fix bug that raised a ``UnicodeEncodeError`` on Python 2 when an Arg's validator function received non-ASCII input.

0.6.1 (2014-09-28)
******************

* Fix regression with parsing an ``Arg`` with both ``default`` and ``target`` set (see issue #11).

0.6.0 (2014-09-23)
******************

* Add ``validate`` parameter to ``Parser.parse`` and ``Parser.use_args``. Allows validation of the full parsed output.
* If ``allow_missing`` is ``True`` on an ``Arg`` for which ``None`` is explicitly passed, the value will still be present in the parsed arguments dictionary.
* *Backwards-incompatible*: ``Parser's`` ``parse_*`` methods return ``webargs.core.Missing`` if the value cannot be found on the request. NOTE: ``webargs.core.Missing`` will *not* show up in the final output of ``Parser.parse``.
* Fix bug with parsing empty request bodies with ``TornadoParser``.

0.5.1 (2014-08-30)
******************

* Fix behavior of ``Arg's`` ``allow_missing`` parameter when ``multiple=True``.
* Fix bug in tornadoparser that caused parsing JSON arguments to fail.

0.5.0 (2014-07-27)
******************

* Fix JSON parsing in Flask parser when Content-Type header contains more than just `application/json`. Thanks Samir Uppaluru for reporting.
* *Backwards-incompatible*: The ``use`` parameter to ``Arg`` is called before type conversion occurs. Thanks Eric Wang for the suggestion.
* Tested on Tornado>=4.0.

0.4.0 (2014-05-04)
******************

* Custom target handlers can be defined using the ``Parser.target_handler`` decorator.
* Error handler can be specified using the ``Parser.error_handler`` decorator.
* ``Args`` can define their request target by passing in a ``target`` argument.
* *Backwards-incompatible*: ``DEFAULT_TARGETS`` is now a class member of ``Parser``. This allows subclasses to override it.

0.3.4 (2014-04-27)
******************

* Fix bug that caused ``use_args`` to fail on class-based views in Flask.
* Add ``allow_missing`` parameter to ``Arg``.

0.3.3 (2014-03-20)
******************

* Awesome contributions from the open-source community!
* Add ``use_kwargs`` decorator. Thanks @venuatu.
* Tornado support thanks to @jvrsantacruz.
* Tested on Python 3.4.


0.3.2 (2014-03-04)
******************

* Fix bug with parsing JSON in Flask and Bottle.

0.3.1 (2014-03-03)
******************

* Remove print statements in core.py. Oops.

0.3.0 (2014-03-02)
******************

* Add support for repeated parameters (#1).
* *Backwards-incompatible*: All `parse_*` methods take `arg` as their fourth argument.
* Add ``error_handler`` param to ``Parser``.

0.2.0 (2014-02-26)
******************

* Bottle support.
* Add ``targets`` param to ``Parser``. Allows setting default targets.
* Add ``files`` target.

0.1.0 (2014-02-16)
******************

* First release.
* Parses JSON, querystring, forms, headers, and cookies.
* Support for Flask and Django.
