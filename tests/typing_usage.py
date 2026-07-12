"""Static public-API contract checked by mypy in CI."""

from __future__ import annotations

import uuid

from fastuuid7 import (
    UUID7Obj,
    uuid7,
    uuid7_bytes,
    uuid7_bytes_many,
    uuid7_many,
    uuid7_obj,
    uuid7_obj_many,
    uuid7_str,
    uuid7_str_many,
)

uuid_value: uuid.UUID = uuid7()
native_value: UUID7Obj = uuid7_obj()
text_value: str = uuid7_str()
raw_value: bytes = uuid7_bytes()
uuid_values: list[uuid.UUID] = uuid7_many(10)
native_values: list[UUID7Obj] = uuid7_obj_many(10)
text_values: list[str] = uuid7_str_many(10)
raw_values: bytes = uuid7_bytes_many(10)

native_int: int = native_value.int
native_time: int = native_value.time
native_text: str = str(native_value)
native_raw: bytes = bytes(native_value)
