"""Fast UUID v7 generation compatible with :func:`uuid.uuid7`."""

from __future__ import annotations

import uuid as _uuid

from uuidv7.uuidv7_impl.uuid7_gen import (
    UUID7Obj,
    _configure_uuid7,
    _generate_uuid7_at_bytes,
)
from uuidv7.uuidv7_impl.uuid7_gen import (
    generate_uuid7 as _generate_uuid7_str,
)
from uuidv7.uuidv7_impl.uuid7_gen import (
    generate_uuid7_bytes as _generate_uuid7_bytes,
)
from uuidv7.uuidv7_impl.uuid7_gen import (
    generate_uuid7_int as _generate_uuid7_int,
)
from uuidv7.uuidv7_impl.uuid7_gen import (
    uuid7 as _generate_uuid7_uuid,
)
from uuidv7.uuidv7_impl.uuid7_gen import (
    uuid7_bytes_many as _generate_uuid7_bytes_many,
)
from uuidv7.uuidv7_impl.uuid7_gen import (
    uuid7_many as _generate_uuid7_many,
)
from uuidv7.uuidv7_impl.uuid7_gen import (
    uuid7_obj as _generate_uuid7_obj,
)
from uuidv7.uuidv7_impl.uuid7_gen import (
    uuid7_obj_many as _generate_uuid7_obj_many,
)
from uuidv7.uuidv7_impl.uuid7_gen import (
    uuid7_str_many as _generate_uuid7_str_many,
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


def _uuid7_python() -> _uuid.UUID:
    return _uuid7_from_int(_generate_uuid7_int())


def uuid7_at(*, unix_ms: int) -> _uuid.UUID:
    """Generate a UUID at an exact Unix millisecond timestamp, with 74 random bits.

    Independent of the live generator's monotonic counter. Repeated calls for
    one timestamp are random, not monotonically ordered or deterministic.
    """
    if isinstance(unix_ms, bool) or not isinstance(unix_ms, int):
        raise TypeError("unix_ms must be an integer number of Unix milliseconds")
    if not 0 <= unix_ms < (1 << 48):
        raise ValueError("unix_ms must be between 0 and 2**48 - 1")
    return _UUID7(bytes=_generate_uuid7_at_bytes(unix_ms))


_configure_uuid7(_UUID7, _SAFE_UUID_UNKNOWN)
uuid7 = _generate_uuid7_uuid
uuid7_obj = _generate_uuid7_obj
uuid7_str = _generate_uuid7_str
uuid7_bytes = _generate_uuid7_bytes
uuid7_many = _generate_uuid7_many
uuid7_obj_many = _generate_uuid7_obj_many
uuid7_str_many = _generate_uuid7_str_many
uuid7_bytes_many = _generate_uuid7_bytes_many


__version__ = "0.4.0"
__all__ = [
    "UUID7Obj",
    "uuid7",
    "uuid7_at",
    "uuid7_bytes",
    "uuid7_bytes_many",
    "uuid7_many",
    "uuid7_obj",
    "uuid7_obj_many",
    "uuid7_str",
    "uuid7_str_many",
    "__version__",
]
