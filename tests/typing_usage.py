"""Static public-API contract checked by mypy in CI."""

from __future__ import annotations

import uuid

import fastuuid7
from fastuuid7 import (
    UUID7Obj,
    uuid7,
    uuid7_at,
    uuid7_at_many,
    uuid7_bytes,
    uuid7_bytes_many,
    uuid7_many,
    uuid7_obj,
    uuid7_obj_many,
    uuid7_str,
    uuid7_str_many,
)

uuid_value: uuid.UUID = uuid7()
historical_value: uuid.UUID = uuid7_at(unix_ms=1_645_557_742_123)
historical_values: list[uuid.UUID] = uuid7_at_many(unix_ms=(ms for ms in [0, 42]))
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


v4: uuid.UUID = fastuuid7.uuid4()
parsed: uuid.UUID = fastuuid7.parse(str(v4))
parsed_list: list[uuid.UUID] = fastuuid7.parse_many([str(v4)])
packed_values: bytes = fastuuid7.parse_bytes_many([str(v4)])
formatted: str = fastuuid7.format_uuid(v4)
v4_list: list[uuid.UUID] = fastuuid7.uuid4_many(2)
v4_strings: list[str] = fastuuid7.uuid4_str_many(2)
v4_packed: bytes = fastuuid7.uuid4_bytes_many(2)
