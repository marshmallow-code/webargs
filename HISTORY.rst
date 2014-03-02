Changelog
---------

0.3.0 (unreleased)
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
