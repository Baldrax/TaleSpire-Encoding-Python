__version__ = "1.1.2"

from .exceptions import SlabExceedsSizeLimit, BadSlabCode, UnsupportedSlabVersion

__all__ = [
    "SlabExceedsSizeLimit",
    "BadSlabCode",
    "UnsupportedSlabVersion",
]
