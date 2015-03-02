from django.conf.urls import patterns, url

from tests.testapp.echo.views import (
    SimpleCBV, SimpleDecoratedCBV,
    SimpleCBVWithParam, SimpleCBVMulti
)

urlpatterns = patterns('',
    url(r'^simpleview/$', 'tests.testapp.echo.views.simpleview'),
    url(r'^simpleview_required/$', 'tests.testapp.echo.views.simpleview_with_required_arg'),
    url(r'^simpleview/(?P<pid>\d+)/$', 'tests.testapp.echo.views.simpleview_with_param'),
    url(r'^simplecbvview/$', SimpleCBV.as_view()),
    url(r'^simplecbvview/(?P<pid>\d+)/$', SimpleCBVWithParam.as_view()),
    url(r'^decoratedview/', 'tests.testapp.echo.views.decoratedview'),
    url(r'^validatedview/', 'tests.testapp.echo.views.validatedview'),
    url(r'^decoratedcbv/', SimpleDecoratedCBV.as_view()),
    url(r'^cookieview/$', 'tests.testapp.echo.views.cookieview'),
    url(r'^simpleview_multi/$', 'tests.testapp.echo.views.simpleview_multi'),
    url(r'^simplecbv_multi/$', SimpleCBVMulti.as_view())
)
