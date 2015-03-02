*******
webargs
*******

*webargs is a Python library for parsing HTTP request arguments, with built-in support for popular web frameworks, including Flask, Django, Bottle, Tornado, and Pyramid.*

Release v\ |version|. (:ref:`Changelog <changelog>`)

.. contents::
   :local:
   :depth: 2

Useful Links:

`webargs @ Github <http://github.com/sloria/webargs>`_ |
`webargs @ PyPI <http://pypi.python.org/pypi/webargs>`_ |
`Issue Tracker <http://github.com/sloria/webargs/issues>`_

Hello Webargs
=============

.. code-block:: python

    from flask import Flask
    from webargs import Arg
    from webargs.flaskparser import use_args

    app = Flask(__name__)

    hello_args = {
        'name': Arg(str, default='World')
    }

    @app.route('/', methods=['get', 'post'])
    @use_args(hello_args)
    def index(args):
        return 'Hello ' + args['name']

    if __name__ == '__main__':
        app.run()

Webargs will automatically parse:

**URL Parameters**
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

**Framework support**

- Flask
- Django
- Bottle
- Tornado
- Pyramid


Why Use It
==========

* **Simple, declarative syntax**. Define your arguments as a mapping rather than imperatively pulling values off of request objects.
* **Code reusability**. If you have multiple views that have the same request parameters, you only need to define your parameters once. You can also reuse validation and pre-processing routines.
* **Self-documentation**. Webargs makes it easy to understand the expected arguments and their types for your view functions.
* **Automatic documentation**. The metadata that webargs provides can serve as an aid for automatically generating API documentation.
* **Cross-framework compatibility**. Webargs provides a consistent request-parsing interface that will work across the major Python web frameworks.

Inspired by `Flask-RESTful's <http://flask-restful.readthedocs.org/en/latest/>`_ reqparser, webargs offers a lightweight, cross-framework solution to request parsing that's simple and fun to use.

Install
=======

webargs is *small*. It has no hard dependencies, so you can easily vendorize it within your project or install the latest version from the PyPI:
::

   pip install -U webargs

webargs supports Python >= 2.6 or >= 3.3.

Examples
========

See the `examples directory <https://github.com/sloria/webargs/tree/dev/examples>`_ for full examples using webargs.

Usage Guide
===========

Basic Usage
-----------

Arguments are specified as a dictionary of name -> :class:`Arg <webargs.core.Arg>` pairs. :class:`Arg <webargs.core.Arg>` objects take a number of optional arguments, e.g. for type conversion and validation.

Below are examples of the various parameters that :class:`Arg <webarsg.core.Arg>` objects can take.

.. code-block:: python

    from webargs import Arg

    user_args = {

        'username': Arg(str, required=True),  # 400 error thrown if
                                              # required argument is missing

        # Validation function (`validate`)
        'password': Arg(str, validate=lambda p: len(p) > 6,
                        error='Invalid password'),

        # Conversion/postprocessing function (`use`)
        'fullname': Arg(str, use=lambda n: n.lower()),

        # Default value
        'display_per_page': Arg(int, default=10),

        # Repeated parameter, e.g. "/?nickname=Fred&nickname=Freddie"
        'nickname': Arg(str, multiple=True),

        # When you know where an argument should be parsed from
        'active': Arg(bool, location='query')

        # When value is keyed on a variable-unsafe name or you want to rename a key
        'Content-Type': Arg(str, dest='content_type')
    }

To parse request arguments, use the :meth:`parse <webargs.core.Parser.parse>` method of a :class:`Parser <webargs.core.Parser>` object.

.. code-block:: python

    from flask import request
    from webargs.flaskparser import FlaskParser

    parser = FlaskParser()

    @app.route('/register')
    def register():
        args = parser.parse(user_args, request)
        return register_user(args['username'], args['password'],
            fullname=args['fullname'], per_page=args['display_per_page'])

Alternatively, you can decorate your view with :meth:`use_args <webargs.core.Parser.use_args>` or :meth:`use_kwargs <webargs.core.Parser.use_kwargs>`. The parsed arguments dictionary will be injected as a parameter of your view function or as keyword arguments, respectively.

.. code-block:: python

    from webargs.flaskparser import use_args, use_kwargs

    @app.route('/register')
    @use_args(user_args)  # Injects args dictionary
    def register(args):
        return register_user(args['username'], args['password'],
            fullname=args['fullname'], per_page=args['display_per_page'])

    @app.route('/settings')
    @use_kwargs(user_args)  # Injects keyword arguments
    def user_settings(username, password, fullname, display_per_page, nickname):
        return render_template('settings.html', username=username, nickname=nickname)


By default, webargs will search for arguments from the URL querystring (e.g. ``"/?name=foo"``), form data, and JSON data (in that order). You can explicitly specify which locations to search, like so:

.. code-block:: python

    @app.route('/register')
    @use_args(user_args, locations=('json', 'form'))
    def register(args):
        return 'registration page'

