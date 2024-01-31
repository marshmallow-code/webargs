import importlib.metadata

DJANGO_MAJOR_VERSION = int(importlib.metadata.version("django").split(".")[0])
DJANGO_SUPPORTS_ASYNC = DJANGO_MAJOR_VERSION >= 3
