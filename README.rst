=======
webargs
=======

.. image:: https://badgen.net/pypi/v/webargs
    :target: https://badge.fury.io/py/webargs
    :alt: PyPI version

.. image:: https://badgen.net/travis/marshmallow-code/webargs
    :target: https://travis-ci.org/marshmallow-code/webargs
    :alt: TravisCI build status

.. image:: https://badgen.net/badge/marshmallow/2,3?list=1
    :target: https://marshmallow.readthedocs.io/en/latest/upgrading.html
    :alt: marshmallow 2/3 compatible

.. image:: https://badgen.net/badge/code%20style/black/000
    :target: https://github.com/ambv/black
    :alt: code style: black

Homepage: https://webargs.readthedocs.io/

webargs is a Python library for parsing and validating HTTP request arguments, with built-in support for popular web frameworks, including Flask, Django, Bottle, Tornado, Pyramid, webapp2, Falcon, and aiohttp.

.. code-block:: python

    from flask import Flask
    from webargs import fields
    from webargs.flaskparser import use_args

    app = Flask(__name__)

    hello_args = {"name": fields.Str(required=True)}


    @app.route("/")
    @use_args(hello_args)
    def index(args):
        return "Hello " + args["name"]


    if __name__ == "__main__":
        app.run()

    # curl http://localhost:5000/\?name\='World'
    # Hello World

Install
-------

::

    pip install -U webargs

webargs supports Python >= 2.7 or >= 3.5.


Documentation
-------------

Full documentation is available at https://webargs.readthedocs.io/.

Project Links
-------------

- Docs: https://webargs.readthedocs.io/
- Changelog: https://webargs.readthedocs.io/en/latest/changelog.html
- PyPI: https://pypi.python.org/pypi/webargs
- Issues: https://github.com/marshmallow-code/webargs/issues


License
-------

MIT licensed. See the `LICENSE <https://github.com/marshmallow-code/webargs/blob/dev/LICENSE>`_ file for more details.