Available locations include:

- ``'querystring'`` (same as ``'query'``)
- ``'json'``
- ``'form'``
- ``'headers'``
- ``'cookies'``
- ``'files'``

Adding Custom Location Handlers
-------------------------------

To add your own custom location handler, write a function that receives a request, an argument name, and an :class:`Arg <webargs.core.Arg>` object, then decorate that function with :func:`Parser.location_handler <webargs.core.Parser.location_handler>`.


.. code-block:: python

    from webargs.flaskparser import parser

    @parser.location_handler('data')
    def parse_data(request, name, arg):
        return request.data.get(name)

    # Now 'data' can be specified as a location

    @parser.use_args({'per_page': Arg(int)}, locations=('data', ))
    def posts(args):
        return 'displaying {} posts'.format(args['per_page'])


Validation
----------

Each :class:`Arg <webargs.core.Arg>` object can be validated individually by passing the ``validate`` argument.

.. code-block:: python

    from webargs import Arg

    args = {
        'age': Arg(int, validate=lambda val: val > 0)
    }

The validator may return either a `boolean` or raise a :exc:`ValidationError <webargs.core.ValidationError>`.

.. code-block:: python

    def must_exist_in_db(val):
        if not User.query.get(val):
            # Optionally pass a status_code
            raise ValidationError('User does not exist', status_code=404)

    args = {
        'id': Arg(int, validate=must_exist_in_db)
    }

.. note::

    You may also pass a list of validators to the ``validate`` parameter.

The full arguments dictionary can also be validated by passing ``validate`` to :meth:`Parser.parse <webargs.core.Parser.parse>`, :meth:`Parser.use_args <webargs.core.Parser.use_args>`, :meth:`Parser.use_kwargs <webargs.core.Parser.use_kwargs>`.


.. code-block:: python

    from webargs import Arg
    from webargs.flaskparser import parser

    args = {
        'age': Arg(int),
        'years_employed': Arg(int),
    }

    # ...
    result = parser.parse(args,
                          validate=lambda args: args['years_employed'] < args['age'])


Handling Errors
---------------

Each parser has a default error handling method. To override the error handling callback, write a function that receives an error and handles it, then decorate that function with :func:`Parser.error_handler <webargs.core.Parser.error_handler>`.

.. code-block:: python

    from webargs import core
    parser = core.Parser()

    class CustomError(Exception):
        pass

    @parser.error_handler
    def handle_error(error):
        raise CustomError(error)


Nesting Args
------------

`Arg` dictionaries can be nested within each other. This can be useful for validating nested data.

.. code-block:: python

        args = {
            'name': Arg({
                'first': Arg(str, required=True),
                'last': Arg(str, required=True),
            })
        }


Flask Support
=============

Flask support is available via the :mod:`webargs.flaskparser` module.

Decorator Usage
---------------

When using the :meth:`use_args <webargs.flaskparser.FlaskParser.use_args>` decorator, the arguments dictionary will be *before* any URL variable parameters.

.. code-block:: python

    from webargs.flaskparser import use_args

    @app.route('/user/<int:uid>')
    @use_args({'per_page': Arg(int)})
    def user_detail(args, uid):
        return ('The user page for user {uid}, '
                'showing {per_page} posts.').format(uid=uid,
                                                    per_page=args['per_page'])

Error Handling
--------------

Webargs uses Flask's ``abort`` function to raise an ``HTTPException`` when a validation error occurs. If you use the ``Flask.errorhandler`` method to handle errors, you can access validation messages from the ``data`` attribute of an error.

Here is an example error handler that returns validation messages to the client as JSON.

.. code-block:: python

    from flask import jsonify

    @app.errorhandler(400)
    def handle_bad_request(err):
        # webargs attaches additional metadata to the `data` attribute
        data = getattr(err, 'data')
        if data:
            err_message = data['message']
        else:
            err_message = 'Invalid request'
        return jsonify({
            'message': err_message,
        }), 400


Django Support
==============

Django support is available via the :mod:`webargs.djangoparser` module.

Webargs can parse Django request arguments in both function-based and class-based views.

Decorator Usage
---------------

When using the :meth:`use_args <webargs.djangoparser.DjangoParser.use_args>` decorator, the arguments dictionary will always be the second parameter (after ``self`` or ``request``).

**Function-based Views**

.. code-block:: python

  from django.http import HttpResponse
  from webargs import Arg
  from webargs.djangoparser import use_args

  account_args = {
    'username': Arg(str),
    'password': Arg(str)
  }

  @use_args(account_args)
  def login_user(request, args):
      if request.method == 'POST':
          login(args['username'], args['password'])
      return HttpResponse('Login page')

**Class-based Views**

