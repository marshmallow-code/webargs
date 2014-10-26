Changelog
---------

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

