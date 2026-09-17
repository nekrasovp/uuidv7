"""Differential checks against stdlib UUIDs reconstructed from the same value."""

import operator
import pickle
import uuid

import pytest

import fastuuid7

pytest.importorskip("hypothesis", reason="install the properties extra to run UUID properties")
from hypothesis import example, given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

# Reproduce input generation in CI without pretending that OS entropy is seeded.
UUID_COMPAT_SETTINGS = settings(max_examples=75, derandomize=True, deadline=None)

TIMESTAMPS = st.integers(min_value=0, max_value=(1 << 48) - 1)
COMPARISONS = (operator.eq, operator.ne, operator.lt, operator.le, operator.gt, operator.ge)


def assert_stdlib_compatible(value):
    assert isinstance(value, uuid.UUID)
    reference = uuid.UUID(int=value.int)
    assert value.bytes == reference.bytes
    assert value.bytes_le == reference.bytes_le
    assert str(value) == str(reference)
    assert value.hex == reference.hex
    assert value.urn == reference.urn
    assert value.fields == reference.fields
    assert value.version == reference.version == 7
    assert value.variant == reference.variant == uuid.RFC_4122
    assert uuid.UUID(bytes=value.bytes) == value
    assert uuid.UUID(bytes_le=value.bytes_le) == value
    assert uuid.UUID(str(value)) == value
    assert uuid.UUID(hex=value.hex) == value
    assert value == reference and reference == value
    assert hash(value) == hash(reference)
    assert {value: "present"}[reference] == "present"
    assert {reference: "present"}[value] == "present"
    assert len({value, reference}) == 1
    for compare in COMPARISONS:
        assert compare(value, reference) == compare(reference, reference)
        assert compare(reference, value) == compare(reference, reference)
    # Older stdlib versions interpret .time as UUIDv1 even for version 7.
    if hasattr(uuid, "uuid7"):
        assert value.time == reference.time
    for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
        restored = pickle.loads(pickle.dumps(value, protocol=protocol))
        assert isinstance(restored, uuid.UUID)
        assert restored == reference and hash(restored) == hash(reference)
        assert restored.bytes == value.bytes
        assert restored.time == value.time


@UUID_COMPAT_SETTINGS
@given(ms=TIMESTAMPS, other_int=st.integers(min_value=0, max_value=(1 << 128) - 1))
@example(ms=0, other_int=0)
@example(ms=(1 << 48) - 1, other_int=(1 << 128) - 1)
def test_historical_uuid_matches_stdlib_for_its_value(ms, other_int):
    value = fastuuid7.uuid7_at(unix_ms=ms)
    assert_stdlib_compatible(value)
    assert value.time == ms
    reference = uuid.UUID(int=value.int)
    other = uuid.UUID(int=other_int)
    for compare in COMPARISONS:
        assert compare(value, other) == compare(reference, other)
        assert compare(other, value) == compare(other, reference)


@UUID_COMPAT_SETTINGS
@given(count=st.integers(min_value=0, max_value=24))
@example(count=0)
@example(count=24)
def test_live_scalar_and_batch_round_trip_and_mixed_order(count):
    values = [fastuuid7.uuid7(), *fastuuid7.uuid7_many(count)]
    assert len(values) == count + 1
    for value in values:
        assert_stdlib_compatible(value)
    references = [uuid.UUID(bytes=value.bytes) for value in values]
    # Compare each representation of each ID, never two independent generators.
    reverse_values = list(reversed(values))
    assert sorted(reverse_values) == sorted(references)
    assert sorted([*reversed(values), *references]) == sorted(references * 2)
    for first, second in zip(values, values[1:]):
        assert first < second


@UUID_COMPAT_SETTINGS
@given(count=st.integers(min_value=0, max_value=24))
def test_native_objects_obey_only_their_documented_contract(count):
    values = [fastuuid7.uuid7_obj(), *fastuuid7.uuid7_obj_many(count)]
    for value in values:
        assert isinstance(value, fastuuid7.UUID7Obj)
        reference = uuid.UUID(int=value.int)
        assert str(value) == str(reference)
        for attribute in ("bytes", "bytes_le", "hex", "urn", "fields", "version", "variant"):
            assert getattr(value, attribute) == getattr(reference, attribute)
        assert value.timestamp == value.time == int.from_bytes(reference.bytes[:6], "big")
        assert {value: "present"}[value] == "present"
        with pytest.raises((AttributeError, TypeError)):
            value.int = 0
    reverse_values = list(reversed(values))
    assert sorted(reverse_values) == values
    assert len(set(values)) == len(values)
    for first, second in zip(values, values[1:]):
        for compare in COMPARISONS:
            assert compare(first, second) == compare(first.int, second.int)
            assert compare(second, first) == compare(second.int, first.int)
    # No native/stdlib equality, equal hashes, pickle or framework adaptation promise.
