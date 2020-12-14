from distutils.version import LooseVersion
from marshmallow.utils import missing

# Make marshmallow's validation functions importable from webargs
from marshmallow import validate

from webargs.core import ValidationError
from webargs import fields

__version__ = "7.0.1"
__version_info__ = tuple(LooseVersion(__version__).version)
__all__ = ("ValidationError", "fields", "missing", "validate")
