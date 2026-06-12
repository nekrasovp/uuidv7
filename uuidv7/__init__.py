"""Fast UUID v7 generation compatible with :func:`uuid.uuid7`."""

from __future__ import annotations

import uuid as _uuid

from uuidv7.uuidv7_impl.uuid7_gen import (
    generate_uuid7 as _generate_uuid7_str,
)
from uuidv7.uuidv7_impl.uuid7_gen import (
    generate_uuid7_bytes as _generate_uuid7_bytes,
)
from uuidv7.uuidv7_impl.uuid7_gen import (
    generate_uuid7_int as _generate_uuid7_int,
)


class _UUID7(_uuid.UUID):
    """UUID subclass that exposes Python 3.14-compatible UUIDv7 ``time``."""

    @property
    def time(self) -> int:
        if self.version == 7:
            return self.int >> 80
        return super().time

    def __repr__(self) -> str:
        return f"UUID('{self}')"


_UUID_NEW = _uuid.UUID.__new__
_OBJECT_SETATTR = object.__setattr__
_SAFE_UUID_UNKNOWN = _uuid.SafeUUID.unknown


def _uuid7_from_int(value: int) -> _uuid.UUID:
    uuid_obj = _UUID_NEW(_UUID7)
    _OBJECT_SETATTR(uuid_obj, "int", value)
    _OBJECT_SETATTR(uuid_obj, "is_safe", _SAFE_UUID_UNKNOWN)
    return uuid_obj


def uuid7() -> _uuid.UUID:
    """Generate a UUID version 7 value.

    The return value is compatible with Python's ``uuid.uuid7()`` API. On
    Python versions older than 3.14, a private ``uuid.UUID`` subclass is used
    so that ``u.time`` returns the UUIDv7 Unix timestamp in milliseconds.
    """
    return _uuid7_from_int(_generate_uuid7_int())


def uuid7_str() -> str:
    """Generate a UUID version 7 value as a canonical string."""
    return _generate_uuid7_str()


def uuid7_bytes() -> bytes:
    """Generate a UUID version 7 value as 16 big-endian bytes."""
    return _generate_uuid7_bytes()


__version__ = "0.2.0"
__all__ = ["uuid7", "uuid7_bytes", "uuid7_str", "__version__"]
