.. _frameworks:

Framework Support
=================

This section includes notes for using webargs with specific web frameworks.

Flask
-----

Flask support is available via the :mod:`webargs.flaskparser` module.

Decorator Usage
+++++++++++++++

When using the :meth:`use_args <webargs.flaskparser.FlaskParser.use_args>` decorator, the arguments dictionary will be *before* any URL variable parameters.

.. code-block:: python

    from webargs import fields
    from webargs.flaskparser import use_args

    @app.route('/user/<int:uid>')
    @use_args({'per_page': fields.Int()})
    def user_detail(args, uid):
        return ('The user page for user {uid}, '
                'showing {per_page} posts.').format(uid=uid,
                                                    per_page=args['per_page'])

Error Handling
++++++++++++++

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


Django
------

Django support is available via the :mod:`webargs.djangoparser` module.

Webargs can parse Django request arguments in both function-based and class-based views.

Decorator Usage
+++++++++++++++

When using the :meth:`use_args <webargs.djangoparser.DjangoParser.use_args>` decorator, the arguments dictionary will always be the second parameter (after ``self`` or ``request``).

**Function-based Views**

.. code-block:: python

  from django.http import HttpResponse
  from webargs import Arg
  from webargs.djangoparser import use_args

  account_args = {
    'username': fields.Str(required=True),
    'password': fields.Str(required=True),
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
    from webargs import fields
    from webargs.djangoparser import use_args

    blog_args = {
        'title': fields.Str(),
        'author': fields.Str(),
    }

    class BlogPostView(View):
        @use_args(blog_args)
        def get(self, args, request):
          blog_post = Post.objects.get(title__iexact=args['title'],
                                       author=args['author'])
          return render_to_response('post_template.html',
                                    {'post': blog_post})

Error Handling
++++++++++++++

The :class:`DjangoParser` does not override :meth:`handle_error <webargs.core.Parser.handle_error>`, so your Django views are responsible for catching any :exc:`ValidationErrors` raised by the parser and returning the appropriate `HTTPResponse`.

.. code-block:: python

    from django.http import JsonResponse

    from webargs import fields, ValidationError

    args = {
        'name': fields.Str(required=True)
    }
    def index(request):
        try:
            args = parser.parse(required_args, request)
        except ValidationError as err:
            return JsonResponse({'error': str(err)}, status=400)
        return JsonResponse({'message': 'Hello {name}'.format(name=name)})

Tornado
-------

Tornado argument parsing is available via the :mod:`webargs.tornadoparser` module.

The :class:`webargs.tornadoparser.TornadoParser` parses arguments from a :class:`tornado.httpserver.HTTPRequest` object. The :class:`TornadoParser <webargs.tornadoparser.TornadoParser>` can be used directly, or you can decorate handler methods with :meth:`use_args <webargs.tornadoparser.TornadoParser.use_args>` or :meth:`use_kwargs <webargs.tornadoparser.TornadoParser.use_kwargs>`.

.. code-block:: python

    import tornado.ioloop
    import tornado.web

    from webargs import fields
    from webargs.tornadoparser import parser


    class HelloHandler(tornado.web.RequestHandler):

        hello_args = {
            'name': fields.Str()
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
+++++++++++++++

When using the :meth:`use_args <webargs.tornadoparser.TornadoParser.use_args>` decorator, the decorated method will have the dictionary of parsed arguments passed as a positional argument after ``self``.


.. code-block:: python

    from webargs import fields
    from webargs.tornadoparser import use_args

    class HelloHandler(tornado.web.RequestHandler):

        @use_args({'name': fields.Str()})
        def post(self, reqargs, id):
            response = {
                'message': 'Hello {}'.format(reqargs['name'])
            }
            self.write(response)

    application = tornado.web.Application([
        (r"/hello/([0-9]+)", HelloHandler),
    ], debug=True)

As with the other parser modules, :meth:`use_kwargs <webargs.tornadoparser.TornadoParser.use_kwargs>` will add keyword arguments to the view callable.

Error Handling
++++++++++++++

A `HTTPError <webargs.tornadoparser.HTTPError>` will be raised in the event of a validation error. Your `RequestHandlers` are responsible for handling these errors.

Here is how you could write the error messages to a JSON response.

.. code-block:: python

    from tornado.web import RequestHandler

    class MyRequestHandler(RequestHandler):

        def write_error(self, status_code, **kwargs):
            """Write errors as JSON."""
            self.set_header('Content-Type', 'application/json')
            if 'exc_info' in kwargs:
                etype, value, traceback = kwargs['exc_info']
                if hasattr(value, 'messages'):
                    self.write({'errors': value.messages})
                    self.finish()

Pyramid
-------

Pyramid support is available via the :mod:`webargs.pyramidparser` module.

Decorator Usage
+++++++++++++++

When using the :meth:`use_args <webargs.pyramidparser.PyramidParser.use_args>` decorator on a view callable, the arguments dictionary will be positioned after the `request` argument.

.. code-block:: python

    from pyramid.response import Response
    from webargs import fields
    from webargs.pyramidparser import use_args

    @use_args({'per_page': fields.Int()})
    def user_detail(request, args):
        return Response('The user page for user {uid}, '
                'showing {per_page} posts.').format(uid=uid,
                                                    per_page=args['per_page']))

As with the other parser modules, :meth:`use_kwargs <webargs.pyramidparser.PyramidParser.use_kwargs>` will add keyword arguments to the view callable.

URL Matches
+++++++++++

The `PyramidParser` supports parsing values from a request's matchdict.

.. code-block:: python

    from pyramid.response import Response
    from webargs.pyramidparser import use_args

    @parser.use_args({'mymatch': fields.Int()}, locations=('matchdict',))
    def matched(request, args):
        return Response('The value for mymatch is {}'.format(args['mymatch'])))
