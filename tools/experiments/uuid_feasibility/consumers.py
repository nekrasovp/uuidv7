"""Equivalent consumers for packed/native representations, including conversions."""

import uuid

import _uuid_lab as lab
import fastuuid
import uuid_utils
from pydantic import TypeAdapter

ADAPTER = TypeAdapter(list[uuid.UUID])


def native_to_standard(values):
    return [uuid.UUID(int=x.int) for x in lab.parse_many_native(values)]


def packed_to_standard(values):
    raw = lab.parse_many_bytes(values)
    return [lab.from_bytes(raw[i : i + 16]) for i in range(0, len(raw), 16)]


CONSUMERS = {
    "stdlib": lambda values: [uuid.UUID(s) for s in values],
    "pydantic": ADAPTER.validate_python,
    "uuid_utils": lambda values: [uuid.UUID(int=uuid_utils.UUID(s).int) for s in values],
    "fastuuid": lambda values: [uuid.UUID(int=fastuuid.UUID(s).int) for s in values],
    "c_scalar": lambda values: [lab.parse(s) for s in values],
    "c_bulk": lab.parse_many,
    "c_native_converted": native_to_standard,
    "c_packed_converted": packed_to_standard,
}
