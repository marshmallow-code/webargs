import json
from django.http import HttpResponse
from django.views.generic import View

from webargs import Arg
from webargs.djangoparser import DjangoParser

parser = DjangoParser()
hello_args = {
    'name': Arg(str, default='World')
}

class SimpleCBV(View):

    def get(self, request):
        args = parser.parse(hello_args, self.request)
        return HttpResponse(
            json.dumps(args),
            content_type='application/json'
        )

    def post(self, request):
        args = parser.parse(hello_args, self.request)
        return HttpResponse(
            json.dumps(args),
            content_type='application/json'
        )

def simpleview(request):
    args = parser.parse(hello_args, request)
    return HttpResponse(
        json.dumps(args),
        content_type='application/json'
    )
