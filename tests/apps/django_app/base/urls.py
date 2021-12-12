from django.urls import re_path

from tests.apps.django_app.echo import views


urlpatterns = [
    re_path(r"^echo$", views.echo),
    re_path(r"^echo_form$", views.echo_form),
    re_path(r"^echo_json$", views.echo_json),
    re_path(r"^echo_json_or_form$", views.echo_json_or_form),
    re_path(r"^echo_use_args$", views.echo_use_args),
    re_path(r"^echo_use_args_validated$", views.echo_use_args_validated),
    re_path(r"^echo_ignoring_extra_data$", views.echo_ignoring_extra_data),
    re_path(r"^echo_use_kwargs$", views.echo_use_kwargs),
    re_path(r"^echo_multi$", views.echo_multi),
    re_path(r"^echo_multi_form$", views.echo_multi_form),
    re_path(r"^echo_multi_json$", views.echo_multi_json),
    re_path(r"^echo_many_schema$", views.echo_many_schema),
    re_path(
        r"^echo_use_args_with_path_param/(?P<name>\w+)$",
        views.echo_use_args_with_path_param,
    ),
    re_path(
        r"^echo_use_kwargs_with_path_param/(?P<name>\w+)$",
        views.echo_use_kwargs_with_path_param,
    ),
    re_path(r"^error$", views.always_error),
    re_path(r"^echo_headers$", views.echo_headers),
    re_path(r"^echo_cookie$", views.echo_cookie),
    re_path(r"^echo_file$", views.echo_file),
    re_path(r"^echo_nested$", views.echo_nested),
    re_path(r"^echo_nested_many$", views.echo_nested_many),
    re_path(r"^echo_cbv$", views.EchoCBV.as_view()),
    re_path(r"^echo_use_args_cbv$", views.EchoUseArgsCBV.as_view()),
    re_path(
        r"^echo_use_args_with_path_param_cbv/(?P<pid>\d+)$",
        views.EchoUseArgsWithParamCBV.as_view(),
    ),
]
