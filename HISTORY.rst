Changelog
---------

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
++++++++++++++++++

* Custom target handlers can be defined using the ``Parser.target_handler`` decorator.
* Error handler can be specified using the ``Parser.error_handler`` decorator.
* ``Args`` can define their request target by passing in a ``target`` argument.
* *Backwards-incompatible*: ``DEFAULT_TARGETS`` is now a class member of ``Parser``. This allows subclasses to override it.

0.3.4 (2014-04-27)
++++++++++++++++++

* Fix bug that caused ``use_args`` to fail on class-based views in Flask.
* Add ``allow_missing`` parameter to ``Arg``.

0.3.3 (2014-03-20)
++++++++++++++++++

* Awesome contributions from the open-source community!
* Add ``use_kwargs`` decorator. Thanks @venuatu.
* Tornado support thanks to @jvrsantacruz.
* Tested on Python 3.4.


0.3.2 (2014-03-04)
++++++++++++++++++

* Fix bug with parsing JSON in Flask and Bottle.

0.3.1 (2014-03-03)
++++++++++++++++++

* Remove print statements in core.py. Oops.

0.3.0 (2014-03-02)
++++++++++++++++++

* Add support for repeated parameters (#1).
* *Backwards-incompatible*: All `parse_*` methods take `arg` as their fourth argument.
* Add ``error_handler`` param to ``Parser``.

0.2.0 (2014-02-26)
++++++++++++++++++

* Bottle support.
* Add ``targets`` param to ``Parser``. Allows setting default targets.
* Add ``files`` target.

0.1.0 (2014-02-16)
++++++++++++++++++

* First release.
* Parses JSON, querystring, forms, headers, and cookies.
* Support for Flask and Django.
