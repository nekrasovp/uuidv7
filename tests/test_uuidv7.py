"""Tests for UUID v7 generation functionality."""

import re

from uuidv7 import uuid7


def test_uuid_format():
    """Test that generated UUIDs match the UUID v7 format."""
    uuid = uuid7()

    # UUID v7 format: 8-4-4-4-12 hexadecimal digits
    uuid_pattern = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$", re.IGNORECASE
    )

    assert uuid_pattern.match(uuid), f"UUID {uuid} does not match UUID v7 format"
    assert len(uuid) == 36, f"UUID length should be 36, got {len(uuid)}"


def test_uuid_version_field():
    """Test that the version field (13th character) is '7'."""
    uuid = uuid7()
    parts = uuid.split("-")
    assert len(parts) == 5, "UUID should have 5 parts"
    assert parts[2][0] == "7", f"Version field should be '7', got '{parts[2][0]}'"


def test_uuid_variant_field():
    """Test that the variant field (17th character) is 8, 9, a, or b."""
    uuid = uuid7()
    parts = uuid.split("-")
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

    # Extract timestamp parts (first two segments)
    timestamps = []
    for uuid in uuids:
        parts = uuid.split("-")
        # Combine first two parts to get timestamp
        timestamp_hex = parts[0] + parts[1]
        timestamps.append(int(timestamp_hex, 16))

    # Check that timestamps are non-decreasing (allowing for small variations)
    for i in range(1, len(timestamps)):
        assert timestamps[i] >= timestamps[i - 1] - 1, (
            f"Timestamps should be non-decreasing: {timestamps[i - 1]} -> {timestamps[i]}"
        )


def test_uuid_type():
    """Test that uuid7 returns a string."""
    uuid = uuid7()
    assert isinstance(uuid, str), f"UUID should be a string, got {type(uuid)}"


def test_multiple_calls():
    """Test that the function can be called multiple times without errors."""
    for _ in range(100):
        uuid = uuid7()
        assert uuid is not None
        assert len(uuid) == 36
