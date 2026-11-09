"""Arbitrary 128-bit parser/formatter round trips using the optional properties extra."""

import uuid

import pytest

import fastuuid7 as f

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402


@settings(max_examples=2000)
@given(st.binary(min_size=16, max_size=16))
def test_arbitrary_roundtrip(raw):
    value = uuid.UUID(bytes=raw)
    text = str(value)
    forms = [text, text.upper(), value.hex, "{" + text + "}", "URN:UUID:" + text]
    assert f.parse_many(forms) == [value] * len(forms)
    assert f.parse_bytes_many(forms) == raw * len(forms)
    assert f.format_uuid(raw) == f.format_uuid(value) == text


@settings(max_examples=1000)
@given(st.text(max_size=80))
def test_random_text_never_crashes(text):
    try:
        value = f.parse(text)
    except ValueError:
        return
    assert value == uuid.UUID(f.format_uuid(value))
