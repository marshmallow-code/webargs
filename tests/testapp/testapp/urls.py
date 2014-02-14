from django.conf.urls import patterns, include, url

from tests.testapp.echo.views import SimpleCBV, SimpleDecoratedCBV, SimpleCBVWithParam

urlpatterns = patterns('',
    url(r'^simpleview/$', 'tests.testapp.echo.views.simpleview'),
    url(r'^simpleview/(?P<pid>\d+)/$', 'tests.testapp.echo.views.simpleview_with_param'),
    url(r'^simplecbvview/$', SimpleCBV.as_view()),
    url(r'^simplecbvview/(?P<pid>\d+)/$', SimpleCBVWithParam.as_view()),
    url(r'^decoratedview/', 'tests.testapp.echo.views.decoratedview'),
    url(r'^decoratedcbv/', SimpleDecoratedCBV.as_view())
)
