from __future__ import annotations
import importlib.metadata

from packaging.version import Version
from marshmallow.utils import missing

# Make marshmallow's validation functions importable from webargs
from marshmallow import validate

from webargs.core import ValidationError
from webargs import fields

# TODO: Deprecate __version__ et al.
__version__ = importlib.metadata.version("webargs")
__parsed_version__ = Version(__version__)
__version_info__: (
    tuple[int, int, int] | tuple[int, int, int, str, int]
) = __parsed_version__.release  # type: ignore[assignment]
if __parsed_version__.pre:
    __version_info__ += __parsed_version__.pre  # type: ignore[assignment]
__all__ = ("ValidationError", "fields", "missing", "validate")
