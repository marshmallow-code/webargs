=======
webargs
=======

.. image:: https://badge.fury.io/py/webargs.svg
    :target: http://badge.fury.io/py/webargs

.. image:: https://travis-ci.org/sloria/webargs.svg?branch=pypi
    :target: https://travis-ci.org/sloria/webargs

Homepage: https://webargs.readthedocs.io/

webargs is a Python library for parsing and validating HTTP request arguments, with built-in support for popular web frameworks, including Flask, Django, Bottle, Tornado, Pyramid, webapp2, Falcon, and aiohttp.

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

Install
-------

::

    pip install -U webargs

webargs supports Python >= 2.7 or >= 3.4.


Documentation
-------------

Full documentation is available at https://webargs.readthedocs.io/.

Project Links
-------------

- Docs: http://webargs.readthedocs.io/
- Changelog: http://webargs.readthedocs.io/en/latest/changelog.html
- PyPI: https://pypi.python.org/pypi/webargs
- Issues: https://github.com/sloria/webargs/issues


License
-------

MIT licensed. See the `LICENSE <https://github.com/sloria/webargs/blob/dev/LICENSE>`_ file for more details.
