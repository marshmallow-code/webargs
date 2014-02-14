=======
webargs
=======

.. image:: https://badge.fury.io/py/webargs.png
    :target: http://badge.fury.io/py/webargs

HTTP Request Argument Parsing, Simplified

.. code-block:: python

    from flask import Flask
    from webargs import Arg
    from webargs.flaskparser import FlaskParser

    app = Flask(__name__)
    parser = FlaskParser()

    hello_args = {
        'name': Arg(str, required=True)
    }

    @app.route('/')
    @parser.use_args(hello_args)
    def index(args):
        return 'Hello ' + args['name']

    app.run()

    # curl http://localhost:5000/\?name\='World'
    # Hello World

Parses

* Form data
* Request arguments
* Querystrings
* Headers
* Cookies

Framework support

* Flask

Documentation
-------------

Full documentation is available at https://webargs.readthedocs.org/.

Requirements
------------

- Python >= 2.6 or >= 3.3

License
-------

MIT licensed. See the bundled `LICENSE <https://github.com/sloria/webargs/blob/master/LICENSE>`_ file for more details.
