"""Prevent valid-looking legacy UUIDs and changed API shapes entering rankings."""

import uuid

import pytest

from benchmarks.benchmark_competitors import build_cases, validate_uuid7


def value_at(ms):
    return uuid.UUID(int=(ms << 80) | (7 << 76) | (2 << 62))


def test_rejects_legacy_timestamp_despite_valid_version_and_variant():
    value = value_at(7_328_000_000_000)
    assert value.version == 7 and value.variant == uuid.RFC_4122
    with pytest.raises(ValueError, match="timestamp"):
        validate_uuid7(value, "uuid.UUID", before_ms=1_800_000_000_000, after_ms=1_800_000_000_001)


@pytest.mark.parametrize(
    "shape,convert",
    [
        ("uuid.UUID", lambda v: v),
        ("bytes", lambda v: v.bytes),
        ("str", str),
        ("hex", lambda v: v.hex),
    ],
)
def test_current_timestamp_and_correct_shapes_pass(shape, convert):
    expected = value_at(1_800_000_000_000)
    assert (
        validate_uuid7(
            convert(expected), shape, before_ms=1_800_000_000_000, after_ms=1_800_000_000_001
        )
        == expected
    )


def test_changed_native_result_cannot_be_ranked_as_string():
    class Native:
        def __str__(self):
            return str(value_at(42))

    with pytest.raises(ValueError, match="expected str"):
        validate_uuid7(Native(), "str")
    assert validate_uuid7(Native(), "native") == value_at(42)


def test_stdlib_compat_means_actual_uuid_instance():
    with pytest.raises(ValueError, match="expected uuid.UUID"):
        validate_uuid7(str(value_at(42)), "uuid.UUID")


def test_noncanonical_text_and_wrong_version_are_rejected():
    with pytest.raises(ValueError, match="noncanonical"):
        validate_uuid7(value_at(42).hex, "str")
    with pytest.raises(ValueError, match="version/variant"):
        validate_uuid7(uuid.UUID(int=0), "uuid.UUID")


def test_adapters_cover_new_shapes_compat_and_correct_import_path():
    cases = build_cases()
    assert next(c for c in cases if c.key == "fastuuidv7.uuid7()").shape == "native"
    assert any(c.module == "uuid_utils.compat" and c.shape == "uuid.UUID" for c in cases)
    assert any(c.module == "uuid_v7.base" for c in cases)
    assert {"uuid7_str", "uuid7_bytes", "uuid7_hex", "SequentialGenerator"} <= {
        c.function for c in cases if c.package == "fastuuidv7"
    }
