from django import __version__

DJANGO_MAJOR_VERSION = int(__version__.split(".")[0])
DJANGO_SUPPORTS_ASYNC = DJANGO_MAJOR_VERSION >= 3
