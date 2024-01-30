=======
webargs
=======

Release v\ |version|. (:doc:`Changelog <changelog>`)

webargs is a Python library for parsing and validating HTTP request objects, with built-in support for popular web frameworks, including Flask, Django, Bottle, Tornado, Pyramid, Falcon, and aiohttp.

Upgrading from an older version?
--------------------------------

See the :doc:`Upgrading to Newer Releases <upgrading>` page for notes on getting your code up-to-date with the latest version.


Usage and Simple Examples
-------------------------

.. code-block:: python

    from flask import Flask
    from webargs import fields
    from webargs.flaskparser import use_args

    app = Flask(__name__)


    @app.route("/")
    @use_args({"name": fields.Str(required=True)}, location="query")
    def index(args):
        return "Hello " + args["name"]


    if __name__ == "__main__":
        app.run()

    # curl http://localhost:5000/\?name\='World'
    # Hello World

By default Webargs will automatically parse JSON request bodies. But it also
has support for:

**Query Parameters**
::

  $ curl http://localhost:5000/\?name\='Freddie'
  Hello Freddie

  # pass location="query" to use_args

**Form Data**
::

  $ curl -d 'name=Brian' http://localhost:5000/
  Hello Brian

  # pass location="form" to use_args

**JSON Data**
::

  $ curl -X POST -H "Content-Type: application/json" -d '{"name":"Roger"}' http://localhost:5000/
  Hello Roger

  # pass location="json" (or omit location) to use_args

and, optionally:

- Headers
- Cookies
- Files
- Paths

Why Use It
----------

* **Simple, declarative syntax**. Define your arguments as a mapping rather than imperatively pulling values off of request objects.
* **Code reusability**. If you have multiple views that have the same request parameters, you only need to define your parameters once. You can also reuse validation and pre-processing routines.
* **Self-documentation**. Webargs makes it easy to understand the expected arguments and their types for your view functions.
* **Automatic documentation**. The metadata that webargs provides can serve as an aid for automatically generating API documentation.
* **Cross-framework compatibility**. Webargs provides a consistent request-parsing interface that will work across many Python web frameworks.
* **marshmallow integration**. Webargs uses `marshmallow <https://marshmallow.readthedocs.io/en/latest/>`_ under the hood. When you need more flexibility than dictionaries, you can use marshmallow `Schemas <marshmallow.Schema>` to define your request arguments.

Get It Now
----------

::

    pip install -U webargs

Ready to get started? Go on to the :doc:`Quickstart tutorial <quickstart>` or check out some `examples <https://github.com/marshmallow-code/webargs/tree/dev/examples>`_.

User Guide
----------

.. toctree::
    :maxdepth: 2

    install
    quickstart
    advanced
    framework_support
    ecosystem

API Reference
-------------

.. toctree::
    :maxdepth: 2

    api


Project Info
------------

.. toctree::
   :maxdepth: 1

   license
   changelog
   upgrading
   authors
   contributing
