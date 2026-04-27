"""Exceptions for talespire-encoding."""

# Base Exception
class TSEncodingException(Exception):
    """Base TS Encoding Exception"""
    pass

# Creature Blueprint Exceptions
# TODO: Replace generic exceptions in creature_bp.py with specific exceptions

# Slab Exceptions
class SlabExceedsSizeLimit(TSEncodingException):
    """Raised when encoding a slab that exceeds TaleSpires size limit."""
    pass

class BadSlabCode(TSEncodingException):
    """Raised when a slab code fails to read."""
    pass

class UnsupportedSlabVersion(TSEncodingException):
    """Raised when the slab is an unsupported version."""
    pass

# Asset Exceptions
class InvalidTaleSpireDirectory(TSEncodingException):
    """Raised when the TaleSpire directory can not be found."""
    pass

class InvalidAssetType(TSEncodingException):
    """Raised when an invalid asset type is requested or found."""
    pass
