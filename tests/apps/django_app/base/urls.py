from django.conf.urls import url

from tests.apps.django_app.echo import views

urlpatterns = [
    url(r'^echo$', views.echo),
    url(r'^echo_query$', views.echo_query),
    url(r'^echo_use_args$', views.echo_use_args),
    url(r'^echo_use_kwargs$', views.echo_use_kwargs),
    url(r'^echo_multi$', views.echo_multi),
    url(r'^echo_many_schema$', views.echo_many_schema),
    url(r'^echo_use_args_with_path_param/(?P<name>\w+)$', views.echo_use_args_with_path_param),
    url(r'^echo_use_kwargs_with_path_param/(?P<name>\w+)$', views.echo_use_kwargs_with_path_param),
    url(r'^error$', views.always_error),
    url(r'^error400$', views.error400),
    url(r'^echo_headers$', views.echo_headers),
    url(r'^echo_cookie$', views.echo_cookie),
    url(r'^echo_file$', views.echo_file),
    url(r'^echo_nested$', views.echo_nested),
    url(r'^echo_nested_many$', views.echo_nested_many),
    url(r'^echo_cbv$', views.EchoCBV.as_view()),
    url(r'^echo_use_args_cbv$', views.EchoUseArgsCBV.as_view()),
    url(r'^echo_use_args_with_path_param_cbv/(?P<pid>\d+)$',
        views.EchoUseArgsWithParamCBV.as_view()),
]