.. code-block:: python

    from django.views.generic import View
    from django.shortcuts import render_to_response
    from webargs import Arg
    from webargs.djangoparser import use_args

    blog_args = {
        'title': Arg(str, use=lambda t: t.lower()),
        'author': Arg(str)
    }

    class BlogPostView(View):
        @use_args(blog_args)
        def get(self, args, request):
          blog_post = Post.objects.get(title__iexact=args['title'],
                                       author=args['author'])
          return render_to_response('post_template.html',
                                    {'post': blog_post})

Error Handling
--------------

The :class:`DjangoParser` does not override :meth:`handle_error <webargs.core.Parser.handle_error>`, so your Django views are responsible for catching any :exc:`ValidationErrors` raised by the parser and returning the appropriate `HTTPResponse`.

.. code-block:: python

    from django.http import JsonResponse

    from webargs import Arg, ValidationError

    args = {
        'name': Arg(str, required=True)
    }
    def index(request):
        try:
            args = parser.parse(required_args, request)
        except ValidationError as err:
            return JsonResponse({'error': str(err)}, status=400)
        return JsonResponse({'message': 'Hello {name}'.format(name=name)})

Tornado Support
===============

Tornado argument parsing is available via the :mod:`webargs.tornadoparser` module.

The :class:`webargs.tornadoparser.TornadoParser` parses arguments from a :class:`tornado.httpserver.HTTPRequest` object. The :class:`TornadoParser <webargs.tornadoparser.TornadoParser>` can be used directly, or you can decorate handler methods with :meth:`use_args <webargs.tornadoparser.TornadoParser.use_args>` or :meth:`use_kwargs <webargs.tornadoparser.TornadoParser.use_kwargs>`.

.. code-block:: python

    import tornado.ioloop
    import tornado.web

    from webargs import Arg
    from webargs.tornadoparser import parser


    class HelloHandler(tornado.web.RequestHandler):

        hello_args = {
            'name': Arg(str),
        }

        def post(self, id):
            reqargs = parser.parse(self.hello_args, self.request)
            response = {
                'message': 'Hello {}'.format(reqargs['name'])
            }
            self.write(response)

    application = tornado.web.Application([
        (r"/hello/([0-9]+)", HelloHandler),
    ], debug=True)

    if __name__ == "__main__":
        application.listen(8888)
        tornado.ioloop.IOLoop.instance().start()

Decorator Usage
---------------

When using the :meth:`use_args <webargs.tornadoparser.TornadoParser.use_args>` decorator, the decorated method will have the dictionary of parsed arguments passed as a positional argument after ``self``.


.. code-block:: python

    from webargs import Arg
    from webargs.tornadoparser import use_args

    class HelloHandler(tornado.web.RequestHandler):

        @use_args({'name': Arg(str)})
        def post(self, reqargs, id):
            response = {
                'message': 'Hello {}'.format(reqargs['name'])
            }
            self.write(response)


With :meth:`use_kwargs <webargs.tornadoparser.TornadoParser.use_kwargs>`, the parsed arguments will be injected as keyword arguments.

.. code-block:: python

    class HelloHandler(tornado.web.RequestHandler):

        @use_kwargs({'name': Arg(str)})
        def post(self, id, name):  # "name" is injected
            response = {
                'message': 'Hello {}'.format(name)
            }
            self.write(response)

Pyramid Support
===============

Pyramid support is available via the :mod:`webargs.pyramidparser` module.

Decorator Usage
---------------

When using the :meth:`use_args <webargs.pyramidparser.PyramidParser.use_args>` decorator on a view callable, the arguments dictionary will be positioned after the `request` argument.

.. code-block:: python

    from pyramid.response import Response
    from webargs.pyramidparser import use_args

    @use_args({'per_page': Arg(int)})
    def user_detail(request, args):
        return Response('The user page for user {uid}, '
                'showing {per_page} posts.').format(uid=uid,
                                                    per_page=args['per_page']))

As with the other parser modules, :meth:`use_kwargs <webargs.pyramidparser.PyramidParser.use_kwargs>` will add keyword arguments to the view callable.


API Reference
=============

.. module:: webargs

webargs.core
------------

.. automodule:: webargs.core
    :inherited-members:

webargs.flaskparser
-------------------

.. automodule:: webargs.flaskparser
    :inherited-members:

webargs.djangoparser
--------------------

.. automodule:: webargs.djangoparser
    :inherited-members:

webargs.bottleparser
--------------------

.. automodule:: webargs.bottleparser
    :inherited-members:

webargs.tornadoparser
---------------------

.. automodule:: webargs.tornadoparser
    :inherited-members:

webargs.pyramidparser
---------------------

.. automodule:: webargs.pyramidparser
    :inherited-members:


Project Info
============

.. toctree::
   :maxdepth: 1

   license
   changelog
   authors
   contributing

Suggested Pairings
==================

If you are using webargs to handle input data for your HTTP API, you might consider using the `marshmallow <https://github.com/sloria/marshmallow>`_ library for formatting your output data.

