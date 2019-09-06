# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SECRET_KEY = "s$28!(eonml-m3jgbq_)bj_&#=)sym2d*kx%@j+r&vwusxz%g$"
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = ["*"]
# Application definition

INSTALLED_APPS = ("django.contrib.contenttypes",)

MIDDLEWARE_CLASSES = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
)

ROOT_URLCONF = "tests.apps.django_app.base.urls"

WSGI_APPLICATION = "tests.apps.django_app.base.wsgi.application"
LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True
STATIC_URL = "/static/"
