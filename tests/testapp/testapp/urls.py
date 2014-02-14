from django.conf.urls import patterns, include, url

from tests.testapp.echo.views import SimpleCBV

urlpatterns = patterns('',
    url(r'^simpleview/', 'tests.testapp.echo.views.simpleview'),
    url(r'^simplecbvview/', SimpleCBV.as_view())
)
