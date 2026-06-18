"""Tests for UUID v7 generation functionality."""

import re
import time
import uuid

from uuidv7 import UUID7Obj, uuid7, uuid7_bytes, uuid7_obj, uuid7_str
from uuidv7.uuidv7_impl.uuid7_gen import (
    _generate_uuid7_bytes_for_tests,
    _reset_state_for_tests,
    generate_uuid7_int,
)

UUID7_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def _timestamp_ms(value: uuid.UUID) -> int:
    return value.int >> 80


def test_uuid_format():
    """Test that generated UUIDs match the UUID v7 format."""
    value = uuid7()

    assert UUID7_PATTERN.match(str(value)), f"UUID {value} does not match UUID v7 format"
    assert len(str(value)) == 36, f"UUID length should be 36, got {len(str(value))}"


def test_uuid_version_field():
    """Test that the version field (13th character) is '7'."""
    value = str(uuid7())
    parts = value.split("-")
    assert len(parts) == 5, "UUID should have 5 parts"
    assert parts[2][0] == "7", f"Version field should be '7', got '{parts[2][0]}'"


def test_uuid_variant_field():
    """Test that the variant field (17th character) is 8, 9, a, or b."""
    value = str(uuid7())
    parts = value.split("-")
    assert len(parts) == 5, "UUID should have 5 parts"
    variant_char = parts[3][0].lower()
    assert variant_char in ["8", "9", "a", "b"], (
        f"Variant field should be 8/9/a/b, got '{variant_char}'"
    )


def test_uuid_uniqueness():
    """Test that multiple generated UUIDs are unique."""
    uuids = [uuid7() for _ in range(100)]
    assert len(uuids) == len(set(uuids)), "Generated UUIDs should be unique"


def test_uuid_timestamp_monotonicity():
    """Test that UUIDs generated sequentially have increasing timestamps."""
    uuids = [uuid7() for _ in range(10)]

    timestamps = [_timestamp_ms(value) for value in uuids]

    for i in range(1, len(timestamps)):
        assert timestamps[i] >= timestamps[i - 1], (
            f"Timestamps should be non-decreasing: {timestamps[i - 1]} -> {timestamps[i]}"
        )


def test_uuid_type():
    """Test that uuid7 returns a UUID object."""
    value = uuid7()
    assert isinstance(value, uuid.UUID), f"UUID should be uuid.UUID, got {type(value)}"
    assert value.version == 7
    assert value.variant == uuid.RFC_4122
    assert value == uuid.UUID(str(value))


def test_uuid7_result_is_immutable():
    """Test that fast construction preserves UUID immutability."""
    value = uuid7()
    try:
        value.int = 0
    except TypeError:
        pass
    else:
        raise AssertionError("UUID objects should be immutable")


def test_uuid7_str_fast_path():
    """Test that uuid7_str returns a canonical UUIDv7 string."""
    value = uuid7_str()
    assert isinstance(value, str)
    assert UUID7_PATTERN.match(value)
    parsed = uuid.UUID(value)
    assert parsed.version == 7
    assert parsed.variant == uuid.RFC_4122


def test_uuid7_bytes_fast_path():
    """Test that uuid7_bytes returns UUIDv7 bytes."""
    value = uuid7_bytes()
    assert isinstance(value, bytes)
    assert len(value) == 16
    parsed = uuid.UUID(bytes=value)
    assert parsed.version == 7
    assert parsed.variant == uuid.RFC_4122


def test_uuid7_int_fast_path():
    """Test that the C integer fast path returns a UUIDv7 integer."""
    value = generate_uuid7_int()
    assert isinstance(value, int)
    parsed = uuid.UUID(int=value)
    assert parsed.version == 7
    assert parsed.variant == uuid.RFC_4122


def test_uuid7_obj_fast_path():
    """Test that uuid7_obj returns a compact UUIDv7-like native object."""
    value = uuid7_obj()
    parsed = uuid.UUID(str(value))

    assert isinstance(value, UUID7Obj)
    assert not isinstance(value, uuid.UUID)
    assert UUID7_PATTERN.match(str(value))
    assert repr(value) == f"UUID('{value}')"
    assert bytes(value) == value.bytes
    assert int(value) == value.int
    assert value.bytes == parsed.bytes
    assert value.bytes_le == parsed.bytes_le
    assert value.hex == parsed.hex
    assert value.fields == parsed.fields
    assert value.time == parsed.int >> 80
    assert value.timestamp == value.time
    assert value.version == 7
    assert value.variant == uuid.RFC_4122
    assert value.urn == parsed.urn


def test_uuid7_obj_is_immutable_and_orderable():
    """Test native UUIDv7 objects are immutable, hashable, and sortable."""
    values = [uuid7_obj() for _ in range(100)]

    assert len(values) == len(set(values))
    assert values == sorted(values)

    try:
        values[0].int = 0
    except TypeError:
        pass
    else:
        raise AssertionError("UUID objects should be immutable")


def test_uuid_time_matches_uuidv7_timestamp_bits():
    """Test Python 3.14-compatible UUIDv7 time semantics."""
    before = int(time.time() * 1000)
    value = uuid7()
    after = int(time.time() * 1000)

    assert value.time == _timestamp_ms(value)
    assert before <= value.time <= after + 1


def test_same_millisecond_values_are_monotonic():
    """Test monotonic ordering for UUIDs generated within the same millisecond."""
    _reset_state_for_tests()
    timestamp_ms = int(time.time() * 1000)
    uuids = [uuid.UUID(bytes=_generate_uuid7_bytes_for_tests(timestamp_ms)) for _ in range(1000)]
    assert uuids == sorted(uuids)
    assert len(uuids) == len(set(uuids))


def test_clock_rollback_does_not_decrease_uuid_values():
    """Test generator state when the observed clock moves backwards."""
    _reset_state_for_tests()
    timestamp_ms = int(time.time() * 1000)
    first = uuid.UUID(bytes=_generate_uuid7_bytes_for_tests(timestamp_ms))
    second = uuid.UUID(bytes=_generate_uuid7_bytes_for_tests(timestamp_ms - 1000))

    assert second.int > first.int
    assert _timestamp_ms(second) == timestamp_ms


def test_multiple_calls():
    """Test that the function can be called multiple times without errors."""
    for _ in range(100):
        value = uuid7()
        assert value is not None
        assert len(str(value)) == 36
