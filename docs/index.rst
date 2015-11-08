:orphan:

=======
webargs
=======

.. container:: lead

    A friendly library for parsing HTTP request arguments.


Release v\ |version|. (:ref:`Changelog <changelog>`)

webargs is a Python library for parsing HTTP request arguments, with built-in support for popular web frameworks, including Flask, Django, Bottle, Tornado, Pyramid, webapp2, Falcon, and aiohttp.


.. code-block:: python

    from flask import Flask
    from webargs import fields
    from webargs.flaskparser import use_args

    app = Flask(__name__)

    hello_args = {
        'name': fields.Str(required=True)
    }

    @app.route('/')
    @use_args(hello_args)
    def index(args):
        return 'Hello ' + args['name']

    if __name__ == '__main__':
        app.run()

    # curl http://localhost:5000/\?name\='World'
    # Hello World

Webargs will automatically parse:

**Query Parameters**
::

    $ curl http://localhost:5000/\?name\='Freddie'
    Hello Freddie

**Form Data**
::

  $ curl -d 'name=Brian' http://localhost:5000/
  Hello Brian

**JSON Data**
::

  $ curl -X POST -H "Content-Type: application/json" -d '{"name":"Roger"}' http://localhost:5000/
  Hello Roger

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
* **marshmallow integration**. Webargs uses `marshmallow <https://marshmallow.readthedocs.org/en/latest/>`_ under the hood. When you need more flexibility than dictionaries, you can use marshmallow `Schemas <marshmallow.Schema>` to define your request arguments.

Get It Now
----------

::

    pip install -U webargs

Ready to get started? Go on to the :ref:`Quickstart tutorial <quickstart>` or check out some `examples <https://github.com/sloria/webargs/tree/dev/examples>`_.

User Guide
----------

.. toctree::
    :maxdepth: 2

    install
    quickstart
    advanced
    framework_support

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
   authors
   contributing
