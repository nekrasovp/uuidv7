"""Clock/counter boundaries, historical UUIDs, and process integration."""

import os
import pickle
import subprocess
import sys
import uuid

import pytest

import fastuuid7
import uuidv7
from uuidv7.uuidv7_impl.uuid7_gen import (
    _generate_uuid7_bytes_for_tests,
    _reset_state_for_tests,
    _set_state_for_tests,
)

MAX_TIMESTAMP = (1 << 48) - 1
MAX_COUNTER = (1 << 42) - 1


@pytest.fixture(autouse=True)
def isolated_generator():
    _reset_state_for_tests()
    yield
    _reset_state_for_tests()


def at_clock(ms):
    return uuid.UUID(bytes=_generate_uuid7_bytes_for_tests(ms))


def counter_of(value):
    return (((value.int >> 64) & 0xFFF) << 30) | ((value.int >> 32) & ((1 << 30) - 1))


@pytest.mark.parametrize("start", [(1 << 30) - 2, MAX_COUNTER - 2])
def test_counter_carry_preserves_layout_and_all_orderings(start):
    ms = 1_645_557_742_123
    _set_state_for_tests(ms, start)
    values = [at_clock(ms) for _ in range(8)]
    assert counter_of(values[0]) == start + 1
    assert counter_of(values[1]) == start + 2
    expected_ms = ms + (start == MAX_COUNTER - 2)
    assert values[-1].int >> 80 == expected_ms
    for a, b in zip(values, values[1:]):
        assert a.int < b.int and a.bytes < b.bytes and str(a) < str(b)
    assert all(v.version == 7 and v.variant == uuid.RFC_4122 for v in values)


def test_repeated_rollback_and_clock_recovery():
    ms = 1_645_557_742_123
    _set_state_for_tests(ms, 100)
    values = [at_clock(t) for t in [ms - 1, ms - 1000, ms, ms + 1, ms - 20]]
    assert [v.int >> 80 for v in values] == [ms, ms, ms, ms + 1, ms + 1]
    assert all(a.int < b.int for a, b in zip(values, values[1:]))


@pytest.mark.parametrize(
    "factory,is_batch",
    [
        (fastuuid7.uuid7, False),
        (fastuuid7.uuid7_obj, False),
        (fastuuid7.uuid7_str, False),
        (fastuuid7.uuid7_bytes, False),
        (lambda: fastuuid7.uuid7_many(2), True),
        (lambda: fastuuid7.uuid7_obj_many(2), True),
        (lambda: fastuuid7.uuid7_str_many(2), True),
        (lambda: fastuuid7.uuid7_bytes_many(2), True),
    ],
)
def test_timestamp_exhaustion_never_wraps_or_returns_partial_batch(factory, is_batch):
    _set_state_for_tests(MAX_TIMESTAMP, MAX_COUNTER - 1)
    # A scalar can consume the final value. A two-item batch must fail wholly.
    if is_batch:
        with pytest.raises(OverflowError, match="48 bits"):
            factory()
    else:
        value = factory()
        parsed = uuid.UUID(bytes=value) if isinstance(value, bytes) else uuid.UUID(str(value))
        assert parsed.int >> 80 == MAX_TIMESTAMP
        assert counter_of(parsed) == MAX_COUNTER
    with pytest.raises(OverflowError, match="48 bits"):
        factory()
    with pytest.raises(OverflowError):
        factory()


@pytest.mark.parametrize("ms", [0, 1, 1_645_557_742_123, MAX_TIMESTAMP])
def test_historical_timestamp_is_exact_and_round_trips(ms):
    assert fastuuid7.uuid7_at is uuidv7.uuid7_at
    value = fastuuid7.uuid7_at(unix_ms=ms)
    assert isinstance(value, uuid.UUID)
    assert value.time == value.int >> 80 == ms
    assert value.version == 7 and value.variant == uuid.RFC_4122
    assert uuid.UUID(str(value)) == value
    assert uuid.UUID(bytes=value.bytes) == value
    assert pickle.loads(pickle.dumps(value)) == value


def test_historical_calls_preserve_live_counter_and_timestamp():
    ms = 1_645_557_742_123
    _set_state_for_tests(ms, 123)
    before = at_clock(ms)
    for t in [MAX_TIMESTAMP, 0, ms - 10000, ms + 10000]:
        assert fastuuid7.uuid7_at(unix_ms=t).time == t
    after = at_clock(ms)
    assert after.int >> 80 == ms
    assert counter_of(after) == counter_of(before) + 1


def test_repeated_historical_timestamp_uses_fresh_randomness():
    values = [fastuuid7.uuid7_at(unix_ms=42) for _ in range(1000)]
    assert len(set(values)) == len(values)
    # Both random fields vary, unlike an accidental timestamp-only constructor.
    assert len({(v.int >> 64) & 0xFFF for v in values}) > 1
    assert len({v.int & ((1 << 62) - 1) for v in values}) > 1


@pytest.mark.parametrize("value", [True, False, 1.5, "123", None])
def test_historical_timestamp_rejects_non_integers(value):
    with pytest.raises(TypeError, match="integer"):
        fastuuid7.uuid7_at(unix_ms=value)


@pytest.mark.parametrize("value", [-1, 1 << 48, 1 << 100])
def test_historical_timestamp_rejects_out_of_range(value):
    with pytest.raises(ValueError, match="unix_ms"):
        fastuuid7.uuid7_at(unix_ms=value)


def test_historical_timestamp_requires_explicit_units():
    with pytest.raises(TypeError):
        fastuuid7.uuid7_at(1000)


def test_subprocess_after_import_and_generation():
    fastuuid7.uuid7_many(1000)
    fastuuid7.uuid7_at(unix_ms=42)
    result = subprocess.run(
        [sys.executable, "-c", "import fastuuid7; print(fastuuid7.uuid7_at(unix_ms=42).time)"],
        capture_output=True,
        text=True,
        check=True,
        timeout=20,
    )
    assert result.stdout.strip() == "42"


@pytest.mark.skipif(not hasattr(os, "fork"), reason="requires POSIX fork")
def test_historical_entropy_is_discarded_after_fork():
    # Prime the entropy buffer; a child must not reuse the parent's next bytes.
    fastuuid7.uuid7_at(unix_ms=42)
    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:
        try:
            os.close(read_fd)
            os.write(write_fd, fastuuid7.uuid7_at(unix_ms=42).bytes)
        finally:
            os._exit(0)
    os.close(write_fd)
    try:
        parent = fastuuid7.uuid7_at(unix_ms=42).bytes
        child = os.read(read_fd, 16)
    finally:
        os.close(read_fd)
        _, status = os.waitpid(pid, 0)
    assert status == 0 and len(child) == 16 and child != parent
