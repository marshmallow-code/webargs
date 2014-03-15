Changelog
---------

0.3.3 (unreleased)
++++++++++++++++++

* Add ``use_kwargs`` decorator. Thanks @venuatu.

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
