# flake8: noqa
from distutils.version import LooseVersion

import marshmallow as ma

MARSHMALLOW_VERSION_INFO = tuple(LooseVersion(ma.__version__).version)  # type: tuple
