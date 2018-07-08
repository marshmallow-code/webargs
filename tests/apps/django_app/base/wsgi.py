"""
WSGI config for helloapp project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.apps.django_app.base.settings")

from django.core.wsgi import get_wsgi_application  # noqa

application = get_wsgi_application()
