class TSEncodingException(Exception):
    """Base TS Encoding Exception"""
    pass

class SlabExceedsSizeLimit(TSEncodingException):
    """Raised when encoding a slab that exceeds TaleSpires size limit."""
    pass

class BadSlabCode(TSEncodingException):
    """Raised when a slab code fails to read."""
    pass

class UnsupportedSlabVersion(TSEncodingException):
    """Raised when the slab is an unsupported version."""
    pass