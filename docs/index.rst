.. webargs documentation master file, created by
   sphinx-quickstart on Tue Jul  9 22:26:36 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

*******
webargs
*******

`Webargs is a Python utility library for parsing HTTP request arguments, with built-in support for popular web frameworks, including Flask and Django.`

Release v\ |version|. (:ref:`Changelog <changelog>`)

.. contents::
   :local:

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

**Framework support**

- Flask
- Django
- Bottle


Why Use It
==========

* *Simple to use*. Can't remember if you're supposed to pull an argument from ``request.form``, ``request.data``, ``request.args``, or ``request.json``? No problem; webargs will find the value for you.
* *Code reusability*. If you have multiple views that have the same request parameters, you only need to define your parameters once. You can also reuse validation and pre-processing routines.

Install
=======

Webargs is *small*. It has no hard dependencies, so you can easily vendorize it within your project or install the latest version from the PyPI:
::

   pip install -U webargs

webargs supports Python >= 2.6 or >= 3.3.

Usage
=====

Arguments are specified as a dictionary of name -> :class:`Arg <webargs.Arg>` pairs. :class:`Arg <webargs.Arg>` objects take a number of optional arguments, e.g. for type conversion and validation.

.. code-block:: python

    from webargs import Arg

    user_args = {

        'username': Arg(str, required=True),  # 400 error thrown if
                                              # required argument is missing

        # Validation function (`validate`)
        'password': Arg(str, validate=lambda p: len(p) > 6,
                        error='Invalid password'),

        # Conversion function (`use`)
        'fullname': Arg(str, use=lambda n: n.lower()),

        # Default value
        'display_per_page': Arg(int, default=10)
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

Alternatively, you can decorate your view with ``use_args``. The parsed arguments dictionary will be injected as a parameter of your view function.

.. code-block:: python

    from webargs.flaskparser import use_args

    @app.route('/register')
    @use_args(user_args)
    def register(args):
        return register_user(args['username'], args['password'],
            fullname=args['fullname'], per_page=args['display_per_page'])

By default, webargs will search for arguments from the URL querystring (e.g. ``"/?name=foo"``), form data, and JSON data (in that order). You can explicitly specify which targets to search, like so:

.. code-block:: python

    @app.route('/register')
    @use_args(user_args, targets=('json', 'form'))
    def register(args):
        return 'registration page'

Available targets include:

- ``'querystring'``
- ``'json'``
- ``'form'``
- ``'headers'``
- ``'cookies'``

Flask Support
=============

Flask support is available via the :mod:`webargs.flaskparser` module.

Decorator Usage
---------------

When using the ``use_args`` decorator, the arguments dictionary will be *before* any URL variable parameters.

.. code-block:: python

    from webargs.flaskparser import use_args

    @app.route('/user/<int:uid>')
    @use_args({'per_page': Arg(int)})
    def user_detail(args, uid):
        return ('The user page for user {uid}, '
                'showing {per_page} posts.').format(uid=uid,
                                                    per_page=args['per_page'])


Django Support
==============

Django support is available via the :mod:`webargs.djangoparser` module.

Webargs can parse Django request arguments in both function-based and class-based views.

Decorator Usage
---------------

When using the ``use_args`` decorator, the arguments dictionary will always be the second parameter (after ``self`` or ``request``).

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

API Reference
=============

.. module:: webargs

webargs.core
------------

.. autoclass:: Arg
    :members:

.. autoclass:: webargs.core.Parser
    :members:

.. autoexception:: webargs.core.WebargsError

.. autoexception:: webargs.core.ValidationError


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


Project Info
============

.. toctree::
   :maxdepth: 2

   license
   changelog

