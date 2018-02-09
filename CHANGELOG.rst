Changelog
---------

2.0.0 (2018-02-08)
******************

Changes:

* Drop support for aiohttp<2.0.0.
* Remove use of deprecated `Request.has_body` attribute in
  aiohttpparser (:issue:`186`). Thanks :user:`ariddell` for reporting.

1.10.0 (2018-02-08)
*******************

Features:

* Add support for marshmallow>=3.0.0b7 (:issue:`188`). Thanks
  :user:`lafrech`.

Deprecations:

* Support for aiohttp<2.0.0 is deprecated and will be removed in webargs 2.0.0.

1.9.0 (2018-02-03)
******************

Changes:

* ``HTTPExceptions`` raised with `webargs.flaskparser.abort` will always
  have the ``data`` attribute, even if no additional keywords arguments
  are passed (:issue:`184`). Thanks :user:`lafrech`.

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
        return jsonify({'errors': err.messages}), 422

    # After
    @app.errorhandler(422)
    def handle_validation_error(err):
        # The marshmallow.ValidationError is available on err.exc
        return jsonify({'errors': err.exc.messages}), 422


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
        'name': Arg(str, required=True)
        'password': Arg(str, validate=lambda p: len(p) >= 6),
        'display_per_page': Arg(int, default=10),
        'nickname': Arg(multiple=True),
        'Content-Type': Arg(dest='content_type', location='headers'),
        'location': Arg({
            'city': Arg(str),
            'state': Arg(str)
        })
        'meta': Arg(dict),
    }

    # New API
    from webargs import fields

    args = {
        'name': fields.Str(required=True)
        'password': fields.Str(validate=lambda p: len(p) >= 6),
        'display_per_page': fields.Int(missing=10),
        'nickname': fields.List(fields.Str()),
        'content_type': fields.Str(load_from='Content-Type'),
        'location': fields.Nested({
            'city': fields.Str(),
            'state': fields.Str()
        }),
        'meta': fields.Dict(),
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
